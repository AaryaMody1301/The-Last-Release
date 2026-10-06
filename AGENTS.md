# The Last Release

Use Ponytail full mode: Python standard library, SQLite, one plain HTML UI,
native GitLab features, no runtime dependencies or speculative frameworks.
Keep validation, privacy, accessibility, and protection against data loss.

This is a loopback-only synthetic notebook demo. Never publish `data/`,
tokens, databases, private notebooks, or backups. Do not retire an owner's
service: only the owner runs the final approval command.

For Duo repair, change only `app.py`, `web/notebook.html`, or the block between
`# EXPORT IMPLEMENTATION START` and `# EXPORT IMPLEMENTATION END` in
`release.py`. Tests, will, CI, flow policy, and the rest of the gate are trusted
controls. Changes to those require owner review and a new trusted baseline.
Use one branch/MR and at most two repair attempts per candidate. Never weaken
a check to make a release pass. Never fabricate CI, Duo, or browser evidence.

Checks: `python tests/contracts.py` and `npm run test:offline`.
GitLab Duo integration is unverified until a real provisioned project runs it.
