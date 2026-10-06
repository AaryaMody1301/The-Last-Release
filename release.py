"""Prepare an exit rehearsal, verify its promises, then approve the exact result."""

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import sqlite3
import subprocess
import tempfile
import time
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAX_FILE = 20 * 1024 * 1024
EXPORT_START, EXPORT_END = "# EXPORT IMPLEMENTATION START", "# EXPORT IMPLEMENTATION END"


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


@contextmanager
def database(path):
    if not Path(path).is_file():
        raise ValueError("Database does not exist.")
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def read_snapshot(db):
    state = dict(db.execute("SELECT mode,revision,epoch FROM service_state WHERE id=1").fetchone())
    return {"state": state,
            "accounts": [dict(a) for a in db.execute("SELECT * FROM accounts ORDER BY id")],
            "notes": [dict(n) for n in db.execute("SELECT * FROM notes ORDER BY id")]}


def expected_notes(snapshot, owner):
    return [{k: n[k] for k in ("id", "title", "body", "updated_at")}
            for n in snapshot["notes"] if n["owner_id"] == owner and not n["deleted"]]


def validate_will(root):
    raw = (root / "will.json").read_bytes()
    if len(raw) > 16384:
        raise ValueError("Software will exceeds 16 KiB.")
    will = json.loads(raw)
    scalar = {"version": 1, "app": "notebook", "privacy": "one-account-per-export",
              "retirement": "owner-approved"}
    lists = {"preserve": ["title", "body", "updated_at"],
             "offline_actions": ["read", "search", "create", "edit", "delete", "backup", "restore"],
             "exclude": ["deleted_notes", "access_tokens"]}
    if not isinstance(will, dict) or set(will) != set(scalar) | set(lists):
        raise ValueError("Unsupported software will keys. No promises have been discarded.")
    if type(will["version"]) is not int or any(will[k] != v for k, v in scalar.items()):
        raise ValueError("Unsupported software will policy.")
    for key, required in lists.items():
        value = will[key]
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value) or sorted(value) != sorted(required):
            raise ValueError(f"Unsupported {key} promises. This edition supports {', '.join(required)}.")
    return digest(raw)


# EXPORT IMPLEMENTATION START
def render_html(root, payload):
    """One shared UI; offline CSP forbids every connection and external asset."""
    template = (root / "web/notebook.html").read_text(encoding="utf-8")
    code = re.search(r'<script id="notebook-code">([\s\S]*?)</script>', template)
    if not code:
        raise ValueError("Notebook template is missing its inline script.")
    script_hash = base64.b64encode(hashlib.sha256(code[1].encode()).digest()).decode()
    data = base64.b64encode(encoded(payload)).decode()
    result = template.replace("__SCRIPT_HASH__", script_hash).replace("__PAYLOAD__", data)
    result = result.replace("__CONNECT__", "'self'" if payload["mode"] == "live" else "'none'")
    if len(result.encode("utf-8")) > MAX_FILE:
        # ponytail: buffered exports are capped at 20 MiB; review a streaming format before raising it.
        raise ValueError("Notebook exceeds the 20 MiB export limit.")
    return result.encode("utf-8")


def export_for(root, snapshot, account, build):
    notes = [{k: n[k] for k in ("id", "title", "body", "updated_at")}
             for n in snapshot["notes"] if n["owner_id"] == account["id"] and not n["deleted"]]
    return render_html(root, {"version": 1, "mode": "offline", "account": account,
                             "notes": notes, "build": build})
# EXPORT IMPLEMENTATION END


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if result.returncode:
        raise ValueError("Git command failed. Use a committed checkout and an existing trusted ref.")
    return result.stdout


