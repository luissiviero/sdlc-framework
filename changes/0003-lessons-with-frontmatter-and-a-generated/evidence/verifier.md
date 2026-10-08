# Verifier report — change 0003, phase (e) fix round, HEAD `00ddfc7e177c2bdb289e0ec10fbf7fca9e9824e5`

## Commands run

This is a CI session (`SDLC_GATE_COMMANDS=runner`), so per the verifier's brief the build/test/lint
targets were not run here. Read instead, not run:

- `changes/0003-lessons-with-frontmatter-and-a-generated/evidence/gate-d.json` (the record of
  phase (d), the phase before this one — phase (e)'s own record is an earlier round's and is
  not judged here). Its `commands` check:
  - `ok: true`, `"reason": "build, test and lint exit 0"`, `"details.ran_by": "runner"`
  - build: `python -m compileall -q plugin tests tasks.py` → exit 0, output `""`
  - test: `python -m pytest` → exit 0, tail `"1429 passed in 282.13s (0:04:42)\n"`
  - lint: `python -m ruff check .` → exit 0, output `"All checks passed!\n"`
- `evidence/build.log`, `evidence/test.log`, `evidence/lint.log`: each file's first line reads
  `# python -m <target> — deferred to the runner — 2026-10-08T06:39:40Z`. This is not a
  failure — this round's session wrote these placeholder files minutes ago and the runner
  will replace them after this session; read, not run.
- `gate-e.json` present (own phase, `result: park`, an earlier round's `findings.ok: false`)
  is this phase's own earlier-round record and is not judged here either.

By-hand: build/test/lint were not invoked in this session (correctly withheld per the CI rule).

## Behavior exercised

A throwaway script (deleted after use) imported `plugin/gate/checks.py`'s
`_supersedes_problem` and `plugin/lessons/index.py`'s `build`/`check` directly and called
them with the inputs this round's fix targets:

1. **`_supersedes_problem`** (`plugin/gate/checks.py:1612`), called directly with a
   `lessons_dir` and `fm["supersedes"]` set to:
   - `/etc/passwd` (absolute) → `"2026-01-caller.md: supersedes must name a lesson file in lessons/"`
   - `../secrets.md` (climbs outside `lessons/`) → same message
   - `2026-01-self.md` (self-reference, lesson named the same) → same message
   - `2026-01-other.md` (well-shaped but nonexistent, a control) →
     `"...supersedes target '2026-01-other.md' does not exist"` (different, correct code path)
   - An absolute path to a real file containing `"TOP-SECRET-CONTENT..."` and unparsable YAML
     → same `"must name a lesson file in lessons/"` message; checked programmatically that
     neither `"TOP-SECRET"` nor `"secret.md"` appear in the result — no leak of the target's
     content or path.

2. **`plugin/lessons/index.py` `build`/`check`**, called directly on a temp `lessons/` with
   three malformed files plus a `README.md` (which must stay excluded):
   - `stale_after: 2027` (int, wrong type)
   - `detected.at: "2026-13-01"` (month 13, out of range)
   - a file written as raw non-UTF-8 bytes (`\xff\xfe\x00...`)
   - Result: `build()` did not raise; notes returned were
     `"...bad-month.md: detected.at '2026-13-01' is not a date"`,
     `"...bad-stale-type.md: stale_after 2027 is not a date"`,
     `"...not-utf8.md: 'utf-8' codec can't decode byte 0xff..."`; generated text placed all
     three under `## Unsorted`, `README.md` excluded. Writing that text to `lessons/index.md`
     and calling `check()` returned `ok=True` (no false drift).
   - Control case: a well-shaped lesson (`detected.at: "2026-01-05"`, string `stale_after`
     absent) built cleanly into a normal `## flaky-test` heading line, not `## Unsorted` —
     confirming the bad-shape detection does not over-fire.

3. **`plugin/commands/sdlc-maintain.md` step 1** — read directly (not executable, so read is
   the correct exercise): confirmed the text now reads *"open only the lessons whose heading
   or `Tags:` clause names this finding's metric or the rule that fired, plus every lesson
   under `## Retired`, plus every lesson under `## Unsorted`..."*.

`DATE_SHAPE_RE` and `_SUPERSEDES_NAME_RE` were also sanity-checked by hand against a handful
of valid/invalid date and filename shapes; both match the spec's stated regex.

## Mismatches with plan.md / spec.md

None found. Specifically:
- spec.md's "fails with one line that never repeats the target file's own content or parser
  error" (Requirements, PR #132 note) — confirmed by direct test.
- spec.md's "`detected.at` or `stale_after` value that is present but not a date-shaped
  string ... go to `## Unsorted`" and "a file that is not valid UTF-8 ... go to `## Unsorted`"
  — confirmed, no crash.
- plan.md's `sdlc-maintain.md` step 1 update (now also opens `## Unsorted`) — confirmed
  present in the file text.

## Verdict

`matches the plan`

Relevant files:
- `plugin/gate/checks.py` (`_supersedes_problem` at line 1612)
- `plugin/lessons/index.py` (`_bad_field_shapes` line 107, `_read_text` line 124, `build`/`check`
  lines 277/287)
- `plugin/commands/sdlc-maintain.md` (step 1)
- `changes/0003-lessons-with-frontmatter-and-a-generated/plan.md`, `spec.md`
- `changes/0003-lessons-with-frontmatter-and-a-generated/evidence/gate-d.json` (previous-phase
  record, read)
- `changes/0003-lessons-with-frontmatter-and-a-generated/evidence/{build,test,lint}.log`
  (deferred-to-runner placeholders, read)
