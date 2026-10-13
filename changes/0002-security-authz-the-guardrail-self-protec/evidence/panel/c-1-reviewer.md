## Verdict
Escalate.

## Why
Read directly at this HEAD: `_part_targets`'s git branch (`plugin/hooks/shell_guard.py:370-376`)
takes `sub = words[1].lower()` with no `_nonflag` pass, unlike every other branch in the same
function; `_inner_shell_command` (lines 235-238) matches only the exact adjacent pair
`(words[0], words[1])`. Both are traceably defeated by a fully literal command
(`git -c x=y rm CLAUDE.md`, `bash --norc -c 'echo x > CLAUDE.md'`) that trips no non-literal
token, so the fail-closed rule never engages, and both commands are allowed bare by
`plugin/ci/settings.ci.json` (`Bash(git *)`).

REVIEW.md's Security pass covers "authentication gaps," and intent.md exists solely to close
"an unattended phase session can overwrite CLAUDE.md... bypassing the guardrail-file
protection" — this is that exact class, on a path-less, fully literal command, through the
exact tool route (Bash with an allow-listed program) this change's Requirements/Design commit
to covering (`git rm`, `bash -c` are both named as covered idioms in spec.md Design).

It is not covered by plan.md's accepted residuals: those name an *unlisted* wrapper, a
non-literal/decoded path, or a pathspec-less git verb (`reset --hard`, `merge`) — a different
shape from a documented idiom whose argument position shifts by one flag. `fix-requests.json`
(`requests: []`, `not_applied: []`) and verifier.md's scope ("re-verification of... commit
3a90bd0" only) confirm this round fixed only the third, unrelated finding from the same prior
adversarial review and left these two open — missed, not weighed and accepted. Per REVIEW.md,
this is Important (breaches the policy the change is the vehicle for) and must escalate, not
pass.
