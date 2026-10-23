## Verdict
Do not park on this: the reported behavior is the fail-closed reading of an ambiguous spec, the "obvious" fix opens a real evasion hole, and no legitimate workflow reaches the scenario — record it as a spec-ambiguity item with one added test at the next gate.

## The case against
1. The scenario is not a legitimate reorganisation. `plugin/evals/run.py:142-151` skips any
   case folder whose name starts with `.`, so a rename of a case file into
   `evals/cases/.foo/` moves it into a folder the eval runner refuses to read. Intent.md
   names that exact maneuver ("moving it to a folder name that starts with a dot hides it
   from the eval runner with no deletion in the diff") as the trick the ratchet exists to
   catch. Reporting `evals/cases/foo/` there is an over-broad *label* for a real hiding
   event, not an invented finding.
2. The proposed fix is worse than the bug. `dropped = (dot_dropped | touched) - survivor_cases`
   makes the hit vanish entirely as soon as one visible path survives under `foo/` — a sibling
   left behind, or a `README.md` added in the same commit. The current code's failure mode is
   noise the owner clears in one label (`sdlc:accept-risk`, decision 24, or a plan
   declaration); the fix's failure mode is silence in the one check written to stop an agent
   lowering the bar. For a ratchet, that asymmetry decides it.
3. The spec does not settle it. Requirements state the dot rule flatly ("an `R` whose
   destination folder name starts with `.` is a drop", spec.md:22-23) and the survivor rule
   flatly ("A case is dropped when no path remains", :25-27); they collide only in this
   intersection, which no Acceptance bullet enumerates. The code picks one reading; the
   reviewer picks the other. That is an open design question for the owner, not a proven
   contradiction of a settled invariant — and "no test" for an intersection the spec never
   specified is a spec gap, not a weakened or missing proof (no pre-existing test was touched).
4. Blast radius is theoretical. A dot-prefixed destination *inside* `evals/cases/` is created
   by no tool, template or convention in this repository; the hit is per case, visible in
   `details.hits`, and parks rather than breaking anything.

What I would decide instead: keep the fail-closed behavior, and require only that the next
round (a) adds `test_ratchets_eval_case_dot_rename_with_surviving_sibling_is_a_drop` pinning
the chosen semantics and (b) adds one spec.md sentence saying the dot rule overrides the
survivor rule. What would make me accept escalation: a documented legitimate use of a
dot-prefixed folder under `evals/cases/` (shared fixtures, disabled variants), or the owner
stating the survivor-emptiness invariant is absolute — then the survivor filter is right and
the hiding case must instead be reported per file, not dropped from the check.
