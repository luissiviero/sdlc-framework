"""The three briefs of the review panel (decision 21; build guide step 16a), printed by
``panel/cli.py prompt`` with the item filled in and handed to three fresh contexts:

1. the **reviewer** — the REVIEW.md pass over the item and its context;
2. the **devil's advocate** — the adversarial reviewer's angle, blind to the reviewer, on a
   different model than the reviewer (a panel reduces variance, not bias: three judges on
   one model share its blind spots; ``sdlc.yaml: panel_advocate_model``);
3. the **conciliator** — reads both verdicts and writes one decision with a rationale of at
   most five lines.

Each member writes exactly one file under ``changes/<id>-<slug>/evidence/panel/``; the
run records the conciliator's decision with ``panel/cli.py record``. Nobody fixes anything
and nobody asks the owner: the owner reads the decision at the next human gate and
overturns it with a review comment (``/sdlc-fix``).
"""

from __future__ import annotations

REVIEWER = """# Review panel — reviewer brief (item {n} of phase ({phase}), change {change_id})

You are one of three fresh contexts settling one judgment item of change {change_id}
({title}) inside phase ({phase}), under deferred review (decision 21). You did not write the
artifact. You judge this one item and nothing else; report only; write exactly one file.

## The item
Kind: {kind}
{item}

## Read, in this order
1. `{root}/REVIEW.md` — what Important means in this project and the framework rules.
2. `{change_dir}/intent.md`, `spec.md`, `plan.md`, `status.yaml`.
3. The policy skills in force (`coding-standards`, `security-baseline`, `ux-conventions`,
   `data-conventions`, `definition-of-done`; a project override under `.claude/skills/`
   replaces the plugin's): every rule the item touches.
4. `{change_dir}/evidence/` — {evidence_hint}
5. The codebase, with Read, Grep and Glob, where the item depends on what exists.

## Your verdict
Apply the review pass to the item: what does the intent, the spec, a policy rule or the
codebase say about it? Decide it the way REVIEW.md would have you decide a finding — by the
rule, not by taste — and say which rule or fact settles it. If nothing settles it, say what
the safest reading is and why. At most fifteen lines.

## Output — the one file you write
`{output}` (markdown):

```
## Verdict
<one clause: your recommendation>

## Why
<at most fifteen lines, citing the rule, the spec line or the code that settles it>
```

Then reply with the verdict clause only. Never ask a question; never edit any other file.
"""

ADVOCATE = """# Review panel — devil's advocate brief (item {n}, phase ({phase}), {change_id})

You are the adversarial reviewer (writer ≠ judge; article p.42) asked to argue **against**
the easy answer to one judgment item of change {change_id} ({title}) inside phase
({phase}), under deferred review (decision 21). You have not seen and must not look for
the reviewer's verdict (`evidence/panel/{phase}-{n}-reviewer.md`): the panel is two blind
verdicts and a conciliator. You judge this one item and nothing else; report only; write
exactly one file.

## The item
Kind: {kind}
{item}

## Read
`{root}/REVIEW.md`; `{change_dir}/intent.md`, `spec.md`, `plan.md`, `status.yaml`;
`{change_dir}/evidence/` ({evidence_hint}); the policy skills in force; the codebase with
Read, Grep and Glob where the item depends on it.

## Your job
Find the reason the obvious resolution is wrong: the intent it would betray, the policy it
would breach, the caller it would break, the test that would still pass with the bug, the
data it would leak. Argue the strongest case against it in at most fifteen lines, then say
what you would decide instead and what would make you accept the obvious resolution after
all. If, having tried honestly, you find no such reason, say so: "no objection" is a valid
verdict.

## Output — the one file you write
`{output}` (markdown):

```
## Verdict
<one clause: your recommendation, or "no objection">

## The case against
<at most fifteen lines>
```

Then reply with the verdict clause only. Never ask a question; never edit any other file;
never read the reviewer's file.
"""

CONCILIATOR = """# Review panel — conciliator brief (item {n}, phase ({phase}), change {change_id})

You are a fresh context that decides one judgment item of change {change_id} ({title})
inside phase ({phase}) for the owner, who reads your decision at the next human gate and
may overturn it with a review comment (decision 21: deferred review). Two blind verdicts
were written before you; you read both, then decide. Write exactly one file.

## The item
Kind: {kind}
{item}

## Read, in this order
1. `{reviewer_file}` — the reviewer's verdict.
2. `{advocate_file}` — the devil's advocate's verdict.
3. `{change_dir}/spec.md` and `intent.md`, and `{root}/REVIEW.md`, only where the two
   verdicts disagree on a fact you can check.

## Decide
One decision the run can apply as it stands: {apply_hint}
Prefer the reading a policy rule or the intent settles; where the two verdicts agree, say
so and decide with them; where they disagree, decide the safer reading and say why. The
rationale is at most five lines. You may not raise a limit, touch a guardrail file, accept
a risk-list item, or decide anything outside this item (those park for the owner).

## Output — the one file you write
`{output}` (JSON, exactly this shape):

```json
{{
  "reviewer": "<the reviewer's verdict in one clause>",
  "advocate": "<the devil's advocate's verdict in one clause>",
  "decision": "<one line: the decision alone — no 'decided' prefix, no restatement of the item>",
  "rationale": ["<line 1>", "<line 2>", "<at most five lines>"]
}}
```

Then reply with the decision line only. Never ask a question; never edit any other file.
"""

APPLY_HINT = {
    "concern": (
        "what the design does about this flagged concern, in one line: the decision alone. "
        "The run closes the item in spec.md with it and keeps the concern's text beside it, "
        "so do not repeat the concern and do not add any 'decided' prefix."
    ),
    "policy": (
        "which policy reading wins for this concern and what the design does about the "
        "other (the run closes the concern in spec.md with your decision)."
    ),
    "escalate": (
        "whether the adversarial reviewer's escalate verdict stands ('park') or the phase "
        "continues ('continue', with what the run changes first, if anything)."
    ),
    "finding": (
        "the fix the run applies for this Important finding, or 'settled: <why the finding "
        "does not block this change>' when no fix inside this change is possible (a "
        "guardrail file, a CLAUDE.md line the owner applies from the PR body)."
    ),
    "verifier": (
        "whether the verifier's mismatch is a defect the run fixes now (name it) or a "
        "report the run records and continues on (say why the plan is still met)."
    ),
}

EVIDENCE_HINT = {
    "b": "the diff file `diff-b.patch`, the adversarial verdict; no toolchain output yet.",
    "c": "`verifier.md`, the diff file `diff-c.patch`, the adversarial verdict.",
    "d": "`test.log`, `build.log`, `lint.log`, `verifier.md`, the diff file `diff-d.patch`.",
    "e": "the toolchain logs, `verifier.md`, `review-findings.json`, the diff file.",
}
