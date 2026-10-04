# Progress — 2026-10-02, outside the session plan: the review panel's two blind verdicts enforced; plugin 0.2.30

## Summary
- **Why.** The owner's playbook-versus-framework study parks the crosswalk row x-roles on T1 (AI roles that write briefs, `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`), and T1 builds the roles on the panel's pattern. Reading the panel's code for it showed that the two blind verdicts were asked for, not enforced. The owner asked to close that with what exists before any role is built; no decision is reopened (decision 21 is the same panel).
- **Seven items, a test each.** (1) `panel/cli.py record` refuses an item whose reviewer or advocate file is missing or has no `## Verdict`, before a panel call is counted. (2) The ledger carries the two verdicts from those files, not the conciliator's restatement, and the item's number (`item_n`). (3) The gate's `panel` check requires both files in HEAD for every line with an `item_n`. (4) The `panel_blind` hook (PreToolUse on Read and Grep) refuses a Read of one blind verdict while the other is missing, and a Grep that would search it; a Grep over another folder or limited to code passes (the owner chose this over blocking every whole-repository Grep, logging only, or detecting afterwards). (5) A CI run that added panel decisions parks when no model in its `modelUsage` is `panel_advocate_model`. (6) A session already on that model is a warning in the PR summary, not a park (the owner's choice). (7) "Decisions taken for you" names the run's models.
- **Changed from the plan shown to the owner.** No new eval case for the hook: case 0005 already proves `hooks.json` loads, and a deterministic test proves the registration. The blindness rule applies to every caller, not only the advocate, so it needs no agent name and covers a reversed order.
- **Two gaps closed in the same PR, at the owner's request.** (a) The hook also refuses a Bash or PowerShell command that names a one-sided verdict or the panel folder (the main session could otherwise `cat` the reviewer's verdict into the advocate's prompt). (b) The advocate's model is proved per call, in CI and by hand: when the advocate writes its verdict, the hook reads that sub-agent's own transcript and writes `<phase>-<n>-advocate.model.json` (who wrote it, on which model); `record` and the gate require it to name the devil's advocate on `panel_advocate_model`, and only the hook may write it. The transcript layout is observed on 2.1.287, not documented: NOTES §25 asks the next CI panel run (2.1.278) to confirm it, and a different layout parks the item rather than passing it. The run-level check stays as a second net.
- **What stays open.** A shell command that reads a verdict without naming it or the panel folder (`grep -r half-up .`); a shell command forging a `.model.json`. Both are recorded in the hook's docstring.
- Docs: NOTES §25 (the hook-input quote, the `modelUsage` evidence from the sample, the hook's cost); OPERATING_MODEL §3 and the decision-21 row; README's hook list.

## Guardrail lines for the owner (after `v0.2.30` exists; this session cannot edit these files)
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sdlc.yaml](../sdlc.yaml) | line 98 | `  version: 0.2.29` | `  version: 0.2.30` |
| the sample, `sdlc.yaml` | line 77 | `  version: 0.2.29` | `  version: 0.2.30` |

---
