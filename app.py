"""Loopback notebook demo. Runtime dependencies: Python's standard library."""

import argparse
import hashlib
import json
import secrets
import socket
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAX_NOTES, MAX_BODY, MAX_REQUEST = 1000, 16 * 1024, 32 * 1024


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def seed(path, keys):
    """Create synthetic data; refuse to overwrite an existing notebook or keys."""
    path, keys = Path(path), Path(keys)
    if path.resolve() == keys.resolve():
        raise ValueError("Database and access keys need separate paths.")
    if path.exists() or keys.exists():
        raise ValueError("Database or keys already exist. Choose new paths.")
    path.parent.mkdir(parents=True, exist_ok=True)
    keys.parent.mkdir(parents=True, exist_ok=True)
    tokens = {}
    with connect(path) as db:
        db.executescript("""
            CREATE TABLE accounts(id TEXT PRIMARY KEY, alias TEXT NOT NULL,
                                  token_hash TEXT NOT NULL UNIQUE);
            CREATE TABLE notes(id TEXT PRIMARY KEY, owner_id TEXT NOT NULL
                               REFERENCES accounts(id), title TEXT NOT NULL,
                               body TEXT NOT NULL, updated_at TEXT NOT NULL,
                               deleted INTEGER NOT NULL DEFAULT 0);
            CREATE INDEX notes_owner ON notes(owner_id, deleted);
            CREATE TABLE service_state(id INTEGER PRIMARY KEY CHECK(id=1),
                mode TEXT NOT NULL, revision INTEGER NOT NULL, epoch TEXT NOT NULL,
                ready_digest TEXT, trusted_ref TEXT, server_port INTEGER,
                server_nonce TEXT);
        """)
        db.execute("INSERT INTO service_state VALUES(1,'active',0,?,NULL,NULL,NULL,NULL)",
                   (secrets.token_hex(16),))
        for alias in ("Alice", "Bob"):
            account_id, token = str(uuid.uuid4()), secrets.token_urlsafe(32)
            tokens[alias] = {"id": account_id, "token": token}
            db.execute("INSERT INTO accounts VALUES(?,?,?)", (account_id, alias,
                       hashlib.sha256(token.encode()).hexdigest()))
            examples = [("A service can end", "Your notes should still have a future."),
                        ("My private notebook", f"{alias.upper()}_PRIVATE_CANARY — stays with {alias}."),
                        ("Text, never code", '<script>window.INJECTED=true</script> Café 🌱'),
                        ("Deleted note", f"{alias.upper()}_DELETED_CANARY")]
            for title, body in examples:
                db.execute("INSERT INTO notes VALUES(?,?,?,?,?,?)", (str(uuid.uuid4()),
                           account_id, title, body, now(), int(title == "Deleted note")))
    with keys.open("x", encoding="utf-8") as out:
        json.dump(tokens, out, indent=2)
    try:
        keys.chmod(0o600)
        path.chmod(0o600)
    except OSError:
        pass  # Windows permissions remain controlled by the user's directory ACL.
    return tokens


def note_input(value):
    if not isinstance(value, dict) or set(value) != {"title", "body"}:
        raise ValueError("Expected only title and body.")
    title, body = value["title"], value["body"]
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError("Title must contain 1–200 characters.")
    if not isinstance(body, str) or len(body.encode("utf-8")) > MAX_BODY:
        raise ValueError("Body must be at most 16 KiB of UTF-8 text.")
    return title, body


