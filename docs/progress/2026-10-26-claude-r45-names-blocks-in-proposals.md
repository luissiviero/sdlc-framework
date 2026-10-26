# Progress — R45's names in the unbuilt proposals: one "Names since R45" block each (2026-10-26, no plugin version)

This session ran on branch `claude/r45-names-blocks-in-proposals`, from `main` at `80d7de5` (#396, plugin 1.0.47, tagged `v1.0.47`), as lane E of wave 5, started by the central session (`session_013TgyuTukXLjdZU3rmrgyRt`) at the owner's request. It is a documentation PR: nothing under `plugin/`, `template/` or `.github/` changes, and no version is bumped. No numbered choice, note or decision is taken (`python tasks.py next-free` after `git fetch origin` reads choice 275, candidate R68, note 62, decision 42, patch 1.0.48, none used).

## The owner's word
Relayed by the central session (the owner, 2026-10-25; the central session records it as a choice in its next record): after R45's fifth rename PR merges (#396, plugin 1.0.47 on `80d7de5`), the unbuilt proposals get decision 39's names by one short block near the top of each, mapping each old name the file uses to its new one, without rewriting any existing sentence (choice 126), so that citations by line and by quote into these files keep working; a proposal that uses none says "Names since R45: none of the renamed names appear here"; each candidate's ROADMAP row gets a dated annotation pointing to the block. This PR is the documentation PR of its own that choice 259's rule asks for an annotation that touches other candidates' rows.

## What was built
1. **A block in 40 proposals and in decision 41**, one line each, in place of the empty line that followed the file's title (`# <title>`, or decision 41's `## 41. <title>`). Nothing else in those files changes: `git diff --numstat` shows `1 1` for each of the 41 files, and every removed line is an empty line, so every line keeps its number and every sentence its words.
2. **A dated annotation in 42 ROADMAP rows**, at the end of each row's Status cell: R5, R6, R9, R11 to R16, R19 to R21, R23, R25, R26, R28 to R44 (R27 and R45 aside, which are out), R50 to R53, R56, R57, R60, R62, R66 and R67. Two proposals serve two rows each (`llm-wiki-adoption.md`: R56 and R57; `speed-beyond-the-sprint.md`: R52 and R53). R67's annotation names both its proposal and decision 41.

## The block's format
One line, the same in every file, so a script can read it:

