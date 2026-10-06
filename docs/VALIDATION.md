# Verified development build — 6 October 2026

GitHub [PR #1](https://github.com/AaryaMody1301/The-Last-Release/pull/1) merged
as `d52a76c09a2629fa6cb5360d71fc3f4daa36ebd8`. Its source tree is
`79f6bcef4cafad1e10801a3e613a13685a3fc898`, identical to the recovered build.

The [merged-main run](https://github.com/AaryaMody1301/The-Last-Release/actions/runs/37489071487)
and [survival job](https://github.com/AaryaMody1301/The-Last-Release/actions/runs/37489071487/job/112356679719)
passed the following checks:

| Check | Observed result |
|---|---|
| Python contracts | 14 passed |
| Browser engines | Chromium 151.0.7922.34 and Firefox 153.0 |
| Live download and offline drill | Both synthetic accounts passed |
| Offline actions | Read, search, create, edit, delete, backup, fresh-context restore |
| Observed offline HTTP(S) attempts | 0 |
| Complete candidate rehearsal | 6 active notes preserved across 2 accounts |
| Original disposable server | Stopped; original port closed |
| Database after fixture retirement | Preserved |
| Candidate browser drill duration | 16,930 ms |

The tests include wrong-token and cross-account operations, exact data
comparison, foreign/missing/altered-note negative controls, hostile text,
invalid backups, empty editions, keyboard labels/navigation, interrupted
packaging, changed source/controls/snapshot, forged/stale approvals, failed
reverification, public-output exclusions, and reversible freeze. Only the
disposable synthetic fixture is automatically retired.

The original hosted report, browser reports, and receipt are preserved in
[evidence/main-2026-10-06.json](evidence/main-2026-10-06.json). They are copied
from GitHub artifact `11425030775`, whose ZIP SHA-256 is
`bef2cec6f4b6d6e4e1da760f46818a1552c3ea216212a048674230c5d730e760`.
They contain synthetic counts and digests, not notebook contents or tokens.
The manifest SHA-256 for that completed run is
`8372ac798a0fec1b2e692e949d352768dea9d1897de91d13307646975a87d97c`.
This is historical evidence for the exact commit above, not approval for a
later candidate or an owner's real notebook.

The generated public package was also checked locally: exactly `index.html`
and `sample.html`, with an empty reader and explicitly synthetic sample.
The [one-line fault fixture](foreign-export.patch) makes the existing
exact-export contract reject a foreign-account export in a disposable clone.
This preparation is not a Duo repair session.

## Reproduce

```sh
npm ci --ignore-scripts
npx playwright install --with-deps chromium firefox
python tests/contracts.py
PYTHON=python TLR_BROWSERS=chromium,firefox npm run test:offline
TLR_BROWSERS=chromium,firefox python tests/rehearsal.py --trusted-ref HEAD
```

Start from a clean committed checkout and a new rehearsal output directory.
Private generated data remains ignored. In the current ChatGPT Linux
environment, Python contracts pass but local browser executables are absent;
the two-engine result above comes from the actual GitHub runner.

## Remaining proof

The project is a tested development prototype. Completion still requires a
public canonical GitLab project, sponsor credit/compute confirmation, actual
platform validation and enabling of the native flow, a capability smoke test,
a genuine failing-pipeline → Duo repair → passing-pipeline record, GitLab
Pages publication, and the public YouTube demo under three minutes.
See [PLAN-CHECK.md](PLAN-CHECK.md) and [DUO.md](DUO.md).
