"""Trusted end-to-end privacy, preservation, and retirement controls; stdlib only."""

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SOURCE = Path(os.environ.get("TLR_SOURCE_ROOT", Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(SOURCE))
import app
import release


class Running:
    def __init__(self, db, root):
        self.db, self.root, self.error = db, root, []

    def __enter__(self):
        def run():
            try:
                app.serve(self.db, 0, self.root)
            except Exception as exc:
                self.error.append(exc)
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.error:
                raise self.error[0]
            with app.connect(self.db) as db:
                port = db.execute("SELECT server_port FROM service_state WHERE id=1").fetchone()[0]
            if port:
                self.url = f"http://127.0.0.1:{port}"
                return self
            time.sleep(0.02)
        raise RuntimeError("Server failed to start.")

    def __exit__(self, *_):
        with app.connect(self.db) as db:
            db.execute("UPDATE service_state SET mode='retired' WHERE id=1")
        self.thread.join(5)
        if self.thread.is_alive():
            raise RuntimeError("Own fixture server failed to stop.")

    def request(self, method, path, token=None, body=None, headers=None):
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = "Bearer " + token
        request_headers.update(headers or {})
        request = Request(self.url + path, data=data, method=method, headers=request_headers)
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as response:
            return response.code, json.loads(response.read())
        with response:
            raw = response.read()
            return response.status, raw if "text/html" in response.headers["Content-Type"] else json.loads(raw)


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="last-release-contracts-")
        cls.root = Path(cls.workspace.name) / "source"
        cls.root.mkdir()
        # A separate committed fixture tests source freshness without touching the owner's checkout.
        for name in ("app.py", "release.py", "will.json", ".gitignore", "web/notebook.html",
                     "tests/contracts.py", "tests/offline.spec.mjs"):
            target = cls.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, target)
        for args in (("init", "-b", "main"), ("add", "."),
                     ("-c", "user.name=Contract Fixture", "-c", "user.email=fixture@example.invalid",
                      "commit", "-m", "Trusted synthetic fixture")):
            subprocess.run(["git", "-C", str(cls.root), *args], capture_output=True, check=True)
        cls.baseline = release.git(cls.root, "rev-parse", "HEAD").decode().strip()

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=self.root / "data" if (self.root / "data").exists() else None,
                                                      prefix="last-release-case-")
        self.place = Path(self.directory.name)
        self.db = self.place / "notebook.sqlite3"
        self.keys = app.seed(self.db, self.place / "keys.json")
        self.out = self.place / "candidate"

    def tearDown(self):
        self.directory.cleanup()

    def mode(self):
        with app.connect(self.db) as db:
            return db.execute("SELECT mode FROM service_state WHERE id=1").fetchone()[0]

    def test_ownership_crud_and_restart(self):
        alice, bob = self.keys["Alice"]["token"], self.keys["Bob"]["token"]
        with Running(self.db, self.root) as server:
            self.assertEqual(server.request("GET", "/api/notes")[0], 401)
            self.assertEqual(server.request("GET", "/api/notes", "wrong")[0], 401)
            self.assertEqual(server.request("GET", "/api/notes", alice, headers={"Origin":"https://untrusted.invalid"})[0], 403)
            self.assertEqual(server.request("GET", "/api/notes", alice, headers={"Host":"untrusted.invalid"})[0], 400)
            own = server.request("GET", "/api/notes", alice)[1]
            other = server.request("GET", "/api/notes", bob)[1]
            self.assertEqual(len(own["notes"]), 3)
            self.assertFalse({n["id"] for n in own["notes"]} & {n["id"] for n in other["notes"]})
            other_id = other["notes"][0]["id"]
            self.assertEqual(server.request("PATCH", "/api/notes/"+other_id, alice, {"title":"stolen","body":"x"})[0], 404)
            self.assertEqual(server.request("DELETE", "/api/notes/"+other_id, alice)[0], 404)
            self.assertEqual(server.request("GET", "/api/export")[0], 401)
            payload = release.check_html(server.request("GET", "/api/export", alice)[1])
            self.assertEqual(payload["notes"], own["notes"])
            self.assertNotIn(bob, json.dumps(payload))
            status, created = server.request("POST", "/api/notes", alice, {"title":"Café 🌱","body":"A lasting thought"})
            self.assertEqual(status, 201)
            note_id = created["id"]
            self.assertEqual(server.request("PATCH", "/api/notes/"+note_id, alice, {"title":"Still here","body":"Edited"})[0], 200)
            deleted = own["notes"][0]["id"]
            self.assertEqual(server.request("DELETE", "/api/notes/"+deleted, alice)[0], 200)
            self.assertEqual(server.request("PATCH", "/api/notes/"+deleted, alice, {"title":"resurrected","body":"x"})[0], 404)
        with app.connect(self.db) as db:
            db.execute("UPDATE service_state SET mode='active' WHERE id=1")
        with Running(self.db, self.root) as server:
            notes = server.request("GET", "/api/notes", alice)[1]["notes"]
            self.assertTrue(any(n["id"] == note_id and n["body"] == "Edited" for n in notes))
            self.assertFalse(any(n["id"] == deleted for n in notes))

    def test_validation_and_reversible_freeze(self):
        token = self.keys["Alice"]["token"]
        with Running(self.db, self.root) as server:
            for value in ({"title":"", "body":"x"}, {"title":"x","body":"x","owner_id":self.keys["Bob"]["id"]},
                          {"title":"x","body":"é"*8193}, {"title":"x","body":None}):
                self.assertEqual(server.request("POST", "/api/notes", token, value)[0], 400)
            self.assertEqual(server.request("POST", "/api/notes", token, {"title":"x","body":"x"*40000})[0], 413)
            release.freeze(self.db)
            self.assertEqual(server.request("POST", "/api/notes", token, {"title":"x","body":"x"})[0], 409)
            self.assertEqual(server.request("GET", "/api/export", token)[0], 200)
            release.unfreeze(self.db)
            self.assertEqual(server.request("POST", "/api/notes", token, {"title":"Recovered","body":"kept"})[0], 201)

    def test_unsupported_will_blocks_before_freeze(self):
        path = self.root / "will.json"
        original = path.read_bytes()
        invalid = json.loads(original)
        invalid["offline_actions"].append("collaboration")
        try:
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                release.prepare(self.db, self.out, self.root)
            self.assertEqual(self.mode(), "active")
            self.assertFalse(self.out.exists())
        finally:
            path.write_bytes(original)

    def test_exact_exports_and_fault_injection(self):
        release.prepare(self.db, self.out, self.root)
        manifest, _ = release.validate_candidate(self.db, self.out, self.root)
        self.assertEqual([a["notes"] for a in manifest["accounts"]], [3,3])
        original = release.export_for
        for fault in ("foreign", "missing", "altered"):
            def broken(root, snapshot, account, build, fault=fault):
                altered = copy.deepcopy(snapshot)
                if fault == "foreign":
                    for note in altered["notes"]:
                        if note["owner_id"] != account["id"]:
                            note["owner_id"] = account["id"]
                else:
                    note = next(n for n in altered["notes"] if n["owner_id"] == account["id"] and not n["deleted"])
                    if fault == "missing":
                        altered["notes"].remove(note)
                    else:
                        note["body"] = "Altered by faulty export"
                return original(root, altered, account, build)
            target = self.place / fault
            with patch.object(release, "export_for", broken):
                release.prepare(self.db, target, self.root)
            with self.assertRaisesRegex(ValueError, "Privacy or preservation"):
                release.validate_candidate(self.db, target, self.root)
        html = (self.out / manifest["accounts"][0]["file"]).read_bytes()
        with self.assertRaisesRegex(ValueError, "external"):
            release.check_html(html + b'<img src="https://untrusted.invalid/asset">')

    def test_interrupted_export_preserves_database(self):
        original = Path.write_bytes
        def interrupted(path, data):
            if path.suffix == ".html":
                raise OSError("Synthetic interrupted write")
            return original(path, data)
        with patch.object(Path, "write_bytes", interrupted):
            with self.assertRaises(OSError):
                release.prepare(self.db, self.out, self.root)
        self.assertFalse(self.out.exists())
        self.assertEqual(self.mode(), "frozen")
        with app.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM notes").fetchone()[0], 8)
        release.unfreeze(self.db)
        release.prepare(self.db, self.out, self.root)
        release.validate_candidate(self.db, self.out, self.root)

    def fixture_approval(self):
        # Only this disposable fixture seeds the verification ledger. The real CLI
        # registers it exclusively after pinned contracts and actual browser runs.
        manifest, manifest_sha = release.validate_candidate(self.db, self.out, self.root)
        report = {"status":"ready", "manifest_sha256":manifest_sha, "trusted_ref":self.baseline}
        raw = release.encoded(report)
        (self.out / "report.json").write_bytes(raw)
        approval = release.digest(raw)
        with app.connect(self.db) as db:
            db.execute("UPDATE service_state SET ready_digest=?,trusted_ref=? WHERE id=1", (approval,self.baseline))
        return approval

    def test_forged_and_stale_approval_cannot_retire(self):
        release.prepare(self.db, self.out, self.root)
        manifest, manifest_sha = release.validate_candidate(self.db, self.out, self.root)
        raw = release.encoded({"status":"ready","manifest_sha256":manifest_sha,"trusted_ref":self.baseline})
        (self.out / "report.json").write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "registered"):
            release.approve(self.db, self.out, self.root, release.digest(raw), self.baseline)
        approval = self.fixture_approval()
        artifact = self.out / manifest["accounts"][0]["file"]
        original = artifact.read_bytes()
        artifact.write_bytes(original + b"\n")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            release.approve(self.db, self.out, self.root, approval, self.baseline)
        artifact.write_bytes(original)
        release.unfreeze(self.db)
        release.freeze(self.db)
        with self.assertRaisesRegex(ValueError, "freeze changed"):
            release.approve(self.db, self.out, self.root, approval, self.baseline)
        self.assertEqual(self.mode(), "frozen")
        self.assertTrue(self.db.exists())

    def test_exact_approval_stops_only_own_server_and_keeps_data(self):
        with Running(self.db, self.root) as server:
            release.prepare(self.db, self.out, self.root)
            approval = self.fixture_approval()
            with self.assertRaisesRegex(ValueError, "Approval"):
                release.approve(self.db, self.out, self.root, "0"*64, self.baseline)
            self.assertEqual(server.request("GET", "/api/status")[0], 200)
            audit = release.approve(self.db, self.out, self.root, approval, self.baseline)
            self.assertTrue(audit["original_port_closed"])
            self.assertTrue(audit["database_preserved"])
        with app.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM notes").fetchone()[0], 8)
        with self.assertRaisesRegex(ValueError, "final"):
            release.unfreeze(self.db)

    def test_dirty_source_invalidates_candidate(self):
        release.prepare(self.db, self.out, self.root)
        path = self.root / "app.py"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n# changed after verification\n")
            with self.assertRaisesRegex(ValueError, "uncommitted"):
                release.validate_candidate(self.db, self.out, self.root)
        finally:
            path.write_bytes(original)

    def test_changed_gate_requires_new_trusted_baseline(self):
        path = self.root / "release.py"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n# changed trusted retirement controls\n")
            with self.assertRaisesRegex(ValueError, "retirement controls"):
                release.trusted_baseline(self.root, self.baseline)
        finally:
            path.write_bytes(original)

    def test_trusted_gate_copy_accepts_windows_utf8_bom(self):
        copied = self.place / "trusted-release.py"
        copied.write_bytes(b"\xef\xbb\xbf" + (self.root / "release.py").read_bytes())
        with patch.object(release, "__file__", str(copied)):
            self.assertEqual(release.trusted_baseline(self.root, self.baseline), self.baseline)

    def test_empty_exports_and_capacity_boundary(self):
        owner = self.keys["Alice"]["id"]
        with app.connect(self.db) as db:
            db.execute("UPDATE notes SET deleted=1 WHERE owner_id=?", (owner,))
        release.prepare(self.db, self.out, self.root)
        manifest, _ = release.validate_candidate(self.db, self.out, self.root)
        self.assertEqual(next(a["notes"] for a in manifest["accounts"] if a["id"] == owner), 0)
        release.unfreeze(self.db)
        with app.connect(self.db) as db:
            db.executemany("INSERT INTO notes VALUES(?,?,?,?,?,0)",
                [(str(app.uuid.uuid4()),owner,"A thought", "Kept", app.now()) for _ in range(1000)])
        with Running(self.db, self.root) as server:
            self.assertEqual(server.request("POST", "/api/notes", self.keys["Alice"]["token"],
                                           {"title":"Overflow", "body":"must not overwrite"})[0], 409)
            self.assertEqual(len(server.request("GET", "/api/notes", self.keys["Alice"]["token"])[1]["notes"]), 1000)

    def test_changed_snapshot_or_backup_blocks_retirement(self):
        release.prepare(self.db, self.out, self.root)
        approval = self.fixture_approval()
        with app.connect(self.db) as db:
            db.execute("UPDATE notes SET body='Changed without incrementing revision'")
        with self.assertRaisesRegex(ValueError, "data or freeze changed"):
            release.approve(self.db, self.out, self.root, approval, self.baseline)
        self.assertEqual(self.mode(), "frozen")
        # Check backup integrity against a new clean candidate as well.
        with app.connect(self.db) as db:
            snapshot = release.read_snapshot(db)
        target = self.place / "new-candidate"
        release.prepare(self.db, target, self.root)
        with app.connect(target / "source.sqlite3") as db:
            db.execute("UPDATE notes SET body='Tampered preserved backup'")
        with self.assertRaisesRegex(ValueError, "backup changed"):
            release.validate_candidate(self.db, target, self.root)
        with app.connect(self.db) as db:
            self.assertEqual(release.read_snapshot(db), snapshot)

    def test_failed_reverification_clears_registered_readiness(self):
        release.prepare(self.db, self.out, self.root)
        approval = self.fixture_approval()
        with patch.object(release, "run_checked", side_effect=ValueError("Synthetic verification failure")):
            with self.assertRaisesRegex(ValueError, "Synthetic verification failure"):
                release.verify(self.db, self.out, self.root, self.baseline)
        with self.assertRaisesRegex(ValueError, "registered"):
            release.approve(self.db, self.out, self.root, approval, self.baseline)
        self.assertEqual(self.mode(), "frozen")

    def test_publication_is_only_empty_reader_and_synthetic_sample(self):
        target = self.place / "public"
        release.public_reader(target, self.root)
        self.assertEqual(set(p.name for p in target.iterdir()), {"index.html","sample.html"})
        for path in target.iterdir():
            payload = release.check_html(path.read_bytes())
            self.assertNotIn("PRIVATE_CANARY", json.dumps(payload))
            self.assertFalse(any(a["token"] in json.dumps(payload) for a in self.keys.values()))
        (target / "private.json").write_text("secret")
        with self.assertRaisesRegex(ValueError, "unexpected"):
            release.public_reader(target, self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
