"""A complete disposable, synthetic freeze/verify/approve/stop rehearsal."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app
import release
from contracts import Running


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--trusted-ref", required=True)
    cli.add_argument("--out", type=Path, default=ROOT / "data/rehearsal")
    args = cli.parse_args()
    place = args.out.resolve()
    if place.exists():
        cli.exit(1, "Choose a new rehearsal output directory; existing data is never overwritten.\n")
    place.mkdir(parents=True)
    db, out = place / "notebook.sqlite3", place / "candidate"
    app.seed(db, place / "access-keys.json")
    with Running(db, ROOT) as server:
        release.prepare(db, out, ROOT)
        approval, report = release.verify(db, out, ROOT, args.trusted_ref, os.environ.get("TLR_BROWSERS", "chromium"))
        try:
            release.approve(db, out, ROOT, "0"*64, args.trusted_ref)
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong approval must block retirement.")
        assert server.request("GET", "/api/status")[0] == 200
        audit = release.approve(db, out, ROOT, approval, args.trusted_ref)
        assert audit["original_port_closed"] and audit["database_preserved"]
    print(f"Rehearsal passed: {report['notes_preserved']} notes across {report['accounts_checked']} accounts; zero offline HTTP attempts.")
    print(f"Original disposable server stopped. Database and private editions preserved at {place}.")
    print("GitLab Duo evidence must still come from a real provisioned flow session.")


if __name__ == "__main__":
    main()