`**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26, the text below keeps the old names, choice 126): ` followed by the pairs `` `old` -> new ``, separated by `; `, ending with `. \`.

- The old name is in backticks, as the file writes it, or as the token it writes in several forms: `` `(e)` `` stands for "(e)", "gate (e)", "phase (e)" and "the (e) merge"; `` `sdlc/<id>/a` `` for that branch in any change. A qualifier, when needed, follows the new name: `` `incident` -> `sdlc:triage` (the label) ``.
- The trailing ` \` is a Markdown line break: the block shows as its own line above the Status paragraph without an empty line between them, which is what keeps the line numbers. `detect-local-day.md`, whose title is followed by a heading, has no ` \`.
- A file that uses none of the renamed names: `**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26): none of the renamed names appear here.` Five proposals: `desktop-only-acts.md`, `detect-local-day.md`, `lifecycle-axis-features.md`, `pin-bump-pr.md`, `state-index.md`.
- R67's proposal and decision 41 were written on `main` `0ce7f6b` (#389, plugin 1.0.43), after the first rename PR: their blocks say "only the renames built after this file was written on `main` 0ce7f6b, in plugin 1.0.44 to 1.0.47", and list only R18's triage step, renamed `explain` in #390 (1.0.44). The phase letters they still write ("the gate the row calls (e)") were renamed before them and are not listed.

## The names, as built
Read from decision 39, the name table (`docs/reviews/2026-10-20-names-against-the-article.md`, sections 1 to 12), the rows added since (`docs/reviews/2026-10-25-names-added-since-decision-39.md`, N29 to N40) and the five rename records (`docs/progress/2026-10-25-claude-r45-1-phase-names.md` to `...-r45-4-files.md`, `docs/progress/2026-10-26-claude-r45-5-roles.md`). Every old name below is still read by the plugin for one release, until R45's sixth PR removes the live readers; the readers of history stay for good (choice 273: the remote `sdlc/<id>/<letter>` branches, `counters.py`'s `e`, the evidence files of merged changes).

| PR (version) | Old name | New name | Used in a block |
|---|---|---|---|
| 1 (1.0.43, #389) | phase and gate letters `(a)` to `(f)` | intent, design, build, test, deploy, maintain; "gate (deploy)" in generated text | yes |
| 1 | `status.yaml: phase` values `a` to `f`, `--phase a` to `f` | the phase names | yes |
| 1 | branches `sdlc/<id>/a` to `f` | `sdlc/<id>/intent` and the rest | yes (`a`, `c`) |
| 1 | labels `sdlc:a-ready` to `sdlc:f-ready` | `sdlc:intent-ready` and the rest | yes |
| 1 | check runs `sdlc/a` to `sdlc/f`; evidence `gate-<x>.json`, `claude-<x>.json`, `diff-<x>.patch` and the rest (row 60, N39); commits `run(<x>):` (N40); workflow names "SDLC build (c)", "SDLC merge (e)" (N4) | the phase name in each | `gate-b.json`, `gate-c.json` only |
| 1 | `/sdlc-plan`, `sdlc-plan.md` | `/sdlc-intent`, `sdlc-intent.md` | yes |
| 1 | "the read-only planning run"; the digest's "Phase (f): runbook and dismissal PRs" | "the planning run"; "Maintain: runbook and dismissal PRs" | the digest heading only |
| 2 (1.0.44, #390) | the labels `incident` and `schedule` | `sdlc:triage`, `sdlc:schedule` | yes |
| 2 | the verdict `escalate`; the brief's field "Word" | `park`; "Verdict" | `escalate` only |
| 2 | R18's triage step (N32): `--phase triage`, `plugin/ci/triage.py`, `triage=`, `claude-triage*.json`, "Triage (model-written)", `triage_checkout` | `explain` in each: `--phase explain`, `plugin/ci/explain.py`, `explain=`, "Explanation (model-written)" | yes |
| 3 (1.0.45, #393) | `deploy.production` | `deploy.production_gate` | yes |
| 3 | `bands.yaml: authorization` `preapproved \| go` | `allow \| ask` | yes |
| 3 | `external_review` | `second_opinion` | no proposal in scope uses it |
| 4 (1.0.46, #394) | the intent's `Status:` line | removed | no proposal in scope uses it |
| 4 | `sdlc-evals.yml` | `sdlc-agent-evals.yml` | yes |
| 4 | `ux-conventions`, `policies/ux-conventions.md` | `ux-and-brand`, `policies/ux-and-brand.md` | yes |
| 4 | the merge job `doorbell`; "fallback C1" | `on-approval`; "no merge App" | no proposal in scope uses them |
| 5 (1.0.47, #396) | "Ruleset 1", "Ruleset 2" | the merge ruleset, the review ruleset | yes |
| 5 | the review ruleset's name `... (decision 36, choice 251)` | `review and no direct writes on main` | no proposal in scope uses it |
| decision 39, section 11 (not built) | R31's ticket label `sdlc:intent` | `sdlc:ticket` | `tickets-become-intents.md` |
| decision 39, point 2 (moot) | `sdlc:c-approved`, `sdlc:d-approved` | none: decision 37 removed them | yes, as "none" |

**Not mapped, by rule:**
- **Row 87, "the owner" at four decision points** (PR 5): the product owner, the code owner, the release manager, the service owner. PR 5 kept "the owner" everywhere else, as the one person who owns the repository, and changed only the sentence at each decision point; a proposal's "the owner" is that person, or a decision point the build of that proposal will name. It is not a name with one replacement, so no block lists it.
- **Words that are not the renamed name where they stand:** a list marker or an option's letter ("option (a)", "T4's item (d)", "HANDOFF 4(a)"); the article's own words ("continues or is escalated to a human", p.42; "a pre-approved runbook", p.43, which the plugin still writes); the owner's triage at the maintain gate (row 21 keeps "triage" for it); the entry route `incident` (`status.yaml: entry_route`, not the label); GitHub's `schedule` trigger.
- **Records already written keep their names** (choice 273): change 0002's `evidence/gate-e.json`, change 0001's `claude-b.json`, change 0005's branch `sdlc/0005/a`.
- **R67's proposal and decision 41:** the PR 1 names, renamed before they were written.

## Which proposals, and why
A proposal is in when its ROADMAP candidate is in the Candidates table, not closed, and its Status cell does not record the whole of the row as built (a row that keeps a part to build is in). Read in `docs/ROADMAP.md` at `80d7de5`.

| Proposal | Candidate | In or out | Why |
|---|---|---|---|
| `accept-verb.md` | R6 | in | not built |
| `acting-at-3-sigma.md` | R41 | in | not built |
| `approvals-list.md` | R11 | in | not built |
| `build-test-approvals-label.md` | R12 | in | not built |
| `changes-in-flight-coordinator.md` | R66 | in | not built (after the trial) |
| `claude-md-standing-pr.md` | R37 | in | not built |
| `concurrent-changes.md` | R51 | in | built in 1.0.26 but for check 8 ("Check 8 is not built") |
| `desktop-only-acts.md` | R21 | in | first part built; "the rest ... keeps its place" |
| `detect-local-day.md` | R16 | in | not built |
| `detection-state-in-digest.md` | R40 | in | not built |
| `digest-needs-you-first.md` | R20 | in | not built |
| `docs-citation-reader.md` | R62 (and R8, done) | in | R62 not built |
| `drive-target-and-proof.md` | R14 | in | change 0004 built; the per-item Proof line is a second change, not built |
| `eval-suite-grows.md` | R35 | in | not built |
| `fix-proves-itself.md` | R34 | in | not built |
| `fix-round-fits-its-job.md` | R67 | in | not built; written after PR 1 (above) |
| `formatter-per-language.md` | R33 | in | built in 1.0.29; "full Rust support and the quarantine runbook stay open" |
| `intent-home.md` | R29 | in | part 1 built in 1.0.30; the rest not |
| `learning-from-incidents.md` | R42 | in | not built |
| `lifecycle-axis-features.md` | R60 | in | a study, neither built nor closed; its Order cell is blank |
| `llm-wiki-adoption.md` | R56, R57 (and R55, done) | in | R56 and R57 not built |
| `measures-that-change-a-decision.md` | R26 | in | built in 1.0.39 but for DORA (part 4); "the row staying here" |
| `pin-bump-pr.md` | R5 | in | its check built ahead; "the rest of the row keeps its place" |
| `preview-environment.md` | R39 | in | not built |
| `ratchets.md` | R15 | in | the first change built (1.0.2); the second not |
| `rejection-keeps-reason.md` | R32 | in | not built |
| `release-label-same-visit.md` | R13 | in | not built |
| `reviewer-tuning.md` | R38 | in | not built |
| `revisit-parallel-worktrees.md` | R50 | in | a trigger, not reached |
| `roles-and-manager.md` | R28 | in | not built (after the trial) |
| `runbook-prs-reviewed.md` | R36 | in | not built |
| `sandbox-closes-gaps.md` | R44 | in | built in 1.0.27 and 1.0.31 but for I6, kept "for after the real-project trial" (choice 261) |
| `scan-validates-findings.md` | R43 | in | not built |
| `speed-beyond-the-sprint.md` | R52, R53 (and R54, built) | in | R52 and R53 not built; R54's row is not annotated |
| `starting-a-project.md` | R30 | in | not built |
| `state-index.md` | R9 | in | part 2 applied; part 1 not built |
| `tickets-become-intents.md` | R31 | in | not built |
| `triage-one-act-dismissal.md` | R23 | in | not built |
| `weekly-window-guarded.md` | R25 | in | parts 1-2 built in 1.0.26; parts 3-5 after the trial |
| `what-you-can-do-here.md` | R19 | in | not built |
| `docs/decisions/41.md` | R67 | in | its decision, written after PR 1 (above) |
| `failed-run-explains-itself.md` | R18 | out | built in 1.0.36; what it leaves is other rows' (R13, R20 and the T entries), "as the row says" |
| `policy-sources.md` | R27 | out | built in 1.0.35; only the owner's settings edit is left |
| `gate-diff-and-evidence-hardening.md` | R59 | out | built in 1.0.27 with R44 |
| `trial-project-shape.md` | R61 | out | built in 1.0.29, "all five parts" |
| `template-copies-refresh.md` | R64 | out | built in 1.0.37 |
| `one-owner-per-fact.md` | R65 | out | parts 1 to 6 built |
| `names.md` | R45 | out | R45 itself |
| `okf-adoption.md` | R1 | out | closed (choice 257) |
| `session-tooling-pdf-web.md` | R2 | out | closed (choice 257) |
| `python-language-audit.md` | R4 | out | closed (choice 258) |
| `reviewer-on-opus.md` | R7 | out | Done |
| `external-design-check.md` | R8 | out | Done |
| `test-loop-closes-in-ci.md` | R10 | out | Done |
| `claude-comment-fix-round.md` | R17 | out | Done |
| `gate-e-approving-review.md` | R22 | out | Done |
| `risk-hit-in-banner.md` | R24 | out | Done |
| `pipeline-speed.md` | R46 to R49 | out | Done |
| `docs-lint-checks.md` | R58 | out | Done |
| `template-cli-default.md` | R63 | out | Done |

R3 has no proposal file ("proposed, not written"). Fifty-nine proposals: 40 in, 19 out.

## How it was built
A script in the session's scratch space found the old names (the regular expressions in the check below), printed each hit with its context, and the session judged every ambiguous hit by reading it: the phase letters used as list markers, every "triage", "escalate" and "pre-approved", the `incident` and `schedule` hits, the `gate-<x>.json` and branch names. The blocks and the ROADMAP annotations were written with the Edit tool, file by file and row by row.

## The completeness check
After the edits, the check below lists every old name still present in each file in scope, outside its block, and shows it listed in that file's block, or names why it is not an old name there. It also fails on a name the block lists that the file does not write, and on a "none" block in a file that uses one. Its result: **41 files, 0 gaps** (the full output is under the script).

<details>
<summary>The check (Python, run as <code>python check_blocks.py . scope.txt</code>, where scope.txt lists the 40 proposals above)</summary>

```python
"""Lane E's completeness check: every R45 old name still present in a proposal in scope
(outside its block) is listed in that file's "Names since R45" block, or is an exclusion
named below with its reason. Read-only; prints a report and exits 1 on a gap.

Usage: python check_blocks.py <repo root> <scope.txt> [--draft]
--draft prints the tokens each file's block needs, before the blocks exist.
"""

