# Local validation — 6 October 2026

This is a working local prototype, not a completed hackathon submission.

Verified on Windows with Python 3.12.14, Node 24.18.0, Playwright 1.62.1,
and installed Chrome 154.0.8037.98 (Chromium engine):

- **14 standard-library contract checks pass.** They cover account isolation,
  persistent CRUD, limits, empty exports, exact data fidelity, foreign/missing/
  altered-note failures, interrupted packaging, snapshot/backup tampering,
  dirty source, changed gate code, stale/forged approval, failed reverification,
  final stop, public-output exclusions, and trusted-gate copies from Windows shells.
- The real-browser drill passes for both synthetic accounts. Each downloads
  a private HTML edition; the original disposable server stops and becomes
  unreachable; fresh offline contexts read/search/create/edit/delete, save
  backups, and restore exact edits and timestamps in another fresh context.
- Passing editions make **zero observed offline HTTP(S) attempts**. A deliberate
  dependency canary proves that CSP-blocked attempts are detected too, so
  blocked dependencies cannot silently count as successful offline operation.
- Keyboard/label/save-warning checks pass. Foreign, duplicate, and oversized
  note backups leave the existing notebook intact. A 390-pixel viewport has
  no horizontal overflow; the 1440-pixel interface was visually inspected.
- The complete disposable rehearsal preserves **six active notes across two
  accounts**, runs pinned verification, rejects a wrong approval, stops its
  original server, and keeps the database and private editions.
- The installed dependency lock resolves the expected three development
  packages. Runtime dependency count is zero.

Reproduce with `python tests/contracts.py`, `npm run test:offline`, and
`python tests/rehearsal.py --trusted-ref HEAD` from a clean committed checkout.
Generated machine evidence lives under `test-results/` and each local
`data/rehearsal*/candidate/`. Those private runtime directories are ignored.

## Remaining external proof

Firefox is not installed in this environment; its run remains pending.
An installation attempt reached a network access denial (`EACCES`); it did
not produce a browser result.
Both CI configurations request Chromium and Firefox, but hosted CI has not
run. GitLab's browser job now includes the complete disposable rehearsal
and retains its synthetic reports and retirement receipt. The new repair
issue template provides the owner fields and failure/repair evidence register.
The GitLab Duo definition still needs actual platform validation,
registration, sponsored credit coverage, a capability smoke test, and a
genuine failure/agent-repair/passing-pipeline demonstration. Public Pages and
the YouTube submission video also remain pending.

The GitHub repository was empty when inspected. This session's GitHub write
tool requires approval, while session policy disallows approvals; no code was
pushed and no PR was created. The completed source is in one local commit
with the intended GitHub remote, ready for the owner to publish.
