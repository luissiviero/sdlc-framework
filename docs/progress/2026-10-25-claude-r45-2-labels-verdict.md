# Progress — R45's second rename PR: the triage queue's labels, the verdict `park` and the explain step (2026-10-25, plugin 1.0.44)

This session ran on branch `claude/r45-2-labels-verdict`, built on R45's first rename PR (#389, merged as `0ce7f6b`, plugin 1.0.43, tagged `v1.0.43`), with `main` merged in by a merge commit. It is section 12's PR 2 of `docs/reviews/2026-10-20-names-against-the-article.md`, as decision 39's point 4 amends it (row 62 with N17's "Verdict"), with row N32 of `docs/reviews/2026-10-25-names-added-since-decision-39.md`. Plugin **1.0.44** (`python tasks.py next-free` after `git fetch origin` on `0ce7f6b`). No numbered choice, note or decision is taken.

## What was built
1. **The triage queue's labels carry the prefix** (rows 37 and 38): `incident` is `sdlc:triage` and `schedule` is `sdlc:schedule` (`conventions.TRIAGE_LABEL`, `SCHEDULE_LABEL`); the old ones are read for one release (`TRIAGE_LABELS`, `SCHEDULE_LABELS`). The two code changes the row asks for beyond the rename:
   - **The gate-label sweep** keeps both (`pr/cli.py OWNER_LABELS`), and an upsert at maintain labels the PR `sdlc:triage` and takes off an older plugin's `incident`;
   - **The digest's filter** reads "carries `sdlc:triage` (or `incident`) and no gate label" (`digest.gate_labels`, every `sdlc:` label but the queue's two), and the queue counts only gate labels, so a runbook PR is listed once, under "Maintain: runbook and dismissal PRs — `sdlc:triage`" (row 67's label part), never also as waiting at a gate.
   The detect and runbook steps label their PRs `sdlc:triage`; the commands, `template/changes/README.md`, the scan workflow's comment and `docs/OPERATING_MODEL.md` follow.
2. **The verdict is `continue | park`** (row 62): one reader, `gate/artifacts.verdict_word`, reads an older verdict file's `escalate` as `park` for one release; the panel's item kind and key prefix follow (`ledger.normalize` reads `escalate:<hash>` lines as `park:<hash>`, the hash covering only the reasons); the reviewer's brief field "Word" is "Verdict" (N17), a brief with "Word" read for one release (`risk.parse_brief`). Every instruction to a model (the adversarial reviewer, the panel briefs, the deploy review prompt, the commands) asks for `park`. The gate's own results `continue | wait | park` are unchanged.
3. **The explain step** (N32): `run_phase.py --phase explain` and `plugin/ci/explain.py` (was `--phase triage`, `ci/triage.py`), `explain=park|red` on `$GITHUB_OUTPUT` beside the old `triage=` line for one release, `.sdlc-cache/explain/`, `$RUNNER_TEMP/sdlc-explain.json`, `evidence/claude-explain[-n].json` (a `claude-triage*.json` still counts as the explain run), the commit `explain(<id>): the run's logs read`, the park block's "**Explanation (model-written)**", the gate record's and failed-run record's key `explanation` (the old key read for one release), and the six workflow templates' step names and id `explain_checkout`. `--phase triage` still runs the step for one release. Every other "triage", the owner's at the maintain gate, stays.
4. **The decisions it renames, annotated** (decision 39, "What it amends"; choice 126): decision 21 (the panel's `escalate` item), 25 (the two labels) and 35 (the brief's field and words), each beside its sentence.

## How it was built
This session built the labels; two sub-agents built the verdict and the explain step in parallel on disjoint files, and this session merged `main`, bumped the version, regenerated `plugin/init/template_hashes.json` and ran the suite. Tests that asserted the old names now assert the new ones; none was deleted or skipped; each part added tests that the old names are still read.

## The fresh-context review
<!-- filled in after the review -->

## Carried from #389
The owner checked both rulesets on `main` (the central session's message of 2026-10-25, 20:39 UTC; not re-verified here): neither requires a status check, so the check runs' new names (`sdlc/build`, `sdlc/deploy`) block nothing.

## Port list
This PR touches `plugin/ci/run_phase.py`, `plugin/detect/` and the detect and fix workflow templates: it goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
For this repository's pin-move PR (letters and the old labels keep working until the sixth PR, so none is urgent): none of `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` names `incident`, `schedule`, `escalate` or the triage step (checked with `grep` on `0ce7f6b`). The sample's guardrail lines are read at its own pin-move PR.

## What the owner does
| When | Act |
|---|---|
| Now | Write and commit the seven workflow copies (design, build, test, deploy, fix, detect, scan) on `claude/r45-2-labels-verdict` with `python tasks.py workflow-copies` (the PR body's commands), then merge the PR when `Framework checks` is green on its final head. |
