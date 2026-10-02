# The playbook and the framework compared (2026-09-28)

The owner asked two questions. Does this repository do what its workflow page says it does? And does the page that draws the article's workflow match the article? Once both pages were corrected, a third question followed: at each step, which of the two workflows has the better solution? This page records how the pages were checked, what was wrong, the defects found in the framework on the way, and the step-by-step comparison (the crosswalk) that the owner fills in. Everything here was read-only work except the two corrected pages, the crosswalk page and the five issues below.

The files next to this page, in `2026-09-28-playbook-vs-framework/`:

| File | What it is |
|---|---|
| `crosswalk.json` | The 48 decision points as data: the article's version with its pages, the framework's with its files, the relation, the decision behind any difference, the question to weigh, and the map data (who does each step, and which steps are human decisions); since 2026-09-30 also the owner's tentative target for the rows `target-design.md` touches (`target`, `targets`). This is the source of truth for the crosswalk. |
| `crosswalk.html` | A snapshot of the crosswalk page (cards with a third "Target (tentative)" column, and a side-by-side map). Opened from the repository it is read-only; the owner's choices are saved only on the claude.ai page. |
| `playbook-workflow.html` | A snapshot of the corrected page that draws the article's workflow. |
| `framework-workflow.html` | A snapshot of the corrected page that draws this framework's workflow at 0.2.27. |
| `target-workflow.html` | A snapshot of the third workflow page, beside the other two: the workflow as the owner wants it, drawn only from what `target-design.md` has discussed (T1–T7), all tentative. |
| `target-design.md` | What the owner wants the framework to become, one entry per idea (T1, T2, …), tentative until the whole study is done; nothing in it changes the current version. |
| `naming.md` | Every naming difference between the article and the framework, 23 rows, each judged on the name alone with its reason; summarized as T4 in `target-design.md`. |
| `evidence-article.md`, `evidence-framework.md`, `evidence-source.md` | The verified findings behind sections 3 and 4: each finding with its page and quote, or its file and line, and the findings that were refuted. |

