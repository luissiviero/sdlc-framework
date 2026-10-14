# Spec: Dropped tests and eval cases are gate findings
Change id: 0005. Status: proposed. Produced by: sdlc plugin 0.3.6, /sdlc-design prompt v1 (article p.14). Skills: coding-standards, security-baseline, ux-conventions, data-conventions, definition-of-done (plugin 0.3.6); overrides: none.

## Requirements

- A new gate check, `ratchets`, is added to `CHECKS_BY_PHASE` for phases (c), (d) and (e)
  only (`plugin/gate/checks.py:1709-1755`), for every `change_type`, not fix-type only.
  It is absent from (a), (b) and (f): `design_scope` already parks a committed file outside
  the change folder at those gates, deletions included (`checks.py:1697`, `:1760-1767`).
- The check's source is the committed diff: `git diff --name-status -M <merge base>...HEAD`,
  with rename detection (`-M`) named explicitly on the invocation, so the rule does not
  depend on the git configuration of the machine that runs it. It is invoked the way every
  other diff-reading check is, as an argument list through `plugin/gate/diff.py`'s `_git`
  helper, never a shell string (security-baseline rule 2 and 6: no command built by string
  formatting with external data, no `shell=True`).
- A **dropped test file**: a `D` whose path matches a `test_paths` glob
  (`hooks.test_file_lock.test_path_patterns`, the same patterns `check_test_lock` already
  reads, `checks.py:1278,1291`), or an `R` whose source matches a glob and whose destination
  matches none. An `R` from one test-path match to another is a rename, not a drop.
- A **dropped eval case**: the same rule over `evals/cases/` — the fixed path
  `plugin/evals/run.py:821` already defaults to, read with no new `sdlc.yaml` key — with one
  addition: an `R` whose destination folder name starts with `.` is a drop, because
  `discover` excludes a hidden folder with no deletion in the diff (`run.py:142-151`). A
  case is dropped when no path remains, at HEAD's committed tree, under its folder — decided
  from HEAD's tree, not from the diff's records alone, so that one file dropped out of a
  multi-file case while a sibling survives is never mistaken for the whole case's drop (panel
  decision #2, phase b; see Design). Files moving within the same case folder are not a drop.
- The check names every dropped file and case path in its `details` on failure.
- **A drop the approved plan declares is not a finding.** The plan is read as committed at
  the merge base, via `GateContext.approved_artifact("plan.md")` (`checks.py:124-135`),
  never the working tree or HEAD — unlike `check_plan_sync`, which reads the working-tree
  copy because the build session is expected to edit `plan.md` in (c); a drop must be excused
  by what the owner approved at gate (b), not by an edit the same commit that drops a file
  also makes. A file drop is declared when the approved plan's "## Files that change" lists
  its path (reusing `art.planned_files` / `plan_sync.is_planned`, the same matching
  `check_plan_sync` uses, including a directory listed with a trailing `/`,
  `checks.py:612-613,628`). A drop of a whole ratchet is declared by a fixed Proof item,
  `- ratchet: <name> may fall, because <why>`, naming `tests` or `evals` (skill
  `plan-template` gains the item form).
- A declared drop is `ok`, with the declared paths/ratchets in `details`; the PR's existing
  plan-conformance bullet at phases (c)/(d)/(e) (`_conformance_line`,
  `plugin/pr/description.py:249-259`) gains a clause naming them:
  `"declared drops: tests/x.py (plan)"`.
- **An undeclared drop is recorded as a risk-list-shaped hit** named after the ratchet:
  `ratchet: tests` for test files, `ratchet: evals` for eval cases — the literal key, not the
  bare `tests`/`evals` string, so it cannot be confused with an actual `sdlc.yaml: risk_list`
  entry of the same name. It fails the check and parks, as every failed deterministic check
  does (decision 11, decision 21: never the panel).