def source_identity(root):
    if git(root, "status", "--porcelain", "--untracked-files=all").strip():
        raise ValueError("Source has uncommitted changes. Commit or discard them before preparing.")
    paths = git(root, "ls-files", "-z").decode().strip("\0").split("\0")
    source = hashlib.sha256()
    for name in sorted(paths):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Candidate source must contain regular tracked files.")
        source.update(name.encode() + b"\0" + path.read_bytes() + b"\0")
    return {"commit": git(root, "rev-parse", "HEAD").decode().strip(), "sha256": source.hexdigest()}


def without_export(text):
    # Anchors match whole lines, never this function's literal marker constants.
    start = text.index("\n" + EXPORT_START + "\n")
    end = text.index("\n" + EXPORT_END + "\n", start)
    return text[:start] + text[end:]


def trusted_baseline(root, ref):
    sha = git(root, "rev-parse", "--verify", ref + "^{commit}").decode().strip()
    baseline = git(root, "show", sha + ":release.py").decode("utf-8-sig")
    if without_export(Path(__file__).read_text(encoding="utf-8-sig")) != without_export(baseline):
        raise ValueError("Run the gate from the pinned trusted baseline, as described in README.")
    changed = git(root, "diff", "--name-only", sha, "HEAD").decode().splitlines()
    allowed = {"app.py", "web/notebook.html", "release.py"}
    if set(changed) - allowed:
        raise ValueError("Candidate changed trusted files. Owner review and a new baseline are required.")
    if without_export((root / "release.py").read_text(encoding="utf-8-sig")) != without_export(baseline):
        raise ValueError("Candidate changed retirement controls outside its exporter.")
    return sha


def freeze(path):
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        state = db.execute("SELECT mode FROM service_state WHERE id=1").fetchone()[0]
        if state == "retired":
            raise ValueError("The service is already retired.")
        if state == "active":
            db.execute("UPDATE service_state SET mode='frozen',revision=revision+1,epoch=?,"
                       "ready_digest=NULL,trusted_ref=NULL WHERE id=1", (secrets.token_hex(16),))


def unfreeze(path):
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT mode FROM service_state WHERE id=1").fetchone()[0] == "retired":
            raise ValueError("Retirement is final for this demo database. Restore its preserved backup to a new path.")
        db.execute("UPDATE service_state SET mode='active',revision=revision+1,epoch=?,"
                   "ready_digest=NULL,trusted_ref=NULL WHERE id=1", (secrets.token_hex(16),))


def prepare(path, out, root):
    will_sha, source = validate_will(root), source_identity(root)
    if out.exists():
        raise ValueError("Candidate directory already exists. Choose a new output directory.")
    freeze(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".candidate-", dir=out.parent)).resolve()
    try:
        with database(path) as db:
            db.execute("BEGIN")
            snapshot = read_snapshot(db)
            with closing(sqlite3.connect(stage / "source.sqlite3")) as backup:
                db.backup(backup)
        manifest = {"version": 1, "source": source, "will_sha256": will_sha,
                    "snapshot_sha256": digest(encoded(snapshot)),
                    "revision": snapshot["state"]["revision"], "epoch": snapshot["state"]["epoch"],
                    "accounts": []}
        for entry in snapshot["accounts"]:
            account = {"id": entry["id"], "alias": entry["alias"]}
            filename = f'notebook-{entry["id"]}.html'
            html = export_for(root, snapshot, account, source)
            (stage / filename).write_bytes(html)
            manifest["accounts"].append({"id": account["id"], "file": filename,
                "notes": len(expected_notes(snapshot, account["id"])), "sha256": digest(html)})
        (stage / "manifest.json").write_bytes(encoded(manifest))
        os.replace(stage, out)
        return manifest
    finally:
        if stage.exists() and stage.parent == out.parent.resolve() and stage.name.startswith(".candidate-"):
            shutil.rmtree(stage)


