# The Last Release

**The service can end. Your notes remain useful.**

A small notebook with a **software will**: each person keeps a working,
private offline edition when its backend retires. A deterministic exit
rehearsal checks that promise; a native GitLab Duo flow is configured to
repair failures and leave one outcome for owner review.

Built from scratch for GitLab **Life After Code 2026**, Path A / Supervised,
with Most Creative as the target. Python standard library, SQLite, one plain
HTML interface, and a browser-test dependency. No paid API, cloud account,
runtime packages, or frontend build step.

## Run the notebook

Requires Python 3.12+, Git, and a browser. From the repository directory:

```sh
python app.py seed
python app.py serve
```

On Windows, `./start.ps1` also locates the Python bundled with ChatGPT Work
Mode. Open **http://127.0.0.1:8000**. Copy Alice's or Bob's token from the
local `data/access-keys.json` into the login box. Tokens are generated for
this run and held only in the UI's memory. All initial notes are synthetic.
The server binds only to loopback and never serves repository files.

Create, search, edit, or delete a note. **Download offline edition** gives
you one self-contained HTML file. Stop the server and open that file: read,
search, create, edit, delete, save a JSON backup, and open it in a fresh
browser. The empty reader accepts a backup from any account; an existing
private edition refuses a different account's backup.

**Offline edits live in memory.** Save the note, then **Save backup** before
closing. An HTML file does not rewrite itself. Downloads and backups are
private, unencrypted files; whoever possesses them can read the notes.

## Verify the promises

Only browser verification requires Node 20+ and a dependency:

```sh
npm ci --ignore-scripts
npx playwright install --with-deps chromium firefox
python tests/contracts.py
npm run test:offline
```

Set `PYTHON` to the executable to use, if necessary. The default browser is
Chromium; if its Playwright build is absent, the check can use installed
Chrome. To run both submission browsers:

```sh
# Linux/macOS
PYTHON=python3 TLR_BROWSERS=chromium,firefox npm run test:offline
```

```powershell
# Windows
$env:PYTHON = 'python'
$env:TLR_BROWSERS = 'chromium,firefox'
npm run test:offline
```

The drill signs into two different accounts, downloads each private edition,
stops its **own disposable server**, confirms the original connection fails,
and opens the files in fresh browser contexts with networking disabled.
It edits, creates, deletes, downloads a backup, closes the context, and
restores the edit in another fresh context. Any attempted offline HTTP(S)
request fails the check. It also checks hostile text, keyboard navigation,
labels, unload warnings, and refusal of invalid/foreign/duplicate backups.

Contract checks independently compare exports with SQL snapshots and reject
foreign, missing, changed, or deleted notes. They cover authorization,
input limits, source changes, forged/stale approvals, interrupted packaging,
and reversible freeze. The verification ledger in the notebook database
must register a successful trusted run before the gate accepts approval.

## A complete synthetic rehearsal

Commit the checkout first; generated data is ignored. Review a baseline,
then run this **disposable** scenario:

```sh
python tests/rehearsal.py --trusted-ref HEAD
```

It creates two fresh synthetic accounts, freezes them, packages and verifies
the exact candidate, rejects a wrong approval, approves the verified result,
and proves the original fixture port closed. Private editions, the preserved
database, browser evidence, report, and retirement receipt stay under
`data/rehearsal/`. Choose `--out data/rehearsal-2` for a second run.
`TLR_BROWSERS=chromium,firefox` enables the final cross-browser rehearsal.

## Retire your local demo after reviewing its outcome

Preparation pauses writes; reads and exports remain available. No real
retirement happens during preparation or verification.

```sh
python release.py prepare --out data/candidate
```

Use a **pinned, owner-reviewed trusted commit**, whose tests and gate the
candidate is not allowed to weaken. Run the gate copied from that baseline,
rather than an agent-modified gate:

```sh
# Linux/macOS; run from the candidate repository
trusted=$(git rev-parse HEAD) # replace with the reviewed baseline when evaluating a repair
git show "$trusted:release.py" > data/trusted-release.py
python data/trusted-release.py verify --root . --out data/candidate --trusted-ref "$trusted" --browsers chromium,firefox
```

```powershell
# Windows; run from the candidate repository
$trustedSha = git rev-parse HEAD # replace with the reviewed baseline for a repair
git show "${trustedSha}:release.py" | Set-Content -Encoding utf8 data/trusted-release.py
python data/trusted-release.py verify --root . --out data/candidate --trusted-ref $trustedSha --browsers chromium,firefox
```

Verification executes contracts and browser tests extracted from that
baseline against the candidate. It rejects unreviewed changes to controls;
only the app, shared UI, and exporter block are eligible for a repair.
Review `data/candidate/report.json`, the private editions, and the printed
approval digest. Then run, using the actual digest and trusted commit:

