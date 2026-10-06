# Native GitLab Duo integration and submission evidence

Target: Life After Code 2026, Start Fresh / Supervised, Most Creative.
Deadline: **27 October 2026, 13:00 UTC / 18:30 IST**.

## Status

The native flow is versioned and follows GitLab's documented v1 schema.
It has **not been registered or executed in a provisioned GitLab project**.
Chromium, Firefox, contracts, and the complete disposable rehearsal passed on
the merged GitHub build; see [VALIDATION.md](VALIDATION.md). GitLab CI/Pages
still require their first actual run. Record URLs below only after they exist;
never label local scripts or GitHub Actions as a Duo session.

## Provision and smoke-test

Owner update, 6 October 2026: onboarding is still pending. The
[submission and recording draft](SUBMISSION-DRAFT.md) is ready for completion
after the sponsor project and real execution evidence are available.

1. Join [the hackathon](https://gitlab-transcend.devpost.com/) and complete
   [contributor onboarding](https://contributors.gitlab.com/transcend-hackathon/).
   Use the sponsor-provisioned GitLab project; import the new GitHub source
   or push it there. Keep the submission public, with the MIT license.
2. Check group roles, Duo availability, hosted runners, namespace credits,
   and paid/on-demand spend controls. Triggered flows bill the service account
   at namespace level; included human credits are not assumed to cover them.
   Confirm sponsor coverage before running any flow. Stop at free allowances.
3. Merge the reviewed `agent-config.yml` onto the default branch. Confirm its
   setup finds Python and Node and installs the pinned test dependency/browsers.
   The default GitLab executor/sandbox is preserved. A missing prerequisite
   must fail setup, rather than lead to a simulated check.
4. Go to **AI → Flows → New flow**. Paste `last-release.yml` into the
   configuration editor; use the platform's actual validator. Create and
   enable it in the project. Enable **Mention** only for the initial smoke test.
5. Open a synthetic test issue using the **Last_Release_Repair** description
   template. State sponsor coverage, original trusted-base
   SHA, candidate branch/MR, and previous repair-attempt count. Mention the
   actual assigned service-account username. It is intentionally not hardcoded.
6. Confirm a real session can read the issue and checkout, edit allowed files,
   run checks, commit with Duo attribution, and open/update an MR. Record its
   session URL, flow version, MR, pipeline, and setup errors. Fix executor
   issues before attempting the recorded repair demonstration.

Human mentions start sessions. Bot comments do not recursively trigger
another flow. Do not add paid APIs, a tunnel to localhost, or broad automatic
triggers. Two repairs total per candidate are flow policy; record the count
on the issue across sessions. The owner also reviews the history. The final
local gate independently checks protected files and pinned tests; prompt
instructions alone are not an authorization boundary.

## Creative failure → repair demonstration

Use a clearly labelled **synthetic-only demo branch**, never real note data.
The [foreign-export.patch](foreign-export.patch) is a one-line fault fixture,
not a change to the working exporter. It was applied to a disposable checkout:
the existing exact-export check failed with six records instead of three per
account. The working merged exporter still passes all 14 contracts.

After importing/reviewing the complete source in the sponsor project and
passing its baseline pipeline, create the candidate from that reviewed main:

```sh
git switch main
git pull --ff-only
trusted=$(git rev-parse HEAD)
git switch -c demo/synthetic-foreign-export
git apply docs/foreign-export.patch
git diff -- release.py
git add release.py
git commit -s -m "Synthetic-only demo: make private export fail ownership checks"
python tests/contracts.py Contracts.test_exact_exports_and_fault_injection
```

The last command must fail with `Privacy or preservation failed: missing,
altered, deleted, or foreign notes.` Keep that failure as the demo evidence.
Push this candidate only to the sponsored
GitLab project, open one draft repair MR labelled **SYNTHETIC ONLY — DO NOT
MERGE UNREPAIRED**, and record its failing GitLab pipeline and `$trusted`
in the issue template. Confirm free sponsor coverage before mentioning Duo.
Do not merge the fault into the default branch or use it with an owner's DB.

Make the exporter include all active accounts' notes by removing its owner
predicate inside `export_for`. The independent snapshot check must reject
the foreign canary even if the exporter writes a matching manifest checksum.

Mention Duo on that issue with the failing pipeline and the reviewed baseline.
The configured flow maps the will, establishes the failure, fixes the owner
predicate, reruns contracts/browsers, and creates one repair MR. Keep its
genuine code diff and failed-before/passed-after history. Reuse the MR, and
stop after two repair attempts. Agent edits to controls, the will, or tests
need owner review and a new baseline rather than silent acceptance.

Run the pinned owner-side verification against the frozen final notebook.
Only then review the concrete report and approve its exact digest. The
disposable rehearsal can automatically approve its fixture; real retirement
always uses the owner's explicit local command. The workflow cannot reach
or stop an owner's localhost from hosted GitLab.

The GitLab browser job also runs the full disposable rehearsal using HEAD
and both browser engines. It retains only the synthetic report, browser
report, and retirement receipt. This build smoke test does not approve a
repair's changed controls; use the original owner-reviewed SHA for the
separate pinned verification. The package job waits for both verification
jobs before creating the two-file public reader.

## Evidence register

| Evidence | Status/reference |
|---|---|
| Public canonical GitLab repository | Pending provisioning/import |
| Sponsor credit/compute coverage | Pending owner check |
| Actual flow version and platform validation | Pending |
| Capability smoke-test session and MR | Pending |
| Deliberate failing synthetic pipeline | Pending |
| Duo-created repair diff/session | Pending |
| Passing GitLab pipeline and cross-browser drill | Pending |
| Frozen manifest/report digest and retirement receipt | Produced by local rehearsal; retain the final run |
| Public Pages reader/sample | Prepared by CI; deployment pending |
| Public YouTube demo under three minutes | Pending recording |

Video story: **promise → foreign-note failure → Duo repair → passing exact
candidate → owner approval → server stops → offline edit and fresh restore**.
Show traceable run/build references and label time cuts. Do not imply a
local report establishes a successful AI run, delivery to real people, or
all-app conversion. Keep submitted links and artifacts stable during judging.

## Primary references checked 6 October 2026

- [Official rules](https://gitlab-transcend.devpost.com/rules)
- [Resources and access](https://gitlab-transcend.devpost.com/resources)
- [Custom flows: create and enable](https://docs.gitlab.com/user/duo_agent_platform/flows/custom/)
- [Custom-flow schema and restricted fields](https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/)
- [Flow Registry v1, prompts and tools](https://docs.gitlab.com/user/duo_agent_platform/flows/claude-edit-v1-flow-registry/)
- [Runner execution and default-branch configuration](https://docs.gitlab.com/user/duo_agent_platform/flows/execution/)
- [Agent configuration keys](https://docs.gitlab.com/user/duo_agent_platform/flows/execution/agent-config-yaml/)
- [Triggers and service-account credit attribution](https://docs.gitlab.com/user/duo_agent_platform/triggers/)

The contribution is a tested offline successor to this specific notebook.
Software archives and offline applications are prior art; do not claim global
originality or a guaranteed award.