import re
import sys
from pathlib import Path

LETTER = r"([a-f])"
# (regex, token template). The token is what the block must carry in backticks.
PATTERNS = [
    # PR 1 (1.0.43)
    (r"sdlc/(?:<id>|\d{4})/" + LETTER + r"\b", "sdlc/<id>/{1}"),
    (r"sdlc:" + LETTER + r"-ready", "sdlc:{1}-ready"),
    (r"sdlc:" + LETTER + r"-approved", "sdlc:{1}-approved"),
    (r"`sdlc/" + LETTER + r"`", "sdlc/{1}"),
    (
        r"\b((?:gate|adversarial-review|run|claude|diff|decisions|panel-models|security-policy)-"
        + LETTER
        + r"(?:-\d+|-<n>)?\.(?:json|md|patch|txt))",
        "{0}",
    ),
    (r"\brun\(" + LETTER + r"\)", "run({1})"),
    (r"--phase[ =]" + LETTER + r"\b", "--phase {1}"),
    (r"(?<!--)\b[Pp]hase:? " + LETTER + r"\b(?![-'])", "phase {1}"),
    (r"`" + LETTER + r"`|\['" + LETTER + r"'\]|\{\"" + LETTER + r"\"", "{1}{2}{3}"),
    (r"SDLC \w+ \(" + LETTER + r"\)", "({1})"),
    (r"\(" + LETTER + r"\)", "({1})"),
    (r"/sdlc-plan\b", "/sdlc-plan"),
    (r"(?<![/\w-])sdlc-plan\.md", "sdlc-plan.md"),
    (r"read-only planning run", "read-only planning run"),
    # decision 39, section 11's R31 row (applied when R31 is built)
    (r"sdlc:intent\b(?!-)", "sdlc:intent"),
    # PR 2 (1.0.44)
    (r"`incident`", "incident"),
    (r"`schedule`", "schedule"),
    (r"\b[Ee]scalat\w*", "escalate"),
    (r"\b[Tt]riage\b", "triage"),
    # PR 3 (1.0.45)
    (r"deploy\.production\b(?!_gate)", "deploy.production"),
    (r"(?<![.\w])production: (?:true|false)\b", "production: true"),
    (r"`preapproved`|authorization: preapproved\b", "preapproved"),
    (r"`go`|authorization: go\b", "go"),
    (r"external_review", "external_review"),
    # PR 4 (1.0.46)
    (r"(?<!\*\*)`?Status:`?(?= (?:draft|proposed|accepted)\b(?!\*))|`Status:`", "Status:"),
    (r"sdlc-evals\.yml|SDLC evals\b", "sdlc-evals.yml"),
    (r"ux-conventions", "ux-conventions"),
    (r"doorbell", "doorbell"),
    (r"fallback C1", "fallback C1"),
    # PR 5 (1.0.47)
    (r"\b[Rr]uleset (1|2)\b", "ruleset {1}"),
    (r"\(decision 36, choice 251\)", "(decision 36, choice 251)"),
]

