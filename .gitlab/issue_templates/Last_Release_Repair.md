# Synthetic software-will repair

Complete the owner fields before mentioning the assigned Duo service account.
This issue authorizes work on a disposable fixture only.

## Owner fields

- Sponsor credit/compute coverage confirmed: **PENDING**
- Public project URL: **PENDING**
- Original owner-reviewed trusted commit SHA: **PENDING**
- Candidate branch and existing MR (one per candidate): **PENDING**
- Failing pipeline/job URL and assertion: **PENDING**
- Previous repair attempts for this candidate (0, 1, or 2): **PENDING**
- Previous session/attempt references: **PENDING**

## Demonstration failure

Use synthetic Alice/Bob notes. On the candidate branch, remove only the
`owner_id` predicate in `export_for` inside the marked exporter block in
`release.py`. Preserve the deleted-note exclusion. The independent exact
snapshot comparison should reject the foreign account's notes even when
the exporter regenerates matching artifact checksums.

First record the actual failing contract/pipeline. Ask Duo to restore
account isolation, rerun the existing checks, and update the same repair MR.
Do not label this local mutation or a manually written fix as Duo evidence.

## Allowed outcome

Read AGENTS.md, will.json, README.md, and docs/DUO.md. Edit only app.py,
web/notebook.html, or the marked exporter block in release.py. Preserve
tests, controls, CI, the will, and flow policy. Use the original trusted
baseline for the disposable rehearsal. No owner's live service is in scope.

At most two repair attempts are allowed in total, including prior sessions.
Record the attempt before editing; do not reset the count in a new session.
If coverage/access is missing or two repairs have already been attempted,
report BLOCKED with actual evidence. Otherwise finish with READY FOR OWNER
REVIEW or BLOCKED, with session, commit, MR, and failed/passed job links.

Do not include tokens, databases, private HTML, or note backups in this
issue, its comments, the MR, or public artifacts. Retain the synthetic
verification report, browser report, and retirement receipt from CI.

## Outcome record

- Actual Duo session and flow version: **PENDING**
- Repair attempt total and commit: **PENDING**
- MR and passing pipeline: **PENDING**
- Synthetic report/browser report/receipt links: **PENDING**
- Remaining limitations and owner review: **PENDING**
