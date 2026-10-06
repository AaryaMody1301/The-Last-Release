# Build-plan check — 6 October 2026

Checked the saved `The-Last-Release-Build-Plan.md` against merged GitHub commit
`d52a76c09a2629fa6cb5360d71fc3f4daa36ebd8`, its source, and the genuine
[main verification run](https://github.com/AaryaMody1301/The-Last-Release/actions/runs/37489071487).
The application follows the intended design. All twelve requirements have
not passed together yet: R07 is pending and R11 is only partly demonstrated.

| ID | Plan promise | Current implementation/proof | Status |
|---|---|---|---|
| R01 | Private account access | Owner-scoped routes; invalid-token and cross-account contracts | Passed |
| R02 | Persistent live CRUD | SQLite notebook; CRUD/restart/deletion contracts | Passed |
| R03 | Supported software will | Exact supported will validation; unsupported promise blocks before freeze | Passed |
| R04 | Complete private edition | Independent SQL/payload comparison; foreign/missing/altered/deleted canaries | Passed |
| R05 | Useful offline notebook | Real downloads, stopped fixture server, fresh offline contexts, CRUD/search | Passed in Chromium and Firefox |
| R06 | Save and restore edits | JSON download and import into another fresh context; invalid imports preserve work | Passed in Chromium and Firefox |
| R07 | Native Duo preparation/repair | Flow/executor config and issue template committed; no real session yet | Pending |
| R08 | Check-derived outcome report | Candidate report/manifest includes counts, identity, unsupported behavior and failures | Passed for synthetic candidate |
| R09 | Exact-outcome owner gate | Pinned controls/tests, DB verification ledger, rejected stale/forged approvals | Passed for disposable fixture |
| R10 | Preserve data and recover | Atomic packaging, preserved DB, reversible freeze, self-stop only | Passed for disposable fixture |
| R11 | Free public reproduction | Hosted development reproduction and two-file package pass; canonical GitLab and Pages unpublished | Partial |
| R12 | Usable keyboard/save controls | Labels, focus style, Tab path, explicit saving and unload warnings | Automated checks passed |

The main rehearsal preserved six active notes across two synthetic accounts
with zero offline HTTP(S) attempts. Its database survived and its original
fixture port closed. Exact reports/digests are in [VALIDATION.md](VALIDATION.md).
These facts establish the deterministic prototype, not a native AI run.

## Deliberate differences from the proposed file map

- `web/notebook.html` is shared by live and offline editions instead of two
  separate templates. It keeps behavior consistent and follows Ponytail.
- GitHub is the development repository requested by the owner. The final
  canonical submission still needs the public sponsor-provisioned GitLab repo.
- CLI arguments use the implemented `--root`, `--db`, `--out`, `--trusted-ref`
  and `--approve` contract. The original plan allowed these details to settle
  during implementation.
- Added a DB readiness ledger and trusted-baseline gate to stop a forged
  report or an agent-modified check from authorizing retirement.

Runtime remains Python standard library/SQLite with zero runtime packages,
one plain HTML UI, and one pinned browser-test development dependency. The
capacity limits, unsupported features, public/private boundary, owner-run
retirement, and ₹0 budget are retained.

## Next gate: the Oct 7–8 GitLab/Duo access milestone

1. Confirm Devpost/contributor onboarding and find the provisioned GitLab
   project. The organizer provisions the group/project after approval; this
   account's approval status has not been established.
2. Import the reviewed source while preserving existing sponsor history and
   the welcome issue. Make the final source/MIT license public and run the
   baseline GitLab pipeline. Use a normal push or MR; never force-push over
   an initialized sponsor repository.
3. Confirm free Duo service-account credit coverage, runner allowance, roles,
   and paid-spend controls. No flow has been triggered or paid resource enabled.
4. Validate/register the existing flow in AI → Flows, enable one human Mention
   trigger, and complete the capability smoke test.
5. Apply [foreign-export.patch](foreign-export.patch) only on a labelled
   synthetic candidate branch. The existing independent contract must fail.
   Let actual Duo repair that one candidate/MR, then retain the real failed and
   passed GitLab pipelines/session/diff. Two repair attempts total.
6. Run final pinned verification, publish only the public reader/sample to
   Pages, record the 2:45 demo, and fill the submission evidence register.

[DUO.md](DUO.md) contains the fault command and the actual evidence fields.
Documentation/config changes in this follow-up PR need owner review before
its merged revision becomes a new trusted baseline. The repair branch must
use that original reviewed baseline, not its own modified controls.

## Official requirements rechecked

The [official rules](https://gitlab-transcend.devpost.com/rules) still require
a project using GitLab Duo Agent Platform, a public MIT GitLab repository
with visible pipeline history, and a public YouTube demonstration shorter
than three minutes. Submission closes **27 October 2026 at 13:00 UTC /
18:30 IST**. Path A/Supervised and the Most Creative target remain appropriate.

[Resources](https://gitlab-transcend.devpost.com/resources) direct entrants
through contributor onboarding; provisioning is described as about 24
business hours. Current [custom-flow docs](https://docs.gitlab.com/user/duo_agent_platform/flows/custom/)
separate creation, enabling and triggers. YAML in Git alone is insufficient.
The [schema](https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/)
and [executor config](https://docs.gitlab.com/user/duo_agent_platform/flows/execution/agent-config-yaml/)
match the documented fields; actual sponsor-platform validation is pending.
[Trigger credit attribution](https://docs.gitlab.com/user/duo_agent_platform/triggers/)
is to the namespace service account, so personal included credits do not
establish sponsored coverage.

No additional product feature is needed before this external integration
gate. The remaining work is native execution, public delivery, and recorded
proof for the already implemented promises.
