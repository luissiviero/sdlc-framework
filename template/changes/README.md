# changes/ — one folder per change

Convention (OPERATING_MODEL section 8; decision 10): `changes/<id>-<slug>/` where `<id>` is a
four-digit sequence (`0000` is the framework's own installation) and `<slug>` is the
kebab-case title.

| File | Written in | By |
|---|---|---|
| `intent.md` | (a) plan | `/sdlc-plan`, with the owner (article p.10–11 template) |
| `spec.md` | (b) design | `/sdlc-design` (B3) |
| `plan.md` | (b) design, read-only run | `/sdlc-design` (B3); kept in sync in (c) by the plan-sync hook |
| `evidence/` | (d) test | the test run (B3) |
| `status.yaml` | every phase | `plugin/state` — phase, profile override, change type, gate result, parked reason, iteration count |

Branches: `sdlc/<id>/a` (intent PR), `sdlc/<id>/b` (spec+plan PR), `sdlc/<id>/c` (build PR,
kept open through test and review). Labels: `sdlc:<phase>-ready` (waiting at a human gate),
`sdlc:<phase>-approved` (Full profile, gates c and d), `sdlc:needs-human` (parked).

Nothing here is edited by hand except `intent.md` during phase (a). The repo is the source
of truth; an external tracker holds only the issue number ↔ commit SHA link (decision 9), the
issue number goes into `status.yaml: external_ref`.