# Words the renames left as they are where they mean something else; reported, never required.
# A hit of these tokens is required only on the lines listed in REQUIRED_LINES.
CONTEXT_TOKENS = {"triage", "escalate", "({a})"}

# file -> {token: [lines]} where a context token IS an R45 old name (R18's triage step and
# text, the verdict `escalate`); every other line of that token is a kept word.
REQUIRED_LINES = {
    "detection-state-in-digest.md": {"triage": [83]},
    "digest-needs-you-first.md": {"triage": [77, 88, 90]},
    "fix-round-fits-its-job.md": {"triage": [28, 31, 59, 63, 81, 83, 92, 141]},
    "preview-environment.md": {"triage": [40, 72, 91, 113, 123]},
    "release-label-same-visit.md": {"triage": [58]},
    "weekly-window-guarded.md": {"triage": [94]},
    "roles-and-manager.md": {"escalate": [60]},
    "changes-in-flight-coordinator.md": {"escalate": [70]},
    "41.md": {"triage": [11, 14]},
}

# (file, line, token) -> reason: a hit that is not an R45 old name.
LIST_MARKER = "a list marker or an option's letter, not a phase"
HISTORY = "a record already written keeps its name (choice 273: history is never renamed)"
ROUTE = "the entry route `incident` (`status.yaml: entry_route`), kept (rows 37 and 43 rename the label only)"
EXCLUDE = {}


def exclude(file, lines, token, reason):
    for n in lines:
        EXCLUDE[(file, n, token)] = reason


for t in ("(a)", "(b)", "(c)", "(d)", "(e)"):
    exclude("lifecycle-axis-features.md", [38], t, LIST_MARKER)
exclude("sandbox-closes-gaps.md", [93], "(a)", LIST_MARKER)
exclude("sandbox-closes-gaps.md", [93], "(b)", LIST_MARKER)
exclude("sandbox-closes-gaps.md", [93], "(c)", LIST_MARKER)
exclude("roles-and-manager.md", [19, 178], "(d)", LIST_MARKER)
exclude("roles-and-manager.md", [104], "(a)", LIST_MARKER)
exclude("what-you-can-do-here.md", [86, 107], "(a)", LIST_MARKER)
exclude("what-you-can-do-here.md", [85, 108], "(b)", LIST_MARKER)
exclude("intent-home.md", [63, 107], "(a)", "HANDOFF's item 4(a), a list marker")
exclude("eval-suite-grows.md", [60], "gate-e.json", HISTORY + "; change 0002's gate record")
exclude("learning-from-incidents.md", [34, 60], "gate-e.json", HISTORY + "; change 0002's gate record")
exclude("weekly-window-guarded.md", [49], "claude-b.json", HISTORY + "; change 0001's session result")
exclude("ratchets.md", [37], "sdlc/<id>/a", HISTORY + "; change 0005's intent branch `sdlc/0005/a`")
exclude("learning-from-incidents.md", [57], "incident", ROUTE)
exclude("tickets-become-intents.md", [65], "incident", ROUTE)
exclude("tickets-become-intents.md", [62], "schedule", "GitHub's `schedule` trigger, not the label")
# R67's proposal and decision 41 were written on main 0ce7f6b (#389, plugin 1.0.43): the
# phase names were already built; only the names of PRs 2 to 5 changed after them.
WRITTEN_AFTER_PR1 = {"fix-round-fits-its-job.md", "41.md"}
PR1_TOKENS = re.compile(
    r"^\([a-f]\)$|^[a-f]$|^sdlc/|^sdlc:[a-f]-|^--phase|^phase |^run\(|^/sdlc-plan|sdlc-plan\.md|-[a-f](-\d+)?\.\w+$"
)

