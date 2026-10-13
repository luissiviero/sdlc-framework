## Verdict
Do not park on this: downgrade it to a build-phase instruction (a survivor-set argument plus one missing acceptance test), because the "unimplementable design" claim rests on reading a testability sentence as an interface contract and on one consequence that cannot occur.

## The case against
1. The premise is a misreading. "One small pure function taking the parsed records ... so it is
   unit-testable without git" is a testability statement, not a signature. `drop_rule(records,
   survivors)` is still one small pure function, still unit-testable without git — the caller
   passes the survivor set in. Nothing in spec.md's Design or plan.md step 2 forbids a second
   parameter; step 2 only says the test input is a fixture, "not live git".
2. The survivor source is already the codebase's idiom and already in scope. Every diff-reading
   check calls `diffmod.committed_files(ctx.root, ctx.diff.merge_base, ctx.diff.head)`
   (`plugin/gate/checks.py:614, 663, 746, 940`), so the HEAD ref is at hand in `GateContext`; a
   `tree_files(root, ref, prefix)` built on `_git(root, "ls-tree", "-r", "--name-only", ref, "--",
   prefix)` is argument-list only (security-baseline rules 2 and 6, like `file_at`/`_cat_ok`) and
   lands in `plugin/gate/diff.py`, a file plan.md's "## Files that change" already lists. No spec
   amendment, and no `plan_sync`/`design_scope` finding: those checks match paths, not prose.
3. Half the stated consequence is factually wrong. "Under-detect real drops spread across several
   commits" cannot happen: the source is `git diff --name-status -M <merge base>...HEAD`, a
   three-dot diff over the whole branch, so a case deleted across three commits shows three `D`
   records. An escalation the owner must read twice should not carry an impossibility as evidence.
4. What survives is narrower than the verdict: a partial delete (one file of a multi-file case, the
   rest untouched) is a real false-positive risk, but it is a missing acceptance test, not a broken
   design. spec.md's Acceptance pins the emptied folder and the internal move; neither forces the
   survivor read. Escalating the whole design buries that one actionable item.
5. Cost: a park here returns 0005 to design over a sentence the build phase resolves in its own
   step 2, with intent, requirements and blast radius untouched.

What I would decide instead: continue phase (b) with two build-phase conditions written into the
item — the drop rule takes the survivor listing as an argument, read at `ctx.diff.head` through a
new `diff.py` argument-list helper (no `shell=True`, same ref the records came from, never the
working tree); and spec.md Acceptance / plan.md Proof gain one case:
`test_ratchets_eval_case_partial_delete_is_not_a_drop`.

What would make me accept the escalation: if plan.md or spec.md pinned `drop_rule`'s signature to
records only, or declared `diff.py` closed to anything but the `--name-status` parser, or if the
survivor read had no committed ref to stand on (`ctx.diff.head` absent at these gates) — then the
requirement really would be unsatisfiable by the prescribed design and the owner would have to
choose.
