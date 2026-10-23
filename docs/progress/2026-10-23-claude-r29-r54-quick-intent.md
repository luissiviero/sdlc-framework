# Progress — R29 part 1 with R54: the intent home's examples and mock, the quick intent, plugin 1.0.28 (2026-10-23)

This session ran on branch `claude/r29-r54-quick-intent`, from `main` at `d72de6a` (#344, plugin 1.0.27), as lane B of wave 2 of the parallel build sessions the owner started on 2026-10-23 ("start wave 2"). Lane A builds R61 with R33 at the same time and merges first (ROADMAP's Order column). The scope is R29's part 1 (`docs/proposals/intent-home.md`, the first two rows of its "Order" table) and R54 (`docs/proposals/speed-beyond-the-sprint.md`, "R54, the quick intent"), with choice 239's item on R54's row. This PR changes `plugin/` and `template/`, so it bumps the patch; it took 1.0.28, the number `python tasks.py next-free` gave on `d72de6a` (read at the session's start, nothing taken above `main`). It takes no choice, note or decision number.

## What was built
**R29 part 1.**
1. **Examples/References.** The `intent-template` skill gains `## Examples/References` after Open questions and before the incident-only Evidence, where the owner puts examples of what is wanted and references (a link, or a file in the change folder named by its path); "none" is a valid answer. The gate does not require it: `INTENT_SECTIONS` is unchanged and the heading is a constant of its own (`artifacts.INTENT_EXAMPLES_SECTION`), so changes in flight and the detection's incident intents never park on it (the proposal's settle row, recommended).
2. **The build's rule.** The template and `/sdlc-build` step 4 say that the build matches the owner's mock, never a screen the Examples/References only refer to.
3. **The mock question.** `/sdlc-plan` step 1 asks "Do you have a mock or example screens?" when the change touches a screen; a mock goes into `mock/`, examples into Examples/References, and no mock never blocks. `template/changes/README.md` says `mock/` may now come with the intent.
4. **The `Mock:` line.** `spec-template` and `/sdlc-design`: a change that touches a screen ends Acceptance with `Mock: mock/<file>` or `Mock: none, screens follow the UX conventions`. The gate does not check it (the proposal's settle row, recommended): only the design pass knows whether a screen is touched.

**R54, the quick intent.**
5. **`/sdlc-plan`'s quick route.** When the owner asks for a quick intent, or the argument starts with `quick:`, the command takes the owner's one paragraph, asks nothing more (except the change type when the paragraph does not make it plain), writes the quick intent's shape and skips step 4's correction loop.
6. **The quick intent's shape** (`intent-template`, "Quick intent"): a header line `Quick intent: yes`, the paragraph in Problem, and the fixed line `Left to the design run (quick intent).` as the body of the four other article sections. Every section is present and not empty, so `check_artifacts` holds the intent as it is.
7. **Where the design run's fill goes.** The proposal says the design run "fills the rest of the intent template". An accepted `intent.md` may not change after gate (a): `check_guardrails` parks a branch that changes it, and on the fast lane that is read since the owner's intent PR head (`plugin/gate/checks.py`). So the design run writes what it assumed into `spec.md`, in a section of its own, `## Assumed from the quick intent`, before Requirements: one item per section the owner left, plus any other assumption the design rests on. These are assumptions, not flagged concerns, so they cost no panel call; a gap no reasonable reading fills stays a concern.
8. **Gate (b) requires the section** for a quick intent (`check_artifacts`, a few lines local to the spec's block; `artifacts.is_quick_intent` reads the header line only). The adversarial reviewer's first angle asks whether each assumption follows from the paragraph and whether the design rests on one the list omits.
9. **"What I assumed (N)"** heads the design PR and the build PR (`pr/description.assumed_block`), above "Decisions taken for you": on the fast lane a routine design PR is superseded within minutes, so the build PR at gate (e) carries the list too. A review comment on a line corrects it. At (a), the quick intent's bullets say the sections are left to the design run instead of quoting the marker as an open question; the release note and `release/notes.py` never print the marker as the outcome (the title stands in).

**Choice 239's line.**
10. **The intent PR's "What needs you".** The description is written before the PR exists and cannot know who opens it. A PR `upsert` does not open as a draft now reads: opened from the owner's own account and not as a draft, nothing (opening it accepted the intent and started the design, which closes the PR as `sdlc:superseded`; corrections go to the design PR, or the build PR at gate (e)); opened as a draft or by another account, the gate (a) line as before. `upsert --draft` keeps the gate (a) line alone, since a draft never takes the fast lane (`run_phase.intent_pr_start`). No runner code changed.

## Not built, and why
- **R29's later parts:** the template override per project (after the live check, with or after R27), the claude.ai route and its connector check (after R17; the allocation shared with R31), the gate (a) briefs (R28), the names (R45). Their rows in the proposal's "Order" table are unchanged.
- **The quick intent from claude.ai or the phone:** that is the claude.ai route above; R54 runs through `/sdlc-plan` until it exists.
- **The intent PR's line rewritten after the PR opens** (reading the author and the draft flag back and editing the body): it would need the owner check in `pr/cli.py` and a second write for one line; the two-case line is true whichever way the PR was opened. Recorded as a choice the owner may revisit.

## Known limits, recorded
- **A wrongly assumed change type** (feature or fix) is set at allocation in `status.yaml`, which the design run does not change; the quick route asks for it when the paragraph does not make it plain, and the design PR lists it among the assumptions.
- **The fast lane's classification is unchanged for a quick intent:** a routine plan from a one-paragraph intent goes to the build without the owner, and the owner reads the assumptions at gate (e) (R54's own words: "there or at gate (e)").
- **Not verified live:** a quick intent on the sample. It needs the sample's pin to move past 1.0.28.

## The owner's choices
None taken in this session.

## Proposed edits for the owner
None: no guardrail file needs a change for this PR.

## Port list (HANDOFF.md, "Rules for every session")
This PR touches neither `plugin/ci/run_phase.py` nor `plugin/detect/` nor the detect, runbook and fix workflow templates, so it is not on the port list.

## The fresh-context review
Pending at the time of writing; its findings and their fixes are added below once it reports.
