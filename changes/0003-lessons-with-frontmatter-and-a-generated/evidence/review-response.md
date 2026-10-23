# Review response — change 0003, phase (e) fix round

Source: `evidence/review-findings.json` at HEAD `00ddfc7e177c2bdb289e0ec10fbf7fca9e9824e5`
(`review/cli.py validate`'s recorded output). Review mode is `parked` (not `deferred`), so
there is no panel to settle an Important finding this round; this file is that case's
documented alternative (/sdlc-fix step 3: "a finding you believe wrong ... is not fixed
silently ... the owner decides at the gate").

## The 4 Important findings
All four are the framework's second-occurrence rule (REVIEW.md "Framework rules": "The
second occurrence of the same finding across reviews produces a one-line entry in
`CLAUDE.md` ..., proposed in the review for the owner") firing on four pre-existing nits:
the duplicate lazy `lessons.index` import in `plugin/gate/checks.py`, unescaped `]`/`(` in
`plugin/lessons/index.py`'s generated markdown links, `build()`'s `mkdir` side effect on a
read-only `check()`, and `template/lessons/README.md`'s `sources` example missing a sample
`run-<n>` entry. Three of the four are items the owner's own PR #132 review already named
and explicitly marked "can wait for the tag (0.3.7); include or drop" (the `mkdir` one is
the owner's item 7 verbatim).

The "second occurrence" count reached 2 only because this round's own plan.md-sync mistake
(see `fix-response.md`) forced two extra review re-runs on the same otherwise-unchanged
code; each re-run re-reported the same pre-existing nits, mechanically crossing the
recurrence threshold inside this one round rather than across genuinely separate historical
rounds. The remedy the framework rule actually asks for — proposing the one-line
`CLAUDE.md` entry so the owner can apply it — is satisfied: `review/cli.py validate` wrote
the four proposals into `evidence/review-findings.json`'s `proposals`, and `pr/cli.py
upsert` carries them into the PR's "Proposed CLAUDE.md lines" block. Editing `CLAUDE.md`
itself is the one fix this run cannot make (protected path); per /sdlc-fix step 3, that is
answered here, not applied. The underlying code nits are not fixed in this round: three are
the owner's own explicit "can wait" items, and expanding scope to include the fourth
(the import duplication) alone, beyond what either the owner or this round's intent asked
for, would be the scope creep /sdlc-fix step 3 warns against. The owner's review comment on
this finding (or a fix in a future round once `sdlc:reset-iterations` reopens iterations)
is what's needed.

## The 1 nit
`plugin/gate/checks.py:1598` — a non-string `status` reported as "missing" rather than
naming the type: doubt stated by the reviewer itself, no test or spec line calls for a
different message. Not applied; the owner reads it in the PR.

## Verdict and gate
See `evidence/gate-e.json` for this round's final check (parked on both `findings`, per the
above, and `limits` — see `fix-response.md`'s "Iteration cap" note for that one).