The live pages, private to the owner: the playbook page (https://claude.ai/artifact/WhLTjcSzJqQmUFm3aP5G6L), the framework page (https://claude.ai/artifact/KW8jWunfLNa9WgBSzJxw4S), the target workflow page (https://claude.ai/artifact/13X8rzF9KsfekmeSs1w5rM) and the crosswalk (https://claude.ai/artifact/PFnRZ32pwTr4y422Gna2mz).

## 1. Sources

- **The article**: "The AI-native SDLC playbook" (Louis Claxton, 21 August 2026), read as the 53-page print in `docs/reference/ai-native-sdlc-playbook.pdf` (printed 2026-09-02), with its four figures (p.3, p.5, p.8, p.49) extracted at full resolution. Page numbers everywhere are print pages.
- **The live page** (https://claude.com/blog/the-ai-native-sdlc-playbook), fetched on 2026-09-28 and compared sentence by sentence with the print. The text is the same apart from three things: a new "Prefer a PDF? … Download the PDF" box at the top, the title now written "AI-native", and a reading-time figure that the page computes in the browser. The four figures sit in the same places (`evidence-source.md`).
- **Not read**: the "designv2" PDF the live page now links to (uploaded 2026-09-28), and the live page's images. Both are served from `cdn.prod.website-files.com`, which the session's network policy denied. The figures were taken from the print instead. Whether the new PDF uses the same page numbers is unknown.
- **The framework**: this repository at f2a2b29 (plugin 0.2.26) for the first pass and at cf3f696 and 11551ef (plugin 0.2.27) for everything after (plugin 0.2.28, which landed next, changes none of the 47 rows the crosswalk then had); `docs/DECISIONS.md`, `OPERATING_MODEL.md`, `BUILD_GUIDE.md`, `ROADMAP.md` and `NOTES.md` as the documents, the code as the ground truth.
- **The sample project** (`luissiviero/sdlc-sample-python`): the changes 0000 to 0008, their evidence folders, the pull requests and the Actions runs, read-only, as evidence of what really happens.

## 2. Method

The same shape as the readiness review, with every pass read-only:

1. **Twelve slice audits.** Six on the playbook page against the article (source integrity; the whole loop; the PR review loop and the build session; the maintain loop and headless mode; the adoption graph, the roles table and the "left open" list; coverage) and six on the framework page against the code (setup, plan and design; build, test, deploy and release; maintain; gate outcomes and the phase run; coverage and drift since 0.2.19; the sample project's real runs). Each claim got a verdict with a quote and page, or a file and line.
2. **Two adversarial verifiers**, one per page, which re-derived every non-matching finding from the source and tried to refute it. They settled the contradictions between audits and re-rated severities. Their reports are the three evidence files.
3. **Spot checks by the main session** of every finding rated high, before anything was reported: the p.8 graph arrow by arrow, the runbook authorizations in `template/bands.yaml`, `check_approval` in `run_phase.py`, the parked-change guard and the release filter.
4. **One reviewer per corrected page**, before each was published: 5 corrections on the playbook page, 9 on the framework page (one of them a regression the rewrite had introduced).
5. **The crosswalk**: 40 rows seeded from the corrected pages, checked row by row (17 corrections), then 7 rows added for the decision points no row covered (drafted with evidence, then checked: 6 corrected). The map data (who does each step, which steps are decisions) was checked on its own (29 corrections). On 2026-09-30 the owner asked for a 48th row, the adoption order (`setup-adopt`), which no row covered; it was drafted against the article and plugin 0.2.28 on `main` (dd308ca) and checked by an independent reviewer before it was published.

The session's own errors, caught by these passes, are recorded so they are not repeated: the design-mock row first said the framework had no mock step, but `changes/<id>-<slug>/mock/` exists since 0.2.19; issue #71 first said a re-run overwrites its phase's result file, which is true only before 0.2.16 (corrected in the issue); the first decision count read 17 against 12, which double-counted gate (b) and missed several owner labels (15 against 15 once corrected).

## 3. The playbook page against the article

**Verdict: faithful.** No step is invented and no quote is wrong; every page cite is right except two. The p.8 adoption graph is redrawn exactly (13 arrows, the same two dotted). No finding was rated high once verified.

What the correction changed (7 medium findings, the notable low ones; `evidence-article.md` has all 37 and the 12 refuted):
- The headless diagram now places the service owner's triage and the product owner's review before the stages (p.9, p.44), not at the end.
- The two edges from the 2σ and 3σ tiers to `intent.md` are drawn the same way and say the article does not name the tier, as the page's own gap 4 already did.
- Gaps 3, 5, 7, 9 and 10 are narrowed to what the article really leaves open (for example, at 3σ the agent triggers the pre-approved rollback itself, p.43 and p.45; what stays open is whether the production-gate hook exempts a rollback, p.41).
- Added from the article: the change-ticket and "ask" hooks (p.35-37); who approves configuration changes (the policy owner for skills, p.22; code owners for CLAUDE.md, p.20); the Claude Design front-end route (p.12-13); how a headless run is wired (p.43-44).
- Smaller: gates now sit inside their stage boxes, human reviews are hexagons, the conditional @claude edges are dashed, the verifier leads to "report done", and "on-call … approves" was narrowed to the service owner (p.44).

## 4. The framework page against the code

**Verdict: right on the main path, wrong on two edges.** The page was a snapshot of plugin 0.2.19; the corrected page describes 0.2.27 as the code behaves, and its notes say where `OPERATING_MODEL.md` differs.

The two findings rated high (`evidence-framework.md`, H1 and H2):
- **The runbooks behind `sdlc:go`.** The page had the owner's Go running `quarantine-flaky-test` and `revert-pr`. Both are `preapproved` in `template/bands.yaml` and run from the detect job with no person, each opening its own PR; only `go` routes (the template's `rollback-deploy`, and any rehearsal's runbook) wait for `sdlc:go`.
- **Merging a parked PR.** The page had "merge or approval label → the next phase starts" from a parked PR. At (b) the next workflow's guard skips a parked change (`run_phase.py`, `if st.parked_reason`) in a green job; at (c) or (d) the release skips because the phase is not e; at (e) the merge still releases.

The medium findings, all corrected on the page: the owner's one-time GitHub steps after the 0000 merge (Actions allowed to open PRs, the Claude secret, the "Restrict updates" ruleset, a CI workflow for the metric); scan findings never go through `/sdlc-maintain` (a template intent, no diagnosis run); closing an incident PR with a comment only opens a dismissal PR, which the owner must merge; an infrastructure failure ends the job red, it does not park; phase (e) has the REVIEW.md pass, not the adversarial verdict; the guard and the hand-over are the CI runner's steps; `deploy.command` runs only when `deploy.action` is not `none` and a command is set, both off by default; the legend now says Setup and (a) run under the owner's account.

## 5. Framework defects found on the way (filed)

| Issue | Defect |
|---|---|
| #66 | The release runs for any merged PR from `sdlc/<id>/c` at phase e with no "already released" record. Phase e is set before the review, so a merge during (e) releases unreviewed code, and the second build PR the (e) run then opens releases again. Seen on the sample (#17 and #19; both release runs reached the action step). |
| #67 | Merging a PR that touches only `changes/0000-sdlc-init/` starts a design run for change 0000 once the Claude secret exists; nothing exempts the installation change. This repository's own change 0000 is exposed. |
| #68 | A parked build PR merged at (e) releases, whatever the park reason (a risk-list hit included), and the reason is not shown again. |
| #71 | `gate.max_budget_usd` is documented per change but compared with the last session's cost: `start-run` resets the figure and `record-spend` overwrites it. On the sample's change 0002 the cap would have compared 4.86 USD against at least 19.06 USD spent. |
| #72 | The docs call the stored `--output-format json` result a transcript; it holds the final message and run metadata, not the conversation. |

Where the documents and the code disagree and no issue was filed (`evidence-framework.md`, section 2): the Full profile's "approving review + label" (only the label and its actor are checked, `run_phase.py` `check_approval`); `OPERATING_MODEL.md` §3 saying an infrastructure failure parks (§7 of the same file agrees with the code); §4 listing a scan finding as an input of `/sdlc-maintain`; the closing of an incident PR described as dismissing without conditions; `template/evals/README.md` saying a plugin-version change runs the evals (`sdlc-evals.yml` does not trigger on it; fixed in 0.2.28, whose README says a pin bump is evaluated after its merge); the design guard also accepting phase f; and the "read-only planning run" being a restricted pass inside the same session.

## 6. The crosswalk

48 decision points, one row each (Setup 4, Plan 3, Design 5, Build 9, Test 5, Deploy 8, Maintain 7, across stages 7). Relation: 13 same, 29 adapted, 2 added, 2 missing, 2 diverges.

**Where the framework differs from the article with no decision behind it** (9 rows; the place to look first):
- the adoption order (a project starts with the whole loop; D1, D17 and D19 touch it, none decides it);
- a ticket becoming `intent.md` (alerts are covered by D15 and D16, tickets by nothing);
- the front-end mock (build guide step 34, a convention only);
- who writes the policy skills (owner sources and trigger tests);
- tuning the reviewer (sub-step 26.5, recorded as not built);
- judgment steps in CI (the article's three example jobs);
- Claude on call in a channel (build guide step 40, optional and not built);
- measuring the plays (build guide step 42 computes two counters);
- the audit trail (the OpenTelemetry export, deferred by step 41).

Two rows ask a question that reopens a settled decision, and say so: "What starts implementation" (D11, non-routine plans) and "Acting at 3σ" (D26, the rehearsed rollback with no Go).

**Where a person decides.** The map counts the human decisions on each side, per stage. A decision "every change needs" is counted separately from one that happens only in some cases (a Full-profile label, a declared production, an exception label); a human act that another row already counts is drawn but not counted.

| Stage | Playbook | Framework |
|---|---|---|
| Setup (once per project) | 3 | 2 |
| Plan | 1 | 1 |
| Design | 2 | 2 |
| Build | 3 + 1 | 1 + 1 |
| Test | 0 | 0 + 3 |
| Deploy | 2 | 1 + 1 |
| Maintain | 3 | 1 + 1 |
| Across stages | 0 + 1 | 0 + 1 |
| **Total** | **14 + 2** | **8 + 7** |

(The second number counts decisions that happen only in some cases.) The playbook has 16 decision points and the framework 15. The playbook makes 14 of them on every change (Setup's three once per project; the third, added by the owner's call of 2026-10-02, is the organization's choice of which stages to transform first, p.7); the framework makes 8 (Setup's two once per project), and its other 7 are conditional: the Full profile's two approval labels, the release label on a declared production, and the exception labels (accept-risk, unlock-tests, reset-iterations, the Go for an unrehearsed rollback). The largest gaps are Build (the plan approval folded into gate (b) by D2; no counterpart to the policy owner's sign-off on skills) and Maintain (the scan triage folded into gate (f)). The chart counts decision points, not people: the playbook spreads them over about ten roles, and the framework gives all of them to one owner. That collapse is the one structural difference behind many rows ("Who the humans are").

## 7. Open

- **The owner's decisions (as of 2026-10-02).** For each row the owner marks which workflow is better and what to do: keep the framework's, adopt the playbook's, blend, change both, or park for later. The choices live in the crosswalk page's store; at the end of a session they are copied into `crosswalk.json` (`decision` on each row, `owner` for the weights). "Copy decisions as Markdown" on the page exports them. Every choice is tentative until the whole study is done.
  - Criteria weights (saved 2026-09-29): safety 1, owner attention 3, autonomy 3, auditability 2, cost 0, fidelity to the article 2. The owner works alone, looks in once or twice a day, runs tools and experiments, wants to reconstruct decisions months later, does not mind spend, treats the article as the reference to justify departures from, and wants to hand over as much as possible.
  - Decided (saved 2026-09-30; setup-adopt, the three Plan rows and design-trigger 2026-10-02):

    | Row | Better | Decision | Target |
    |---|---|---|---|
    | setup-home | framework | blend | T3 |
    | setup-gates | framework | blend | T1 |
    | setup-merge | framework | blend | T1 |
    | x-roles | (none) | park for later: "Direction in T1 (target-design.md); not settled." | T1 |
    | setup-adopt | framework | blend: the whole loop stays the default; added, nothing replaced: an optional by-hand start without the Claude secret, and the change-0000 intent lists what starts empty | T5 |
    | plan-idea | playbook | blend: `/sdlc-plan` stays; added: writing the intent from claude.ai (as a PR, never a commit to main) and the role-fed interview | T2, T3 |
    | plan-ticket | playbook | blend: alerts and `/sdlc-plan` stay; added: the owner's label on a GitHub issue starts a run that opens the intent PR (only the owner's label counts; the issue text is data) | T6 |
    | plan-accept | playbook | blend: merge to accept and close to reject stay; added: the owner's closing comment is saved as the change's reason; T1's briefs before gate (a) as recorded | T1, T7 |
    | design-trigger | both | keep: the merge starts the design run (the article's end state); no second interview before the spec; issue #67 stays a defect | T2 |

  - Still open: 39 rows. Next in order: the rest of Design (design-spec, design-mock, design-concerns, design-go), then Build.
- **The target design.** What the owner wants the framework to become is collected in `target-design.md`: T1 (AI roles that advise, and one manager that reviews for the owner, with the approvals, the gates, how they communicate and where transcripts go), T2 (the interview), T3 (the intent home), T4 (names, from `naming.md`, recorded by a parallel session on 2026-09-30), T5 (starting a project, from setup-adopt, 2026-10-02), T6 (tickets become intents, from plan-ticket, 2026-10-02) and T7 (a rejection keeps its reason, from plan-accept, 2026-10-02). All seven are tentative; T5 to T7, like T4, are drawn on the target workflow page only. The crosswalk page shows T1 to T3 in a third column, "Target (tentative)", on the 20 rows they touch, and `crosswalk.json` carries the same text (`target`, `targets`). T4 is deliberately not on the crosswalk, although it names ten of its rows (setup-home, plan-idea, build-plan, build-skills, test-evals, maintain-triage, maintain-scan, maintain-act, deploy-release, x-roles). It was added on 2026-09-30 and taken off again the same day (9d9a983 reverts 6ad93e5), because the owner did not want the crosswalk changed and asked for the target work to go into a separate workflow page instead. That page is the target workflow page (`target-workflow.html`, https://claude.ai/artifact/13X8rzF9KsfekmeSs1w5rM), which draws T1 to T7. The crosswalk's Target column keeps T1 to T3 and is not extended unless the owner asks.
- **Row corrections found on 2026-09-29 and 2026-09-30, applied on 2026-10-02.** The seven rows of the 2026-09-29 session were re-checked against `main` (dd308ca, plugin 0.2.28): the framework side is unchanged since 0.2.27 and no row is wrong, but these precision fixes were due. On 2026-10-02 they were re-checked against plugin 0.2.29 (904f4ec), checked by an independent reviewer (whose fixes were taken, among them three maps the notes had not named), and applied in `crosswalk.json`, the page and the snapshot together:
  - setup-home: the `intent-template` skill ships in the plugin, so the article's lead sign-off has no per-project act; "who can write to it" is D4's ruleset; p.10 itself recommends an `intent/` folder in the product repo for a single product.
  - setup-gates: the managed-settings layer is optional and on the owner's machine only (`sdlc-init.md` §6), never read by a cloud session; the review mode the map names is D21, which `why` should cite beside D18; the risk list is a template default that `/sdlc-init` does not ask about.
  - setup-merge: branch-only write access for the automation identity holds only once the owner has created the ruleset by hand (the framework never creates it; the daily digest warns while it is missing); with the owner's *Exempt* bypass the rules, "Require a pull request" included, do not run for the owner.
  - plan-idea: the framework text and the map leave out the owner's correction step (`sdlc-plan.md` step 4).
  - plan-ticket: `fwSrc` should add `plugin/commands/sdlc-maintain.md`, which writes the detect-path intent; no workflow triggers on issues.
  - plan-accept: a rejection reason is recorded only for incidents (the last member comment becomes the dismissal reason); for an idea or a ticket, `status.yaml: abandoned_reason` holds a fixed string ("pull request N closed without a merge") on the change's branches.
  - x-roles: `OPERATING_MODEL.md` §2 names seven roles (not the policy owners, the platform engineer or the security lead); separation of duties is rebuilt from three things (writer ≠ judge, the automation identity, branch rules), not only owner against automation identity; the policy-owner role is empty rather than held (the five policy skills say "no owner source yet").
  - setup-adopt (a counting call; the row itself was decided the same day, see "Decided"), made by the owner on 2026-10-02: the playbook side counts the organization's choice of which stages to transform first ("organizations may choose to prioritize transforming different stages at different times", p.7) as a once-per-project decision, which moves the playbook's total in section 6 from 13 + 2 to 14 + 2.
  - The page header now names plugin 0.2.29 (904f4ec); 0.2.28 changes none of the older rows, and 0.2.29 changes only how a park message names its failed step.
- **Where the decisions go.** The owner confirms changes only once the whole study is done (said on 2026-09-30). Until then every change the owner wants is collected, tentative, in `target-design.md`, and nothing goes to `docs/ROADMAP.md`. After the study, a confirmed change to the framework becomes a candidate in `docs/ROADMAP.md` with its proposal; one that changes a settled decision is proposed there, never edited into `docs/DECISIONS.md` directly. The table in section 6 and `crosswalk.json` are updated in the same pull request as any change that moves a row.
- **The two issues found by the crosswalk** (#71, #72) and the three found by the audit (#66, #67, #68) are open.
- **The designv2 PDF** is unread; if it becomes the reference, the page numbers in the three pages and in `crosswalk.json` need a check.

## 8. How to continue this study in a new session

A session that should work on this study, and only on it, can be started with:

> Work only on the playbook-versus-framework workflow study. Start by reading `docs/reviews/2026-09-28-playbook-vs-framework.md` and its folder: `crosswalk.json` is the source of truth for the 48 rows, and the four `.html` files are snapshots of the claude.ai pages (the crosswalk https://claude.ai/artifact/PFnRZ32pwTr4y422Gna2mz, the playbook page https://claude.ai/artifact/WhLTjcSzJqQmUFm3aP5G6L, the framework page https://claude.ai/artifact/KW8jWunfLNa9WgBSzJxw4S, the target workflow page https://claude.ai/artifact/13X8rzF9KsfekmeSs1w5rM). My saved choices are in the crosswalk page's store (copied into `crosswalk.json` at the end of each session); read them before anything else, then `target-design.md`, where the changes I want are collected, tentative until the whole study is done. Stay inside this scope: the two workflow pages, the crosswalk and its map, this review and its folder (`target-design.md` included), and issues #66, #67, #68, #71 and #72; nothing goes to `docs/ROADMAP.md` before the study ends. Do not change plugin or template code, `docs/DECISIONS.md`, or the guardrail files; if a step needs one of those, say so and stop. Check every claim against the article (`docs/reference/`, print pages) or the code on the current `main`, and have an independent reviewer check any change to a page or to `crosswalk.json` before it is published or committed. Keep the snapshots, `crosswalk.json` and the live pages in step. Today I want to: …

Replace the last sentence with the task: decide a stage together, re-check the rows after a plugin release, turn confirmed decisions into ROADMAP proposals once the study is done, and so on. Where the study stands is section 7, which lists the next rows to decide. The way of working that the owner settled into on 2026-09-29/30, for each row:
- re-check the row against the current `main` and say whether the framework side changed;
- show both sides, the decision behind the difference, and what the weights favor;
- when the owner asks, give a table with the current framework, the playbook, a suggested blend and why, so the owner can approve it;
- save the owner's answer to the page's store and read it back;
- record any change the owner wants in `target-design.md` (a new entry or an existing one), then show it on the target workflow page, with an independent review before publishing; the crosswalk's Target column is extended only if the owner asks (section 7).