```sh
python data/trusted-release.py retire --root . --out data/candidate --trusted-ref <reviewed-commit> --approve <printed-digest>
```

That command changes persisted state and lets the notebook server stop
itself. It checks the original port closed, preserves the database, and writes
a receipt. It never kills an unrelated process. Source, will, snapshot,
artifact, or freeze changes invalidate approval. A failed verification clears
the registered readiness; writing a fake report is insufficient.

Recover **before retirement** with:

```sh
python release.py unfreeze
```

That invalidates prior candidates. Prepare a new output directory and verify
again. After retirement, the saved database remains; recover to a **new**
database path from `source.sqlite3` and unfreeze that copy. Delivery, consent,
retention policy, and production account hosting are outside this prototype.

## GitLab Duo and free hosting

GitHub is the development repository. The hackathon requires a **public
GitLab submission repository and actual Duo execution**. Import/push this
new code into your sponsor-provisioned project. Follow [docs/DUO.md](docs/DUO.md)
to confirm credit coverage, register the flow, enable a human Mention trigger,
and retain genuine failure → repair → passing-pipeline evidence.

Committing `.gitlab/duo/flows/last-release.yml` alone does not register it.
The agent config must be on GitLab's default branch. Local contract/browser
success does not prove Duo ran. No external model API replaces that requirement.

GitLab CI provides contracts, the two-browser offline drill, the complete
disposable retirement rehearsal, packaging, and an optional manual Pages
job. GitHub Actions also verifies the development checkout. Both retain
only synthetic verification reports and the retirement receipt. The CI
rehearsal uses its current commit as a build smoke test; owner approval of a
repair still requires the original reviewed baseline. Pages publishes an **empty
reader** and **explicitly synthetic sample**, never private exports or databases:

```sh
python release.py public --out public
```

Open `public/index.html` to restore a backup or `public/sample.html` to try
the interface. Hosting a dynamic notebook server is unnecessary.

## Publish the development source

From this committed checkout, the owner can publish to the empty GitHub
repository with:

```sh
git push -u origin main
```

Use a normal push; an existing remote history must be reviewed rather than
overwritten. The source archive also includes `The-Last-Release.bundle`
when supplied through ChatGPT. Recover its committed checkout with
`git clone The-Last-Release.bundle The-Last-Release`, then point `origin` at
`https://github.com/AaryaMody1301/The-Last-Release.git` before pushing.
Open the repository's Actions tab to inspect the first genuine hosted run.

Import that source into the sponsor-provisioned GitLab project. In GitLab,
create a new issue using the **Last_Release_Repair** template, complete the
owner fields, and follow the registration steps in [docs/DUO.md](docs/DUO.md).

## Requirement and evidence map

| Plan requirement | Implemented in | Proof |
|---|---|---|
| R01–R02: private persistent live CRUD | `app.py`, shared UI | Ownership, restart, input and freeze contracts |
| R03: supported software will | `will.json`, `release.py` | Unsupported promises block before freeze |
| R04: exact per-account edition | Exporter and independent SQL comparison | Foreign/missing/changed-note negative controls |
| R05–R06: useful offline operations and restore | `web/notebook.html` | Real stopped-server browser drill |
| R07: Duo preparation/repair | Native flow and execution config | **Pending: actual provisioned Duo session/MR** |
| R08: evidence and limitations | Manifest, browser report, readiness report | Exact artifact and snapshot digests |
| R09–R10: final approval and recovery | Pinned gate and database verification ledger | Forged/stale approval and interrupted-write contracts |
| R11: free reproduction/public reader | CI, Pages, this README | Publication allowlist and fresh-checkout verification |
| R12: usable keyboard and save controls | Shared UI | Labels, Tab path, inert content, unload/import checks |

Runtime limits: 1,000 active notes per account; 200-character titles; 16 KiB
UTF-8 bodies; 20 MiB editions/backups. No attachments, rich HTML, collaboration,
account signup/recovery, automatic saving to the HTML file, or arbitrary-app
conversion. Hashes identify bytes; they are not encryption or a third-party
signature. Python's HTTP server is used only for this loopback demonstrator.

Novelty is the **release-time functional exit rehearsal**, with privacy and
an agent repair loop, rather than a claim that offline notebooks or archives
have never existed. Use synthetic data for the under-three-minute video.
See [docs/DUO.md](docs/DUO.md) for the remaining submission evidence.

MIT-licensed. Original contributions should use `git commit -s` with the
contributor's own identity. Playwright is an Apache-2.0 development dependency;
its optional macOS dependency fsevents is MIT. No third-party runtime assets
are embedded in notebook editions.