- **The owner's existing `sdlc:accept-risk` label accepts it, with no new label.**
  `plugin/state/unpark.py: risk_hits` (`unpark.py:68-84`) is extended to also read a check
  named `ratchets` in the gate record and union its `details.hits` keys with `risk_list`'s,
  so the label is not rejected as "nothing to accept" when only a ratchet hit is reported.
  The new `ratchets` check itself filters `ctx.status.risk_accepted` the way `check_risk_list`
  filters its own hits (`checks.py:743,768`), so an accepted ratchet hit passes on every
  later run of the same change. `status.yaml: risk_accepted` and `risk_accepted_by` record it
  exactly as a risk-list item; `owner_actions` judges the label's actor unchanged.
  `check_risk_list` itself is not modified.
- **Added skip markers are listed, never parked on.** The check scans the added lines of
  files under `test_paths` and of the test runner's configuration files (`pytest.ini`,
  `pyproject.toml`'s `[tool.pytest.ini_options]`, `setup.cfg`, `tox.ini`, `conftest.py`,
  `package.json`'s `jest` block, `jest.config.*`) for the anchored tokens `@pytest.mark.skip`,
  `@pytest.mark.xfail`, `pytest.skip(`, `--deselect`, `--ignore`, `-k`, `testpaths`,
  `norecursedirs`, `collect_ignore`, `it.skip(`, `describe.skip(`, `xit(`, `.only(`,
  `test.todo(`, `#[ignore]`, and writes each hit (file, line, token) to `details`. This never
  changes the check's `ok`/fail outcome.
- `plugin/agents/adversarial-reviewer.md` gains one numbered attack angle, after the
  existing angle 6 "The tests" (`adversarial-reviewer.md:51-52`), read at phases (c) and
  (d): each added skip marker the gate's `ratchets` check listed, and the plan line that
  declares it or "none".
- `template/REVIEW.md` gains one bullet under "## Framework rules", for every change type
  (not fix-only, unlike the existing test-lock bullet at `template/REVIEW.md:23-24`), reading
  the same skip-marker list at phase (e).
- This repository's own root `REVIEW.md` is a guardrail file (decision 6); the build run
  proposes the same line to the owner in a table (link, row, what is there now, what it must
  become) and never writes it.
- `plugin/skills/plan-template/SKILL.md`'s "## Proof" section gains the fixed item form
  `- ratchet: <name> may fall, because <why>`, documented beside the existing test/screenshot
  item forms (`plan-template/SKILL.md:31-33`).
- The finding's "what I need from you" (on an undeclared drop) names the dropped files and
  cases, says how to declare it (list the path under plan.md's "## Files that change", or add
  the `- ratchet:` Proof item, before the next run) or accept it (`sdlc:accept-risk`), and
  says plainly that a file emptied of its tests, a dropped test inside a kept file, or an
  edited test-runner configuration line is not caught by this check — that is the measured
  ratchets, the second change of ROADMAP R15, not this one (ux-conventions rule 4: an error
  message says what happened and what the person can do next).
- `docs/OPERATING_MODEL.md` §3's list of diff-reading checks (`plan_sync`, `design_scope`,
  `guardrails`, `risk_list`) gains `ratchets`; §6's "`sdlc:accept-risk` (accepts the
  risk-list hits the last gate reported)" gains a clause that a ratchet hit is included.
- The plugin version (`.claude-plugin/plugin.json`) is bumped, since `plugin/` and
  `template/` both change (decision 8: pinned process).
- Every behavior above ships with a test that fails without it; no existing test is skipped,
  weakened or deleted (coding-standards rule 4).
- No third-party dependency is added; Python only, Windows and Linux (CLAUDE.md
  conventions); `python -m compileall -q plugin tests tasks.py`, `python -m pytest` and
  `python -m ruff check .` stay green (coding-standards rule 8, definition-of-done).
