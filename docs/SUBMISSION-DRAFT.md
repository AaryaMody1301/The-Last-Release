# Submission and recording draft

Prepared 6 October 2026 while sponsor onboarding is pending. This is a draft,
not a submitted entry or a claim that Duo ran. Replace the pending evidence
with genuine public links before submission. Record the repair footage only
after an actual native Duo session succeeds.

## Entry fields

| Field | Draft value |
|---|---|
| Project | The Last Release |
| Tagline | The service can end. Your notes remain useful. |
| Path | A — Start Fresh |
| Autonomy | Supervised |
| Special-prize target | Most Creative |
| Development repo | https://github.com/AaryaMody1301/The-Last-Release |
| Public canonical GitLab repo | PENDING: sponsor onboarding and source import |
| Native Duo session / repair MR | PENDING: actual platform execution |
| GitLab failed / passed pipelines | PENDING: synthetic failure and genuine repair |
| Public reader / sample | PENDING: GitLab Pages deployment |
| Public YouTube video | PENDING: record and upload under three minutes |

## Project description

Most apps help people create work. The Last Release asks what happens to that
work when the service closes.

It is a small notebook with a software will: each account must keep its own
active notes, search and edit them offline, and save and restore changes. A
downloaded edition is one HTML file. It opens without a server, installation,
CDN, or paid API. Edits stay in memory until the person downloads a JSON backup;
the interface makes that saving step explicit.

The live notebook uses Python's standard library and SQLite. Both live and
offline editions share one plain HTML interface. Deterministic checks compare
each export with an independent database snapshot, reject another account's
notes, and exercise the downloaded file in real browsers after stopping the
disposable server. A pinned verification gate checks the exact source, will,
snapshot and artifact identities before an owner can approve retirement.
The database remains available for recovery.

The creative demonstration is a failed exit rehearsal. A synthetic-only
exporter deliberately includes another account's note. The trusted check
blocks the candidate. The configured native GitLab Duo flow is intended to
repair the exporter on one candidate branch, rerun verification, and leave
one outcome for owner review. This integration is configured but has not yet
run in the sponsor project.

The completed GitHub build passed 14 Python contracts, Chromium and Firefox
offline tests, and a full disposable rehearsal. That run preserved six active
notes across two accounts, observed zero offline HTTP(S) attempts, closed the
original fixture port, and preserved its database. These results establish
the notebook and its deterministic gate; they do not establish a Duo session.

This prototype supports plain-text notes. Attachments, collaboration, automatic
saving to the original HTML file, production account hosting, and conversion
of arbitrary apps are outside its scope. Private editions and backups are
unencrypted files. Public hosting contains only an empty reader and explicitly
synthetic sample data.

## Native Duo section to finalize after the real run

Replace this section with the actual issue, session, repair diff, and failed /
passed pipeline links. State exactly which actions Duo performed. Keep the
deterministic checks and owner approval distinct from agent decisions. Do not
change the description above to past tense until the linked evidence supports
it. Reuse one candidate/MR and retain the total repair-attempt count.

## 2:45 recording outline

Use only synthetic accounts. Keep tokens and private local files outside the
recording. Show the commit/run identity and label cuts that compress the real
Duo wait. The narration below is conditional on the corresponding footage.

| Time | Footage | Narration draft |
|---|---|---|
| 0:00–0:20 | Notebook and the software will | “When a service ends, the work people created should still be useful. The Last Release is a notebook that tests that promise before its server retires.” |
| 0:20–0:40 | Alice/Bob synthetic notes, then will.json | “Each person keeps their own active notes. They must be able to search, edit, save a backup, and restore it without the original server.” |
| 0:40–1:10 | Actual failing GitLab pipeline, Duo session and repair diff — pending | “This synthetic exporter includes another account's notes. The independent check blocks it. Here is the real Duo session repairing that account filter and updating the same candidate.” |
| 1:10–1:35 | Actual passing GitLab pipeline, exact candidate report and fixture approval — pending | “The candidate passes its checks in Chromium and Firefox. The report identifies the exact source, snapshot and artifacts. Only this tested outcome can receive retirement approval.” |
| 1:35–2:15 | Stop the disposable original server, fresh offline file, edit, download backup, fresh restore | “The original fixture server has stopped. This edition still searches and edits notes. I download a backup, open a fresh reader, and restore the edit.” |
| 2:15–2:45 | Final measured report, public repo/reader links and limits | “For this final run, the report shows [actual note count] notes across [actual account count] accounts, [actual HTTP attempts] offline network attempts, and a preserved database. This is a prototype for one plain-text notebook. The public repository contains the checks and reproduction steps.” |

Use the final run's measured values in the last shot, rather than reusing the
historical GitHub counts. Narration is about 200 words plus the final measured
values, leaving time for visible interactions within the 165-second outline.
The final video must be shorter than three minutes and publicly visible on
YouTube under the [official rules](https://gitlab-transcend.devpost.com/rules).

## Ready now and required before submission

The app, fault patch, automated checks, and historical GitHub reports are ready.
The owner has reported onboarding is still pending. If the access request has
not been submitted, use [contributor onboarding](https://contributors.gitlab.com/transcend-hackathon/).
If it has been submitted, the [organizer resources](https://gitlab-transcend.devpost.com/resources)
describe approval as about 24 business hours and automatic project provisioning.

After access arrives, follow [DUO.md](DUO.md): confirm sponsor coverage, import
the source, pass GitLab CI, register/enable the flow, complete a capability smoke
test and real repair, publish the public reader, and record the final video.
Submit only after replacing all pending evidence fields. No entry, flow,
onboarding request, or video has been submitted by this preparation.
