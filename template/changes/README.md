# changes/ — one folder per change

Convention (OPERATING_MODEL section 8; decision 10): `changes/<id>-<slug>/` where `<id>` is a
four-digit sequence (`0000` is the framework's own installation) and `<slug>` is the
kebab-case title.

| File | Written in | By |
|---|---|---|
| `intent.md` | (a) plan | `/sdlc-plan`, with the owner (article p.10–11 template) |
| `spec.md` | (b) design | `/sdlc-design` (B3) |
| `plan.md` | (b) design, read-only run | `/sdlc-design` (B3); kept in sync in (c) by the plan-sync hook |
| `evidence/` | (c), (d), (e) | `verifier.md` (verifier agent), `test.log` · `build.log` · `lint.log` · screenshots (the test run, B3), `adversarial-review-<phase>.json` (adversarial reviewer), `review-findings.json` (review pass, B3), `gate-<phase>.json` and `run-<phase>.json` (the gate) |
| `status.yaml` | every phase | `plugin/state` — phase (or `abandoned`: the PR was closed without a merge), profile override, change type, gate result, parked reason, iteration count, the actors of the owner's un-park labels and of the runbook Go |
| `evidence/detection.json`, `evidence/proposal.json`, `evidence/runbook-<name>.json` | (f) maintain | the detection script (the finding: metric, tier, rule, the numbers), the diagnosis (`/sdlc-maintain`: the proposed route) and the dispatcher (what the runbook did); an incident change is filed by the detection script with `entry_route: incident` and stays at phase `f` until its intent PR is merged (= gate (a)) |
| `mock/` | (b) design, optional | the exported design mock for front-end work (build guide step 34): the visual target phases (c) and (d) compare screenshots against; project content, committed with the spec |

Branches: `sdlc/<id>/a` (intent PR), `sdlc/<id>/b` (spec+plan PR), `sdlc/<id>/c` (build PR,
kept open through test and review). Labels: `sdlc:<phase>-ready` (waiting at a human gate),
`sdlc:<phase>-approved` (Full profile, gates c and d), `sdlc:release-approved` (the release
approval on a declared production), `sdlc:needs-human` (parked); the owner's un-park verbs
`sdlc:accept-risk`, `sdlc:reset-iterations`, `sdlc:unlock-tests` (read and removed by the
next fix round). A "Request changes" review on any of these PRs starts a fix round; closing
one without merging abandons the change. Phase (f): an incident intent PR (head
`sdlc/<id>/a`, title `maintain(<id>): …`) carries `sdlc:f-ready` and `incident`; the owner's
triage is the gate (merge = fix now, label `schedule` = later, close with a comment =
dismiss, recorded in `changes/.dismissed.json` through a dismissal PR); `sdlc:go` on it runs
the runbook the diagnosis proposed when its route needs a person (read and removed once).
The post-mortem of a shipped incident fix lives in `lessons/` and its eval in `evals/cases/`.

Nothing here is edited by hand except `intent.md` during phase (a). The repo is the source
of truth; an external tracker holds only the issue number ↔ commit SHA link (decision 9), the
issue number goes into `status.yaml: external_ref`.