BLOCK_HEAD = "**Names since R45**"


def hits(text):
    out = []
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if line.startswith(BLOCK_HEAD):
            continue
        for rx, tmpl in PATTERNS:
            for m in re.finditer(rx, line):
                groups = [m.group(0)] + [g or "" for g in m.groups()]
                token = tmpl.format(*groups)
                out.append((n, token))
    return out


def block_of(text):
    for line in text.splitlines():
        if line.startswith(BLOCK_HEAD):
            return line
    return None


def classify(name, n, token):
    """'required', or the reason it is not."""
    if (name, n, token) in EXCLUDE:
        return EXCLUDE[(name, n, token)]
    if name in WRITTEN_AFTER_PR1 and PR1_TOKENS.search(token):
        return "built in PR 1 (1.0.43) before this file was written on 0ce7f6b"
    if token in ("triage", "escalate"):
        if n in REQUIRED_LINES.get(name, {}).get(token, []):
            return "required"
        if token == "triage":
            return "the owner's triage at maintain (row 21), or the article's word, kept"
        return "the article's word (p.42), kept"
    return "required"


def main():
    root = Path(sys.argv[1])
    scope = [ln.split()[0] for ln in Path(sys.argv[2]).read_text().splitlines() if ln.strip()]
    draft = "--draft" in sys.argv
    files = [root / "docs/proposals" / f"{s}.md" for s in scope] + [root / "docs/decisions/41.md"]
    gaps = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        name = path.name
        req, kept = {}, {}
        for n, token in hits(text):
            why = classify(name, n, token)
            (req if why == "required" else kept).setdefault(token, []).append(n)
        block = block_of(text)
        print(f"## {path.relative_to(root).as_posix()}")
        if draft:
            print(f"   needs: {sorted(req)}")
            for token, ns in sorted(kept.items()):
                print(f"   not an old name: `{token}` lines {sorted(set(ns))}")
            continue
        if block is None:
            print("   NO BLOCK")
            gaps += 1
            continue
        listed = set(re.findall(r"`([^`]+)` ->", block))
        if not req:
            ok = "none of the renamed names appear here" in block
            print(f"   block says none: {'yes' if ok else 'NO'}")
            gaps += 0 if ok else 1
        for token, ns in sorted(req.items()):
            status = "covered" if token in listed else "MISSING"
            gaps += status == "MISSING"
            print(f"   {status}: `{token}` lines {sorted(set(ns))}")
        rest = "\n".join(ln for ln in text.splitlines() if not ln.startswith(BLOCK_HEAD))
        for token in sorted(listed - set(req)):
            if token in rest:
                print(f"   also listed, written in the file: `{token}`")
                continue
            print(f"   EXTRA in block, not found in the file: `{token}`")
            gaps += 1
        for token, ns in sorted(kept.items()):
            reason = classify(name, ns[0], token)
            print(f"   not an old name: `{token}` lines {sorted(set(ns))}: {reason}")
    print(f"\n{len(files)} files, {gaps} gaps")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
```
</details>

<details>
<summary>Its output</summary>

```text
## docs/proposals/accept-verb.md
   covered: `(e)` lines [4, 16, 26, 48, 50]
## docs/proposals/acting-at-3-sigma.md
   covered: `(c)` lines [28, 46, 96, 111, 119]
   covered: `(d)` lines [28, 46, 96, 111, 119]
   covered: `(f)` lines [62, 63, 64, 74, 87, 99, 100, 111, 121]
   covered: `go` lines [58, 60, 61, 62, 77]
   covered: `incident` lines [59, 77]
   covered: `preapproved` lines [58, 61]
   covered: `sdlc/<id>/a` lines [63, 100]
   covered: `sdlc:c-approved` lines [96]
   covered: `sdlc:d-approved` lines [96]
## docs/proposals/approvals-list.md
   covered: `(a)` lines [40, 64]
   covered: `(b)` lines [40, 64, 83]
   covered: `(c)` lines [64]
   covered: `(d)` lines [64]
   covered: `(e)` lines [40, 64, 82, 83]
   covered: `schedule` lines [40, 64, 83]
   covered: `sdlc:c-approved` lines [40]
   covered: `sdlc:d-approved` lines [40]
   not an old name: `triage` lines [35, 47]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/build-test-approvals-label.md
   covered: `(b)` lines [44]
   covered: `(c)` lines [4, 32, 44, 53, 65]
   covered: `(d)` lines [4, 32, 44, 52, 53, 65]
   covered: `(e)` lines [44, 52, 53]
   covered: `sdlc:c-approved` lines [32, 44]
   covered: `sdlc:c-ready` lines [44]
   covered: `sdlc:d-approved` lines [32, 44]
   covered: `sdlc:d-ready` lines [44]