class NotebookHTML(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.parts, self.current, self.csp = {}, None, None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if any(k.startswith("on") or k in ("src", "srcset", "href", "action") for k in attrs):
            raise ValueError("Offline artifact contains an external asset, navigation, or inline event handler.")
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "content-security-policy":
            if self.csp is not None:
                raise ValueError("Duplicate content security policy.")
            self.csp = attrs.get("content")
        if tag == "script":
            name = attrs.get("id")
            if name not in ("notebook-data", "notebook-code") or name in self.parts:
                raise ValueError("Unexpected or duplicate script in notebook.")
            self.current = name
            self.parts[name] = ""
        if tag == "style":
            self.current = "style"
            self.parts["style"] = ""

    def handle_data(self, data):
        if self.current:
            self.parts[self.current] += data

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.current = None


def check_html(html):
    parsed = NotebookHTML(html.decode("utf-8"))
    if set(parsed.parts) != {"notebook-data", "notebook-code", "style"}:
        raise ValueError("Missing notebook data, code, or style.")
    code_hash = base64.b64encode(hashlib.sha256(parsed.parts["notebook-code"].encode()).digest()).decode()
    expected = ("default-src 'none'; script-src 'sha256-" + code_hash + "'; style-src 'unsafe-inline'; "
                "connect-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'")
    if parsed.csp != expected or re.search(r"url\s*\(|@import", parsed.parts["style"], re.I):
        raise ValueError("Offline content security policy or styles allow dependencies.")
    payload = json.loads(base64.b64decode(parsed.parts["notebook-data"], validate=True).decode("utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"version", "mode", "account", "notes", "build"}:
        raise ValueError("Unsupported embedded notebook format.")
    if payload["version"] != 1 or payload["mode"] != "offline":
        raise ValueError("Artifact is not an offline notebook.")
    return payload


def checked_bytes(path, limit=MAX_FILE):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("Candidate file is missing, linked, or oversized.")
    return path.read_bytes()


def validate_candidate(path, out, root):
    raw = checked_bytes(out / "manifest.json", 1024 * 1024)
    manifest = json.loads(raw)
    with database(path) as db:
        db.execute("BEGIN")
        snapshot = read_snapshot(db)
    if snapshot["state"]["mode"] not in ("frozen", "retired"):
        raise ValueError("Notebook must be frozen for final verification.")
    if manifest["source"] != source_identity(root) or manifest["will_sha256"] != validate_will(root):
        raise ValueError("Source or software will changed. Prepare again.")
    # Retired state is the only permitted final-state change.
    snapshot["state"]["mode"] = "frozen"
    if manifest["snapshot_sha256"] != digest(encoded(snapshot)) or manifest["revision"] != snapshot["state"]["revision"] or manifest["epoch"] != snapshot["state"]["epoch"]:
        raise ValueError("Notebook data or freeze changed. Prepare again.")
    accounts = snapshot["accounts"]
    if [a["id"] for a in manifest["accounts"]] != [a["id"] for a in accounts]:
        raise ValueError("Manifest is missing or duplicates an account.")
    for entry, account in zip(manifest["accounts"], accounts):
        filename = f'notebook-{account["id"]}.html'
        if entry["file"] != filename:
            raise ValueError("Unexpected artifact path.")
        html = checked_bytes(out / filename)
        if digest(html) != entry["sha256"]:
            raise ValueError("Artifact bytes changed.")
        payload = check_html(html)
        expected = expected_notes(snapshot, account["id"])
        if payload["account"] != {"id": account["id"], "alias": account["alias"]} or payload["notes"] != expected or payload["build"] != manifest["source"] or entry["notes"] != len(expected):
            raise ValueError("Privacy or preservation failed: missing, altered, deleted, or foreign notes.")
        if account["token_hash"].encode() in html or account["token_hash"] in json.dumps(payload):
            raise ValueError("Credentials leaked into an artifact.")
    backup = out / "source.sqlite3"
    with database(backup) as db:
        if digest(encoded(read_snapshot(db))) != manifest["snapshot_sha256"]:
            raise ValueError("Preserved database backup changed.")
    return manifest, digest(raw)


def run_checked(command, env, cwd):
    result = subprocess.run(command, env=env, cwd=cwd, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise ValueError("Trusted verification failed.\n" + result.stdout[-3000:] + result.stderr[-3000:])
    return result.stdout


def verify(path, out, root, trusted_ref, browsers="chromium"):
    import sys
    trusted = trusted_baseline(root, trusted_ref)
    manifest, manifest_sha = validate_candidate(path, out, root)
    with database(path) as db:
        db.execute("UPDATE service_state SET ready_digest=NULL,trusted_ref=NULL WHERE id=1")
    env = dict(os.environ, TLR_SOURCE_ROOT=str(root), PYTHON=sys.executable,
               TLR_BROWSERS=browsers, TLR_CANDIDATE=str(out), TLR_BROWSER_REPORT=str(out / "browser-report.json"))
    with tempfile.TemporaryDirectory(prefix="last-release-trusted-") as directory:
        temp = Path(directory)
        for name in ("contracts.py", "offline.spec.mjs"):
            (temp / name).write_bytes(git(root, "show", trusted + ":tests/" + name))
        run_checked([sys.executable, str(temp / "contracts.py")], env, root)
        run_checked(["node", str(temp / "offline.spec.mjs")], env, root)
    observed = json.loads(checked_bytes(out / "browser-report.json", 1024 * 1024))
    requested = browsers.split(",")
    if not requested or set(requested) - {"chromium", "firefox"}:
        raise ValueError("Only Chromium and Firefox are supported browser checks.")
    if observed["manifest_sha256"] != manifest_sha or observed["browsers"] != requested or observed["accounts_checked"] != len(manifest["accounts"]) or observed["http_attempts"] != 0:
        raise ValueError("Browser evidence does not match the candidate.")
    # Recheck after the full drill, including changes made while tests ran.
    validate_candidate(path, out, root)
    report = {"version": 1, "status": "ready", "manifest_sha256": manifest_sha,
        "trusted_ref": trusted, "source": manifest["source"], "will_sha256": manifest["will_sha256"],
        "revision": manifest["revision"], "notes_preserved": sum(a["notes"] for a in manifest["accounts"]),
        "accounts_checked": len(manifest["accounts"]), "http_attempts": 0,
        "browsers": requested, "checks": ["trusted-contracts", "private-data-fidelity", "offline-edit-backup-restore"],
        "unsupported": ["attachments", "collaboration", "automatic file saving", "arbitrary applications"],
        "duo_evidence": "not established by local verification",
        "verified_at": datetime.now(timezone.utc).isoformat()}
    raw = encoded(report)
    (out / "report.json").write_bytes(raw)
    approval = digest(raw)
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        snapshot = read_snapshot(db)
        if digest(encoded(snapshot)) != manifest["snapshot_sha256"]:
            raise ValueError("Notebook changed during verification.")
        db.execute("UPDATE service_state SET ready_digest=?,trusted_ref=? WHERE id=1", (approval, trusted))
    return approval, report


def approve(path, out, root, approval, trusted_ref):
    trusted = trusted_baseline(root, trusted_ref)
    manifest, manifest_sha = validate_candidate(path, out, root)
    report_raw = checked_bytes(out / "report.json", 1024 * 1024)
    report = json.loads(report_raw)
    if approval != digest(report_raw) or report.get("status") != "ready" or report.get("manifest_sha256") != manifest_sha or report.get("trusted_ref") != trusted:
        raise ValueError("Approval does not match the verified report.")
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        state = db.execute("SELECT * FROM service_state WHERE id=1").fetchone()
        if state["ready_digest"] != approval or state["trusted_ref"] != trusted:
            raise ValueError("No trusted verification is registered for this approval.")
        snapshot = read_snapshot(db)
        snapshot["state"]["mode"] = "frozen"
        if digest(encoded(snapshot)) != manifest["snapshot_sha256"]:
            raise ValueError("Notebook changed before approval.")
        db.execute("UPDATE service_state SET mode='retired' WHERE id=1")
        port = state["server_port"]
    deadline = time.monotonic() + 8
    if port:
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    time.sleep(0.1)
            except OSError:
                break
        else:
            raise ValueError("Retirement recorded; server stop is pending. Database preserved. Retry this exact command.")
    audit = {"approval": approval, "manifest_sha256": manifest_sha, "trusted_ref": trusted,
             "mode": "retired", "original_port_closed": bool(port), "database_preserved": Path(path).is_file()}
    (out / "retirement.json").write_bytes(encoded(audit))
    return audit


def public_reader(out, root):
    """Publish an empty reader and an explicitly synthetic sample only."""
    out.mkdir(parents=True, exist_ok=True)
    if set(p.name for p in out.iterdir()) - {"index.html", "sample.html"}:
        raise ValueError("Public output contains unexpected files. Use an empty directory.")
    empty = {"version": 1, "mode": "offline", "account": None, "notes": [], "build": {"edition": "public reader"}}
    (out / "index.html").write_bytes(render_html(root, empty))
    sample = {"version": 1, "mode": "offline", "account": {"id": "00000000-0000-4000-8000-000000000001", "alias": "Public sample"},
        "notes": [{"id": "00000000-0000-4000-8000-000000000002", "title": "This notebook survives",
                   "body": "Synthetic public data. Try editing, saving a backup, and reopening it in the empty reader.",
                   "updated_at": "2026-10-06T00:00:00+00:00"}], "build": {"edition": "synthetic public sample"}}
    (out / "sample.html").write_bytes(render_html(root, sample))
    check_html((out / "index.html").read_bytes())
    check_html((out / "sample.html").read_bytes())


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=("prepare", "verify", "retire", "unfreeze", "status", "public"))
    cli.add_argument("--root", type=Path, default=Path.cwd())
    cli.add_argument("--db", type=Path, default=Path("data/notebook.sqlite3"))
    cli.add_argument("--out", type=Path, default=Path("data/candidate"))
    cli.add_argument("--trusted-ref")
    cli.add_argument("--approve")
    cli.add_argument("--browsers", default="chromium")
    args = cli.parse_args()
    root, path, out = args.root.resolve(), args.db.resolve(), args.out.resolve()
    try:
        if args.command == "prepare":
            manifest = prepare(path, out, root)
            print(f"Frozen candidate prepared: {out}\nAccounts: {len(manifest['accounts'])}. Run verify before approval.")
        elif args.command in ("verify", "retire"):
            if not args.trusted_ref:
                raise ValueError("--trusted-ref must name an owner-reviewed baseline commit.")
            if args.command == "verify":
                approval, report = verify(path, out, root, args.trusted_ref, args.browsers)
                print(f"READY: {report['notes_preserved']} notes; {report['accounts_checked']} accounts; zero HTTP attempts.\nApproval digest: {approval}")
            else:
                if not args.approve:
                    raise ValueError("--approve must contain the exact verified report digest.")
                print(json.dumps(approve(path, out, root, args.approve, args.trusted_ref), indent=2))
        elif args.command == "unfreeze":
            unfreeze(path)
            print("Notebook active again. Previous approvals are invalid.")
        elif args.command == "status":
            with database(path) as db:
                print(json.dumps(dict(db.execute("SELECT mode,revision,ready_digest,server_port FROM service_state WHERE id=1").fetchone()), indent=2))
        else:
            public_reader(out, root)
            print(f"Public reader and synthetic sample: {out}")
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error, subprocess.TimeoutExpired) as exc:
        cli.exit(1, f"Blocked: {exc}\nDatabase preserved. If frozen, recover with: python release.py unfreeze --db {path}\n")


if __name__ == "__main__":
    main()
