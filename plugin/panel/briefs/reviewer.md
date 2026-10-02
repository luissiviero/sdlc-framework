# Review panel — reviewer brief (item {n} of phase ({phase}), change {change_id})

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
