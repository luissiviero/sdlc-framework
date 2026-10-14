## Verdict
Escalate on reason 1 only, reworded: reasons 2 and 3 do not hold, and reason 1 is a design
ambiguity (not just a missing test) the owner must settle at (b).

## The case against
1. Reason 2 is contradicted by plan.md itself. "Files that change" lists the test inventory
   as "the test-file drop rule (D, R-not-a-rename, R-is-a-rename)" (plan.md:39) and the third
   Risk bullet commits to parser tests "including a rename whose destination also matches a
   `test_paths` glob (not a drop) and one whose destination does not (a drop)"
   (plan.md:120-122). The R-that-is-a-drop behavior is planned and proofed; only a test *id*
   is missing from the Proof index. Parking the owner to look for a hole the plan fills is
   the kind of false positive the gate's own history warns about.
2. Reason 3 misreads the design. spec.md Design:149-153 fixes the scan as "a simple anchored
   substring/regex check per line" over the diff's added `+` lines, "scoped to the
   file-glob/filename list in Requirements" — there is no toml/json per-format parsing to
   test; the config surface is one filename list. Requirements:65 also fixes the scan as
   never changing `ok`/fail. The worst a bug there can do is shorten an advisory list: no
   behavior broken, no data leaked, no policy breached — a nit by REVIEW.md's own definition
   of Important, and REVIEW.md caps nits rather than parking on them.
3. Reason 1 survives and is worse than stated, which is why I still escalate. spec.md reuses
   `plan_sync.is_planned` for declaration; that helper's directory rule is
   `changed.startswith(planned)` (plugin/hooks/plan_sync.py:133-136), so a plan listing
   `evals/cases/foo/` matches a deleted *file* under it but never the *case path*
   `evals/cases/foo` that the hit reports — and spec.md never says whether declaration is
   tested per deleted file or per case path (nor which path declares a dot-rename drop).
   Both readings sit in the text, they disagree, and no Proof item forces a choice.
4. What I would decide: approve (b) with one narrowed finding — spec.md must say which path
   the eval-case declaration is matched on, and plan.md must add the two missing eval Proof
   ids (declared via "Files that change", declared via `- ratchet: evals`). I would accept
   the obvious resolution (park on all three) only if the design claimed per-format config
   parsing, or if plan.md's test inventory did not already name the R-is-a-drop case.