## docs/proposals/changes-in-flight-coordinator.md
   covered: `(b)` lines [60]
   covered: `(e)` lines [4, 35, 36, 45, 59, 60, 70]
   covered: `/sdlc-plan` lines [45, 55]
   covered: `escalate` lines [70]
## docs/proposals/claude-md-standing-pr.md
   covered: `(d)` lines [64]
   covered: `(e)` lines [4, 47, 64, 65, 77, 93, 107, 129]
   covered: `incident` lines [67]
   covered: `ruleset 2` lines [122]
   covered: `sdlc-evals.yml` lines [37, 62, 69, 97, 130]
## docs/proposals/concurrent-changes.md
   covered: `(c)` lines [48]
   covered: `(d)` lines [48]
   covered: `(e)` lines [48]
   covered: `/sdlc-plan` lines [49]
   covered: `sdlc/<id>/a` lines [49]
## docs/proposals/desktop-only-acts.md
   block says none: yes
## docs/proposals/detect-local-day.md
   block says none: yes
## docs/proposals/detection-state-in-digest.md
   covered: `triage` lines [83]
   not an old name: `triage` lines [16, 59, 109]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/digest-needs-you-first.md
   covered: `(a)` lines [92, 108, 109]
   covered: `(c)` lines [59]
   covered: `(d)` lines [59]
   covered: `(f)` lines [57, 94]
   covered: `--phase f` lines [59]
   covered: `/sdlc-plan` lines [109]
   covered: `incident` lines [57, 75, 88, 113]
   covered: `schedule` lines [113]
   covered: `sdlc:f-ready` lines [43, 113]
   covered: `triage` lines [77, 88, 90]
   also listed, written in the file: `Phase (f): runbook and dismissal PRs`
   not an old name: `triage` lines [13, 19, 50, 122]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/docs-citation-reader.md
   covered: `(b)` lines [16, 69]
## docs/proposals/drive-target-and-proof.md
   covered: `(b)` lines [65, 66, 80, 85, 96]
   covered: `(c)` lines [65, 66, 67, 73, 79, 84, 100]
   covered: `(d)` lines [40, 55, 65, 67, 73, 79, 84, 85]
   covered: `(e)` lines [65, 67, 73, 79, 100]
   covered: `gate-b.json` lines [67]
   covered: `gate-c.json` lines [67]
   covered: `ux-conventions` lines [89]
## docs/proposals/eval-suite-grows.md
   covered: `(b)` lines [63]
   covered: `(e)` lines [4, 37, 44, 60, 61, 70, 76, 87, 106, 117]
   covered: `phase a` lines [61, 87]
   covered: `phase e` lines [61, 87]
   covered: `ruleset 2` lines [89]
   covered: `sdlc-evals.yml` lines [30, 53, 55, 56, 57, 58, 69, 82, 89, 100, 114, 115, 116, 118, 124]
   not an old name: `gate-e.json` lines [60]: a record already written keeps its name (choice 273: history is never renamed); change 0002's gate record
## docs/proposals/fix-proves-itself.md
   covered: `(c)` lines [4, 43, 55, 71, 72, 73, 81, 92, 93, 96, 102, 107, 110, 111, 112, 141, 143]
   covered: `(d)` lines [71, 72, 110]
   covered: `(e)` lines [71, 72, 74, 110]
   covered: `/sdlc-plan` lines [85, 118, 148]
   covered: `c` lines [73]
   covered: `gate-c.json` lines [94]
   covered: `phase b` lines [75]
## docs/proposals/fix-round-fits-its-job.md
   covered: `triage` lines [28, 31, 59, 63, 81, 83, 92, 141]
   also listed, written in the file: `plugin/ci/triage.py`
   also listed, written in the file: `steps.phase.outputs.triage`
   not an old name: `(e)` lines [36, 123]: built in PR 1 (1.0.43) before this file was written on 0ce7f6b
## docs/proposals/formatter-per-language.md
   covered: `(c)` lines [81]
   covered: `(d)` lines [81]
   covered: `(e)` lines [81]
## docs/proposals/intent-home.md
   covered: `(a)` lines [40, 65, 76, 78, 80, 104, 115, 121, 133, 134]
   covered: `(b)` lines [47]
   covered: `(d)` lines [48, 67, 103]
   covered: `--phase a` lines [97]
   covered: `/sdlc-plan` lines [33, 34, 40, 46, 49, 59, 63, 76, 86, 96, 97, 104, 107, 108, 114, 130, 131]
   covered: `sdlc-plan.md` lines [48, 49, 64]
   covered: `sdlc/<id>/a` lines [4, 40, 46, 63, 76, 90, 97, 104, 107]
   covered: `sdlc:a-ready` lines [64, 76, 90]
   not an old name: `(a)` lines [63, 107]: HANDOFF's item 4(a), a list marker
## docs/proposals/learning-from-incidents.md
   covered: `(e)` lines [4, 34, 40, 44, 57, 60, 70, 76, 93, 120]
   not an old name: `gate-e.json` lines [34, 60]: a record already written keeps its name (choice 273: history is never renamed); change 0002's gate record
   not an old name: `incident` lines [57]: the entry route `incident` (`status.yaml: entry_route`), kept (rows 37 and 43 rename the label only)