- **Does not apply**: none of `sdlc.yaml: risk_list`'s configured items — auth, data
  migrations, money movement, production config — are touched by this design
  (security-baseline rule 8). Data-conventions does not apply: no new stored field, schema,
  migration or personal data; the dropped-path and skip-marker file/line details are the
  project's own source-tree metadata, already visible in its git history (data-conventions
  rule 1: classified public). Ux-conventions rules 1, 2, 3, 5 and 6 do not apply: there is no
  mock, component library, accessibility surface or translated copy; rule 7 (the phase (d)
  visual loop) does not apply — no UI changes.

## Design

- **`check_ratchets(ctx: GateContext) -> CheckResult`**, in `plugin/gate/checks.py`, beside
  `check_test_lock`: same signature and `_ok`/`_fail` shape as every other check
  (`checks.py:144-149`). Added to the (c), (d) and (e) tuples of `CHECKS_BY_PHASE`.
- A new helper in `plugin/gate/diff.py` parses `git diff --name-status -M -z <merge
  base>...HEAD` into typed records (status letter, one or two paths), since the existing
  `_z` only flattens a `--name-only` file list and cannot carry a rename's source and
  destination; it is invoked through the module's existing `_git` argument-list helper.
  A second new helper, `tree_files(root, ref, prefix) -> list[str]`, lists every path HEAD's
  committed tree holds under `prefix` (`git ls-tree -r --name-only <ref> -- <prefix>`, the
  same argument-list, no-shell-string convention). It exists because the diff's records
  alone cannot tell an eval case's survivor from its drop: a file under a case's folder that
  the diff never touches carries no record at all, so one file's deletion out of a
  multi-file case would be indistinguishable from the whole case's drop without also reading
  what the committed tree still holds at `ctx.diff.head` (panel decision #2, phase b).
- The test-path drop rule (D under a glob; R whose source matches and destination does not)
  is one small pure function taking only the parsed `--name-status` records, so it stays
  unit-testable without live git. The eval-case drop rule is a second pure function taking
  the same records **and** the case's survivor paths — the list `tree_files` reads at
  `ctx.diff.head` for `evals/cases/<name>/` — so that "a case is dropped" is decided from
  what the committed tree still holds, not from which paths the diff happened to touch: a
  case is dropped only when its survivor list is empty (after the dot-prefixed-rename
  addition is applied to the records). Both rules return a path list; `tree_files`'s own
  call is the only part that touches git, so the rules themselves still take plain arguments
  in their tests.
- Declaration is checked against `ctx.approved_artifact("plan.md")` (the merge-base commit,
  `checks.py:124-135`), using `art.planned_files` and `plan_sync.is_planned` for the
  "## Files that change" match, and a plain text search of the "## Proof" section for
  `- ratchet: tests` / `- ratchet: evals` (anchored on the literal ratchet name, not a
  regex over free text) for the whole-ratchet declaration.
- The check's `details` shape: `hits` (a dict exactly like `check_risk_list`'s, keyed
  `"ratchet: tests"` / `"ratchet: evals"`, mapping to the dropped paths — the same shape
  `unpark.risk_hits` already knows how to read from a check named `risk_list`, now read from
  a check named `ratchets` too), `declared` (a list of `{path or ratchet, "plan"}` entries
  for the PR's plan-conformance clause), and `skip_markers` (a list of `{file, line, token}`,
  never affecting `ok`).
- `plugin/state/unpark.py: risk_hits` reads both check names (`risk_list`, `ratchets`) from
  the same gate JSON and returns the union of their `details.hits` keys; nothing else in
  `unpark.py` changes, since `perform`'s accept-risk branch already treats any returned hit
  uniformly.
- `plugin/pr/description.py: _conformance_line` gains a clause built from the `ratchets`
  check's `details.declared`, appended to the existing `plan_sync`-derived sentence at
  phases (c)/(d)/(e); phases (a)/(b) are unchanged (no `ratchets` check runs there).