def handler(db_path, root):
    class NotebookHandler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # URLs and bearer credentials never enter logs.

        def reply(self, status, body, content_type="application/json", attachment=None):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if attachment:
                self.send_header("Content-Disposition", f'attachment; filename="{attachment}"')
            self.end_headers()
            self.wfile.write(body)

        def dispatch(self):
            host = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != host:
                return self.reply(400, {"error": "Unexpected Host."})
            if self.headers.get("Origin") not in (None, f"http://{host}"):
                return self.reply(403, {"error": "Unexpected Origin."})
            if "?" in self.path or "#" in self.path:
                return self.reply(404, {"error": "Not found."})
            with connect(db_path) as db:
                state = db.execute("SELECT * FROM service_state WHERE id=1").fetchone()
                if state["mode"] == "retired":
                    return self.reply(410, {"error": "Service retired. Open your private offline notebook."})
                if self.command == "GET" and self.path == "/":
                    from release import render_html
                    return self.reply(200, render_html(root, {"version": 1, "mode": "live",
                        "account": None, "notes": [], "build": {}}), "text/html; charset=utf-8")
                if self.command == "GET" and self.path == "/api/status":
                    return self.reply(200, {"mode": state["mode"], "revision": state["revision"]})
                auth = self.headers.get("Authorization", "")
                account = db.execute("SELECT id,alias FROM accounts WHERE token_hash=?", (
                    hashlib.sha256(auth[7:].encode()).hexdigest(),)).fetchone() if auth.startswith("Bearer ") else None
                if not account:
                    return self.reply(401, {"error": "A valid access token is required."})
                owner = account["id"]
                if self.command == "GET" and self.path == "/api/notes":
                    notes = [dict(n) for n in db.execute("SELECT id,title,body,updated_at FROM notes "
                        "WHERE owner_id=? AND deleted=0 ORDER BY id", (owner,))]
                    return self.reply(200, {"account": dict(account), "notes": notes, "mode": state["mode"]})
                if self.command == "GET" and self.path == "/api/export":
                    from release import export_for, read_snapshot
                    # One read transaction keeps account, notes, and revision consistent.
                    db.execute("BEGIN")
                    data = read_snapshot(db)
                    html = export_for(root, data, dict(account), {"source": "live preview"})
                    return self.reply(200, html, "text/html; charset=utf-8", f"notebook-{owner}.html")
                is_create = self.command == "POST" and self.path == "/api/notes"
                is_note = self.path.startswith("/api/notes/") and self.command in ("PATCH", "DELETE")
                if not is_create and not is_note:
                    return self.reply(404, {"error": "Not found."})
                if self.headers.get("Transfer-Encoding"):
                    return self.reply(400, {"error": "Transfer encoding is unsupported."})
                if self.command != "DELETE":
                    if self.headers.get("Content-Type") != "application/json":
                        return self.reply(415, {"error": "Send application/json."})
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= MAX_REQUEST:
                        return self.reply(413, {"error": "Request exceeds 32 KiB or is empty."})
                    title, body = note_input(json.loads(self.rfile.read(length)))
                db.execute("BEGIN IMMEDIATE")
                if db.execute("SELECT mode FROM service_state WHERE id=1").fetchone()[0] != "active":
                    return self.reply(409, {"error": "Notebook frozen for an exit rehearsal. Writes are paused."})
                note_id = str(uuid.uuid4()) if is_create else self.path.removeprefix("/api/notes/")
                if not is_create and not db.execute("SELECT 1 FROM notes WHERE id=? AND owner_id=? "
                    "AND deleted=0", (note_id, owner)).fetchone():
                    return self.reply(404, {"error": "Note not found."})
                if is_create:
                    if db.execute("SELECT COUNT(*) FROM notes WHERE owner_id=? AND deleted=0",
                                  (owner,)).fetchone()[0] >= MAX_NOTES:
                        return self.reply(409, {"error": "Limit of 1,000 active notes reached."})
                    db.execute("INSERT INTO notes VALUES(?,?,?,?,?,0)", (note_id, owner, title, body, now()))
                elif self.command == "PATCH":
                    db.execute("UPDATE notes SET title=?,body=?,updated_at=? WHERE id=? AND owner_id=?",
                               (title, body, now(), note_id, owner))
                else:
                    db.execute("UPDATE notes SET deleted=1,updated_at=? WHERE id=? AND owner_id=?",
                               (now(), note_id, owner))
                db.execute("UPDATE service_state SET revision=revision+1,ready_digest=NULL,trusted_ref=NULL WHERE id=1")
                db.commit()
                return self.reply(201 if is_create else 200, {"id": note_id})

        def run_request(self):
            try:
                self.connection.settimeout(5)
                self.dispatch()
            except (ValueError, UnicodeError, json.JSONDecodeError):
                self.reply(400, {"error": "Invalid JSON or note fields."})
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
            except (OSError, sqlite3.Error):
                self.reply(503, {"error": "Notebook unavailable. The database has been preserved."})

        do_GET = do_POST = do_PATCH = do_DELETE = run_request
    return NotebookHandler


def serve(path, port=8000, root=ROOT):
    if not Path(path).is_file():
        raise ValueError("No database. Run app.py seed first.")
    server = HTTPServer(("127.0.0.1", port), handler(path, root))
    server.timeout = 0.25
    nonce = secrets.token_hex(16)
    try:
        with connect(path) as db:
            db.execute("BEGIN IMMEDIATE")
            state = db.execute("SELECT * FROM service_state WHERE id=1").fetchone()
            if state["mode"] == "retired":
                raise ValueError("This service is retired. Its database is preserved.")
            # Binding succeeded, so a stale record for this same port cannot be another server.
            if state["server_nonce"] and state["server_port"] and state["server_port"] != server.server_port:
                try:
                    with socket.create_connection(("127.0.0.1", state["server_port"]), timeout=0.3):
                        raise ValueError("A server for this database is already running.")
                except OSError:
                    pass
            db.execute("UPDATE service_state SET server_port=?,server_nonce=? WHERE id=1",
                       (server.server_port, nonce))
        print(f"Notebook: http://127.0.0.1:{server.server_port}", flush=True)
        while True:
            with connect(path) as db:
                if db.execute("SELECT mode FROM service_state WHERE id=1").fetchone()[0] == "retired":
                    break
            server.handle_request()
    finally:
        server.server_close()
        with connect(path) as db:
            db.execute("UPDATE service_state SET server_port=NULL,server_nonce=NULL WHERE server_nonce=?", (nonce,))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=("seed", "serve"))
    cli.add_argument("--db", type=Path, default=ROOT / "data/notebook.sqlite3")
    cli.add_argument("--keys", type=Path, default=ROOT / "data/access-keys.json")
    cli.add_argument("--port", type=int, default=8000)
    args = cli.parse_args()
    try:
        if args.command == "seed":
            seed(args.db, args.keys)
            print(f"Created two synthetic accounts. Private access tokens: {args.keys}")
        else:
            serve(args.db, args.port)
    except (ValueError, OSError, sqlite3.Error) as exc:
        cli.exit(1, f"Blocked: {exc}\n")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