## docs/proposals/lifecycle-axis-features.md
   block says none: yes
   not an old name: `(a)` lines [38]: a list marker or an option's letter, not a phase
   not an old name: `(b)` lines [38]: a list marker or an option's letter, not a phase
   not an old name: `(c)` lines [38]: a list marker or an option's letter, not a phase
   not an old name: `(d)` lines [38]: a list marker or an option's letter, not a phase
   not an old name: `(e)` lines [38]: a list marker or an option's letter, not a phase
## docs/proposals/llm-wiki-adoption.md
   covered: `(a)` lines [57]
   covered: `(b)` lines [57, 59, 67]
   covered: `(c)` lines [68]
   covered: `(e)` lines [42, 60, 68]
   covered: `/sdlc-plan` lines [57]
## docs/proposals/measures-that-change-a-decision.md
   covered: `(a)` lines [78]
   covered: `(e)` lines [62]
   covered: `deploy.production` lines [77, 85]
   covered: `sdlc/<id>/c` lines [67]
## docs/proposals/pin-bump-pr.md
   block says none: yes
## docs/proposals/preview-environment.md
   covered: `(d)` lines [97]
   covered: `(e)` lines [4, 40, 55, 58, 70, 72, 82, 90, 91, 97]
   covered: `deploy.production` lines [46, 57, 64, 68]
   covered: `go` lines [60, 61]
   covered: `ruleset 1` lines [72, 91]
   covered: `ruleset 2` lines [82]
   covered: `triage` lines [40, 72, 91, 113, 123]
## docs/proposals/ratchets.md
   covered: `(a)` lines [69]
   covered: `(b)` lines [69, 70, 80, 96, 107, 117]
   covered: `(c)` lines [4, 69, 70, 72, 82]
   covered: `(d)` lines [4, 69, 72, 82]
   covered: `(e)` lines [4, 69, 72, 82]
   covered: `(f)` lines [69, 107]
   covered: `incident` lines [60]
   covered: `sdlc:a-ready` lines [37]
   not an old name: `sdlc/<id>/a` lines [37]: a record already written keeps its name (choice 273: history is never renamed); change 0005's intent branch `sdlc/0005/a`
## docs/proposals/rejection-keeps-reason.md
   covered: `(a)` lines [22, 37, 41, 54, 65, 91, 102]
   covered: `(b)` lines [75]
   covered: `(e)` lines [22, 37, 41, 75, 91]
   covered: `(f)` lines [54]
   not an old name: `triage` lines [16, 63, 95]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/release-label-same-visit.md
   covered: `(e)` lines [19, 32, 56, 58]
   covered: `deploy.production` lines [32, 48]
   covered: `sdlc:e-ready` lines [57]
   covered: `triage` lines [58]
## docs/proposals/reviewer-tuning.md
   covered: `(e)` lines [44, 46, 59, 63, 92, 95]
   covered: `sdlc-evals.yml` lines [34, 59, 66, 93, 129]
## docs/proposals/revisit-parallel-worktrees.md
   covered: `(e)` lines [32]
## docs/proposals/roles-and-manager.md
   covered: `(a)` lines [43, 86, 87, 112, 135, 148, 173, 213]
   covered: `(b)` lines [45, 64, 82, 86, 87, 88, 89, 93, 97, 113, 114, 115, 123, 125, 137, 148, 171, 210, 212]
   covered: `(c)` lines [93, 97, 115, 199]
   covered: `(d)` lines [93, 97, 115, 199]
   covered: `(e)` lines [37, 63, 82, 88, 89, 90, 93, 97, 116, 140, 162, 212]
   covered: `(f)` lines [45, 89, 91, 117, 148, 214]
   covered: `/sdlc-plan` lines [4, 31, 47, 57, 64, 65, 132, 173, 213, 222]
   covered: `escalate` lines [60]
   covered: `sdlc-evals.yml` lines [31, 44, 164, 222]
   covered: `sdlc-plan.md` lines [64]
   covered: `ux-conventions` lines [59]
   not an old name: `(a)` lines [104]: a list marker or an option's letter, not a phase
   not an old name: `(d)` lines [19, 178]: a list marker or an option's letter, not a phase
   not an old name: `triage` lines [13, 22, 45, 127, 130, 191, 214]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/runbook-prs-reviewed.md
   covered: `(b)` lines [71, 98]
   covered: `(d)` lines [58, 87]
   covered: `(e)` lines [4, 34, 47, 57, 67, 69, 70, 71, 98, 99, 104]
   covered: `(f)` lines [37, 58, 60, 85, 111, 120]
   covered: `go` lines [60]
   covered: `incident` lines [47]
   covered: `preapproved` lines [59]
   covered: `ruleset 2` lines [84]
   not an old name: `triage` lines [104]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/sandbox-closes-gaps.md
   covered: `(c)` lines [70]
   covered: `(d)` lines [83]
   covered: `(e)` lines [83]
   covered: `sdlc-evals.yml` lines [72]
   not an old name: `(a)` lines [93]: a list marker or an option's letter, not a phase
   not an old name: `(b)` lines [93]: a list marker or an option's letter, not a phase
   not an old name: `(c)` lines [93]: a list marker or an option's letter, not a phase
   not an old name: `triage` lines [94]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/scan-validates-findings.md
   covered: `(f)` lines [28, 37, 52, 66, 72, 118]
   covered: `incident` lines [66]
   covered: `sdlc:f-ready` lines [66]
   not an old name: `triage` lines [16, 19, 28, 52, 58, 102, 107, 118]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/speed-beyond-the-sprint.md
   covered: `(a)` lines [62]
   covered: `(b)` lines [26, 48]
   covered: `(e)` lines [4, 26, 36, 46, 48, 56]
   covered: `/sdlc-plan` lines [56]
   covered: `deploy.production` lines [48, 61]
   covered: `production: true` lines [61]
   not an old name: `triage` lines [62]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/starting-a-project.md
   covered: `(e)` lines [71]