- The skip-marker scan reuses the committed diff's added lines only (a unified-diff `+`
  line, not the whole file), matched against the fixed per-language token list by a simple
  anchored substring/regex check per line, scoped to the file-glob/filename list in
  Requirements; it is a separate pure function from the drop rules, called by `check_ratchets`
  and folded into the same `CheckResult.details`.
- `plugin/agents/adversarial-reviewer.md`'s new angle and `template/REVIEW.md`'s new bullet
  are prose additions read by the reviewer and the owner respectively; neither reads the
  gate JSON itself — the delegation prompt and the PR body are what carry the `ratchets`
  check's findings to them, as every other angle and finding already does.
- `docs/OPERATING_MODEL.md` and `plugin/skills/plan-template/SKILL.md` changes are prose,
  edited sentence by sentence (CLAUDE.md "Things Claude gets wrong": a scripted rewrite is
  not used on documentation).
- Unchanged: `check_test_lock`, `check_risk_list`, `check_plan_sync`, the hooks
  (`test_file_lock.py`, `shell_guard.py`), the panel, every other gate check, and `framework/`
  (see Flagged concerns).

## Open questions from intent

- "How the finding becomes a risk-list hit: written into the `risk_list` check's
  `details.hits`, or read by `unpark.risk_hits` from the `ratchets` check's own details." —
  Answered from intent.md's own Proposed outcome (its lines 49–51): the second option. A new
  `ratchets` check owns its own `details.hits` and its own accepted-filter; `unpark.py:
  risk_hits` is extended to also scan a check named `ratchets`. `check_risk_list` is not
  modified. See Design.
- "The exact token list per language and how each token is anchored... so a test that
  mentions a token in a string... is listed at most, never parked on." — Answered: the list
  intent.md itself states (its lines 53-60) is exact; "listed, never parked" is Requirements'
  "never affecting `ok`" bullet above. Anchoring: a line-level substring/regex match on the
  token text, scoped to the named files only — this repository's own nine `--deselect` lines
  in the runbook's tests are under `test_paths` and would be listed, matching the intent's
  own worked example of what "listed, not parked" must tolerate.
- "Whether `evals/cases/` is a fixed path or read from the eval runner's own default." —
  Answered from the codebase: `plugin/evals/run.py:821` defaults the cases directory to the
  fixed `<root>/evals/cases`, with no `sdlc.yaml` key read anywhere in that module. The check
  reuses that same fixed path.
- "What a `- ratchet:` Proof item naming a ratchet that does not exist does." — Answered:
  change 1 recognizes exactly two ratchet names, `tests` and `evals`. No check at any gate
  parses the Proof section for a ratchet name other than those two literal strings, so a
  third name declares nothing for any real drop and causes no park, no warning and no
  gate-(b) finding — it is inert text. This is the simplest reading consistent with "no
  runner code" (intent.md's Constraints) and change 1's fixed, two-name scope; no new
  validation is added.
- "The wording of the plan-conformance clause on the PR, and of the banner line once T9 is
  built." — Answered for the clause: `"declared drops: tests/x.py (plan)"`, appended to the
  existing bullet (see Requirements and Design). The banner line is carried forward: T9 ("a
  risk-list hit becomes a banner line the merge accepts") does not exist in the code yet
  (`plugin/pr/description.py` has only "what needs you" lines today) and is out of this
  change's scope; it is read, not built, when T9 is.

## Flagged concerns

- [x] Risk-list-hit mechanism (open question 1, above): decided from intent.md's own text,
  not an open design choice — a parallel `ratchets` check plus an `unpark.py` extension, no
  change to `check_risk_list`.
- [x] Skip-marker token list and anchoring (open question 2, above): decided — the list and
  scope intent.md states verbatim, with "listed, never parked" read as "never affects `ok`".
- [x] `evals/cases/` path (open question 3, above): decided from the code — the fixed path
  `plugin/evals/run.py` already uses, no new `sdlc.yaml` key.
- [x] Unrecognized ratchet name in a Proof line (open question 4, above): decided — inert,
  because change 1's declaration logic only ever looks for the two literal names `tests` and
  `evals`.
- [x] Plan-conformance clause wording (open question 5, above): decided — the exact string
  intent.md's own context gives; the banner line is carried forward to T9, out of scope here.
- decided (by panel #1): Closed as confirmed rather than assumed: `framework/` is root-excluded from every phase job's checkout via `plugin/ci/run_phase.py`'s RUNNER_EXCLUDES (`/framework/` in `.git/info/exclude`), and `git diff --name-status -M <merge base>...HEAD` lists only committed paths, so it structurally cannot appear in `check_ratchets`' input; the design's scope boundary stands unchanged. — Assumption, because intent.md and the Proposed outcome's file list (its lines 77-80) are
  both silent on it: `framework/` — a second, independently-versioned checkout of this same
  plugin that `docs/OPERATING_MODEL.md` §6 says the CI runner loads "from the pinned
  framework checkout the session cannot edit", so that a run cannot weaken its own gate — is
  out of this change's scope. This design touches only the root-level `plugin/`, `template/`
  and `docs/` the intent names; the new check reaches the CI runner's own enforcement only
  through this project's existing pin/release process (decision 8), not as a side effect of
  this diff. If that assumption is wrong, the owner says so at this gate.

## Acceptance

- A unit test proves: a `D` under a `test_paths` glob with no plan declaration fails
  `check_ratchets` with `details.hits["ratchet: tests"]` naming the file; the same `D` with
  its path listed in the approved plan's "## Files that change" is `ok`; the same `D` with a
  `- ratchet: tests may fall, because <why>` Proof line in the approved plan is `ok`.
- A unit test proves the same three outcomes for a dropped `evals/cases/<name>/` folder
  (empty of survivors at HEAD's committed tree) and for an `R` whose destination starts
  with `.`.
- A unit test proves a partial, multi-file eval-case deletion — one file under the case
  folder dropped while `tree_files` still lists a sibling file under the same folder at
  HEAD — is not a drop (`test_ratchets_eval_case_partial_delete_is_not_a_drop`, panel
  decision #2, phase b).
- A unit test proves an `R` from one `test_paths` match to another is `ok` (a rename, not a
  drop), and that moving files within one eval case folder is not a drop.
- A unit test proves an accepted ratchet hit (`status.yaml: risk_accepted` containing
  `"ratchet: tests"`) makes `check_ratchets` pass on a later run with the same undeclared
  drop.
- A unit test proves `plugin/state/unpark.py: risk_hits` returns `"ratchet: tests"` when the
  gate JSON carries only a failing `ratchets` check (no `risk_list` check present or failing),
  so `sdlc:accept-risk` is not rejected as "nothing to accept".
- A unit test proves at least one hit per listed skip-marker token appears in
  `details.skip_markers` with its file and line, and that `check_ratchets` is still `ok` when
  only skip markers, no drop, are found.
- A unit test proves `CHECKS_BY_PHASE["c"]`, `["d"]` and `["e"]` contain `check_ratchets` and
  `["a"]`, `["b"]`, `["f"]` do not.
- A unit test proves `plugin/pr/description.py: _conformance_line` renders the
  `"declared drops: ... (plan)"` clause at phases (c)/(d)/(e) when `details.declared` is
  non-empty, and omits it otherwise.
- `plugin/agents/adversarial-reviewer.md`'s new angle and `template/REVIEW.md`'s new bullet
  and `plugin/skills/plan-template/SKILL.md`'s new Proof item form are present as prose (no
  test runs markdown, but a content check may assert the strings exist, matching how this
  repository already tests its own templates and skills).
- `python -m compileall -q plugin tests tasks.py`, `python -m pytest` and
  `python -m ruff check .` all exit 0 with no skipped or deleted test.
- No screenshot or mock: no UI changed.