## docs/proposals/state-index.md
   block says none: yes
## docs/proposals/tickets-become-intents.md
   covered: `(a)` lines [4, 31, 56, 64, 76, 80, 95, 97, 103, 119, 123]
   covered: `(c)` lines [119]
   covered: `(e)` lines [31, 119]
   covered: `(f)` lines [104]
   covered: `--phase a` lines [63, 99]
   covered: `/sdlc-plan` lines [34, 46, 60, 63, 72, 95, 99, 110, 137]
   covered: `incident` lines [104]
   covered: `sdlc-evals.yml` lines [62]
   covered: `sdlc-plan.md` lines [63, 99]
   covered: `sdlc/<id>/a` lines [63, 75, 86]
   covered: `sdlc:a-ready` lines [63, 104]
   covered: `sdlc:intent` lines [4, 74, 79, 97, 129]
   not an old name: `incident` lines [65]: the entry route `incident` (`status.yaml: entry_route`), kept (rows 37 and 43 rename the label only)
   not an old name: `schedule` lines [62]: GitHub's `schedule` trigger, not the label
   not an old name: `triage` lines [54]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/triage-one-act-dismissal.md
   covered: `(a)` lines [55, 64]
   covered: `(e)` lines [89]
   covered: `(f)` lines [4, 22, 41]
   covered: `a` lines [55]
   covered: `b` lines [53]
   covered: `f` lines [55]
   covered: `incident` lines [57]
   covered: `schedule` lines [41, 55, 64, 88]
   not an old name: `triage` lines [3, 10, 13, 16, 22, 35, 37, 41, 49, 53]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/proposals/weekly-window-guarded.md
   covered: `(b)` lines [49, 60, 96]
   covered: `(c)` lines [73]
   covered: `(d)` lines [60]
   covered: `(e)` lines [49, 61, 92, 98]
   covered: `triage` lines [94]
   not an old name: `claude-b.json` lines [49]: a record already written keeps its name (choice 273: history is never renamed); change 0001's session result
   not an old name: `escalate` lines [19, 54]: the article's word (p.42), kept
## docs/proposals/what-you-can-do-here.md
   covered: `(a)` lines [59, 61, 72, 79]
   covered: `(b)` lines [42, 68, 73, 74, 126]
   covered: `(c)` lines [42, 73, 74, 75, 76, 98, 103]
   covered: `(d)` lines [42, 73, 74, 75, 76, 98, 103]
   covered: `(e)` lines [42, 59, 61, 77]
   covered: `(f)` lines [59, 61, 68, 79, 98, 115]
   covered: `/sdlc-plan` lines [61]
   covered: `a` lines [59]
   covered: `deploy.production` lines [119]
   covered: `schedule` lines [59, 61, 79]
   covered: `sdlc-plan.md` lines [61]
   covered: `sdlc:c-approved` lines [61, 76]
   covered: `sdlc:d-approved` lines [61, 76]
   covered: `sdlc:e-ready` lines [77]
   not an old name: `(a)` lines [86, 107]: a list marker or an option's letter, not a phase
   not an old name: `(b)` lines [85, 108]: a list marker or an option's letter, not a phase
   not an old name: `escalate` lines [19, 51]: the article's word (p.42), kept
   not an old name: `triage` lines [13, 59, 126]: the owner's triage at maintain (row 21), or the article's word, kept
## docs/decisions/41.md
   covered: `triage` lines [11, 14]

41 files, 0 gaps
```
</details>

## The citations
Every citation this PR adds was opened and compared with the sentence (choice 241): decision 39 (point 1's "Rows 1 to 88 and section 11 are decided as their Verdict column says", point 2's rows 28 and 29 "moot"), decision 37 (the Full profile and its labels removed), choice 126 ("A kept record is annotated, never rewritten", `docs/progress/choices.md`), choice 273 (the readers of history), the versions and PRs (`git rev-list -n1 v1.0.43` to `v1.0.47`: `0ce7f6b` #389, `dc9692b` #390, `54d498e` #393, `05d9412` #394, `80d7de5` #396), and `0ce7f6b` as the parent of R67's commit `1cdca24` (`git log`).

## The fresh-context review
Pending: a fresh-context sub-agent reviews a sample of the blocks against their files (report only); its findings and what was done are added here before the merge is asked for.

## Port list
Nothing under `plugin/` or `template/` changes: not on the port list.

## Proposed edits for the owner
None. No guardrail file is touched.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its head. |
