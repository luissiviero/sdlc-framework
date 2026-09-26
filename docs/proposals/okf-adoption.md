---
type: Proposal
title: OKF adoption — the Open Knowledge Format applied to the SDLC framework
description: Where the Open Knowledge Format already matches the framework, where adopting it would pay (lessons/ first), and what that would take; proposed, not implemented.
status: proposed
roadmap: R1
sources:
  - id: blog
    resource: https://cloud.google.com/blog/products/data-analytics/introducing-the-open-knowledge-format
    title: "Introducing the Open Knowledge Format (Google Cloud blog, 2026-06-12, v0.1)"
  - id: spec
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
    title: "OKF SPEC.md v0.2"
  - id: analysis
    resource: docs/handoffs/inputs/session-6-okf-analysis.html
    title: "OKF and the SDLC framework — the owner's thinking-session analysis of 2026-09-25 (plugin 0.2.19)"
generated: { by: sdlc-framework-session/7, at: 2026-09-25T23:00:00Z }
---

# OKF adoption

**Status: proposed (roadmap R1). Nothing here is implemented.** (`proposed` is this repository's roadmap value, not one of OKF's lifecycle values `draft | stable | deprecated`; OKF's permissive conformance tolerates an unknown value, SPEC §11.)

AI agents need knowledge that lives outside the model, and today it is scattered across catalogs, wikis, code comments and a few people's heads.[^blog] Google's Open Knowledge Format (OKF) answers with a file format, not a service: a directory of Markdown files, one concept per file, with a small YAML frontmatter block.[^blog] Version 0.2 of the spec adds provenance, trust, freshness and lifecycle fields for corpora that agents maintain.[^spec]

The framework already follows most of OKF's ideas. This proposal records where they match, where they differ, and the few places where adopting the format would pay off.[^analysis]

## What OKF is

**The bundle.** A bundle is a directory of Markdown files, ideally in git; it is the unit you share.[^spec] Each file is one concept: a table, a metric, a playbook, a runbook, an API. The file's path is its identity. Concepts link to each other with ordinary Markdown links, so a bundle is a graph, not just a tree.[^analysis]

**Frontmatter.** A YAML block at the top of each file holds the fields you query; the body holds everything else. Only `type` is required. `title`, `description`, `resource` and `tags` are recommended.[^spec]

**Reserved files.** Two filenames are optional in any folder. `index.md` lists what the folder holds, so an agent can read one level at a time. `log.md` records the folder's change history.[^spec]

**Three design principles.**[^analysis]

- *Minimally opinionated.* Only `type` is required. The spec defines the interoperability surface, not your content model.
- *Producer/consumer independence.* A human, a pipeline or an LLM can write a bundle; anything that reads Markdown can consume it.
- *Format, not platform.* OKF will never require a proprietary account or SDK to read, write or serve.

**What v0.2 adds.** The blog post announced v0.1; the repository's spec is at v0.2.[^spec] It answers three questions an agent-maintained corpus raises: where did this come from, who checked it, and is it still true?

| Field | What it does |
|---|---|
| `sources` | Structured provenance. Each entry has a required `resource` and optional `id`, `title`, and the credibility signals `author`, `usage_count` and `last_modified`. Footnotes cite a source by `id`, not by position, so citations survive agents rewriting the text. |
| `generated: {by, at}` | Who or what produced the content, and when it last changed meaningfully. Replaces v0.1's `timestamp`. |
| `verified` | A list of sign-off events. Trust tiers are derived from it, never stored: unverified, machine-confirmed, human-reviewed. |
| Actors | `human:<id>`, `process:<id>` and `<producer>/<version>`, so "was this a person?" is a string check. |
| `status`, `stale_after` | Lifecycle (`draft`, `stable` or `deprecated`; absent means `stable`) and an absolute expiry instant, so staleness is a plain comparison. |
| Attested Computation | A concept type that fixes how a value must be computed. The agent may only supply parameters; deterministic code on the consumer's side checks that what ran is what was sanctioned. |

**Conformance stays permissive.** A bundle conforms if every non-reserved file has parseable frontmatter with a non-empty `type`. A consumer must not reject a bundle for unknown types or keys, missing optional fields, broken links or missing indexes.[^spec]

Google also shipped proofs of concept: an enrichment agent, a single-file HTML graph viewer and three sample bundles. Google Cloud's Knowledge Catalog can ingest OKF.[^analysis]

## The 25-row mapping

Each row reads the framework as it will be once fully built, noting what was already implemented at plugin 0.2.19. "Complexity" is the effort in the current codebase.[^analysis]

| # | OKF item | What it is | In the framework today (0.2.19) | Worth adopting? | Complexity |
|---|---|---|---|---|---|
| 1 | Knowledge bundle | A directory of Markdown files, ideally in git; the unit you share. | **Yes.** `changes/`, `lessons/`, `docs/` and the skills are Markdown and YAML in git; the repo is the source of truth (decision 9). | Already done. | None |
| 2 | One file per concept, YAML frontmatter, required `type` | A machine-readable header on every knowledge file. | **Partial.** Skills, agents and commands have frontmatter. `intent.md`, `spec.md`, `plan.md` and lessons carry metadata in a prose header line (`Author: … Status: … Change id: …`). | **Medium.** Mainly for `lessons/`, a growing corpus the agent reads. Low for intent, spec and plan, whose headers are already parsed and gated. | Lessons: low; no code validates them yet. Intent, spec, plan: medium; header parsing lives in `plugin/gate/artifacts.py`, plus gate checks and tests. |
| 3 | `title`, `description`, `resource`, `tags` | A one-line summary for indexes and search, the underlying asset, and tags. | **Partial.** Skills have `description` and use it as the load trigger. Lessons, eval cases and changes have none. | **Medium.** Tags such as metric, rule and component would let `/sdlc-maintain` filter lessons instead of reading all of them. | Low |
| 4 | Structured body, conventional headings | Prefer headings, tables and lists over prose; no sections are required. | **Yes, stricter.** Sections are fixed in code (`INTENT_SECTIONS`, `SPEC_SECTIONS`, `PLAN_SECTIONS`); the gate parks a change if one is missing. | Keep as is. The strictness is deliberate. | None |
| 5 | `sources` and keyed footnotes | Structured provenance whose citations survive agents rewriting the text. | **Partial.** Sources are cited in prose: the article by PDF page, `NOTES.md` with verbatim quotes and URLs, an incident's `## Evidence` citing a lesson, each policy skill's `## Source`. | **Low–medium.** Most useful where agents rewrite text on fix rounds (`spec.md`) and for `NOTES.md` platform facts. | Low as a convention; medium if the gate validates it. |
| 6 | `generated {by, at}` | Who or what produced the content, and when. | **Mostly.** The spec header logs plugin and prompt versions, the intent has Author, `status.yaml` has timestamps, evidence JSON has `at`. Lessons and eval cases lack it. | **Low.** Add it to lessons and eval cases only. | Low |
| 7 | `verified` and trust tiers | Sign-off events; tiers derived from them. | **Yes, through git.** The owner's merge is human verification; the adversarial verdict and `gate-<phase>.json` are machine verification. The intent template says: "the merge is the record of acceptance; do not add approval lines." | **Low.** Don't copy sign-offs into files; that conflicts with an existing rule. The derived-tier idea could label lessons and NOTES facts. | Low, but it touches a settled rule. Ask before reopening. |
| 8 | Actor convention | `human:`, `process:`, `<producer>/<version>` used the same way everywhere. | **Partial.** Actors are recorded (label actors in `status.yaml`, dismissal `by`, panel reviewer and advocate), each in its own format. | **Low–medium.** One format would make "was this a person?" the same check across all JSON records. | Medium: several schemas and a `schema_version` bump. |
| 9 | `status: draft, stable, deprecated` | Whether a document is still current. | **Partial.** Intent status and change phase (including abandoned) exist. Lessons and skills can't be marked deprecated. | **Low**, until lessons pile up and some describe code that no longer exists. | Low |
| 10 | `stale_after` | An absolute expiry time; stale once "now" passes it. | **Partial, scattered.** Detection dismissals expire (`until`), runbooks carry `rehearsed_at`, `NOTES.md` says to re-verify when the minimum Claude Code version moves, and the data-conventions skill asks for a freshness expectation. | **Medium.** For `NOTES.md` platform facts, which drive hook behaviour, and for the rehearsed rollback that decision 26 pre-approves. Unverified: whether the age of `rehearsed_at` is enforced. | Low as a convention; medium if the gate or preflight enforces it. |
| 11 | Cross-links | Links from the bundle root; broken links tolerated. The bundle forms a graph. | **Partial.** PR bodies carry a "Links:" line, a lesson's `## Prevention` points to its eval case, an incident cites a lesson. `plan.md` refers to intent and spec by date, not by link. | **Low–medium.** Links between lesson, change folder, eval case and PR would make incident history navigable. | Low |
| 12 | `references/` folder | External material mirrored inside the bundle (spec §6.3). | **Yes, in spirit.** `docs/reference/` holds the page-tagged source article. | Nothing to add. | None |
| 13 | `index.md` for progressive disclosure | A per-folder list of links with one-line descriptions, so an agent reads one level at a time. | **Only through skills.** Skill descriptions do this for skills. There is no index for `lessons/`, `changes/` or `evals/cases/`, and `/sdlc-maintain` reads every lesson file. | **Medium–high.** The clearest win. Unattended runs have budget and time limits, and `lessons/` only grows. | Low: a Python generator run in `/sdlc-deploy` step 0b, committed in the same PR as the lesson. |
| 14 | `log.md` | A dated change history per folder. | **Covered.** Git history, `PROGRESS.md` session records, dated amendments in DECISIONS and BUILD_GUIDE, and release notes. | **Low.** It would duplicate git. | Low |
| 15 | Tags as views | Tag views built by scanning frontmatter; no aggregation file. | **No.** Nothing carries tags yet. | **Low–medium.** Only matters together with rows 2 and 3, for lessons. | Low |
| 16 | Attested Computation | The sanctioned computation is fixed; the agent supplies only parameters, and deterministic code checks the run. | **Largely yes.** `commands.*` in `sdlc.yaml` are the sanctioned commands. `evidence/collect.py` runs them and writes a `# <command> — exit <code>` header. Runbooks run from `sdlc.yaml` without a shell; the agent only picks the route. The gate and policy checks are deterministic. | **Medium, as hardening:** check that each evidence log's command matches the base branch's `sdlc.yaml`. Unverified: whether the gate already does this. | Low–medium |
| 17 | Permissive conformance | Never reject a bundle for missing optional fields, unknown keys or broken links. | **Opposite, by design.** Gated artifacts fail closed: strict sections, and a YAML parser that won't silently turn off a guardrail. | **Low.** Keep strictness for gated artifacts. A minimal OKF-style check would suit lessons, which nothing validates today. | Low |
| 18 | Format version | `okf_version` at the bundle root. | **Partial.** JSON records carry `schema_version: 1`; plugin and prompt versions are pinned. Markdown files carry no format version, except the plugin version in the spec header. | **Low.** | Low |
| 19 | Git as governance | Knowledge is curated through PRs, diffs, blame and review. | **Yes, fully.** This is the framework's core: "the chain of commits is the audit trail." | Already done. | None |
| 20 | Format, not platform | Plain files any Markdown tool or LLM can read; no vendor lock-in. | **Yes, for the knowledge.** Artifacts are plain Markdown, YAML and JSON. The process is tied to GitHub (decision 23) and Claude Code, by design. | Nothing to add. | None |
| 21 | Sharing across teams and projects | Bundles move between organizations and tools unchanged: the "data sharing" in the article's URL. | **Only process knowledge.** Policy skills ship with the pinned plugin. Lessons, eval cases, dismissals and review memory stay inside each project; nothing collects them. | **Medium, grows with projects.** A lesson from one project (a flaky-test pattern, say) could inform diagnosis in another. | Medium–high: it needs a home outside the plugin, since the plugin must not hold project content. It touches decisions 8 and 9, so it is the owner's call. |
| 22 | Enrichment agent | An LLM drafts concepts from metadata, then enriches them from a bounded web crawl. | **No.** The researcher agent explores, but its findings aren't kept. | **Low.** Perhaps a "codebase bundle" at `/sdlc-init` one day. Web crawling in unattended runs raises security-baseline questions. | High |
| 23 | Graph visualizer | A self-contained HTML graph of concepts and their links. | **No.** | **Low.** Nice for browsing changes and lessons; the loop doesn't need it. | Low–medium: Python writing a static HTML file. |
| 24 | Knowledge Catalog serving | A runtime that ingests bundles and serves them to agents. | **No.** | **Low.** Out of scope for a GitHub-only framework whose repo is the source of truth. | High |
| 25 | Signals, not scores | Store raw signals such as usage counts; let each consumer judge. | **Yes, in one place.** `changes/.review-seen.json` counts repeat review findings; the second occurrence proposes a CLAUDE.md line. | Already consistent. | None |

The table was written against plugin 0.2.19. The framework is at 0.2.22/0.2.23 now; nothing in the rows was changed by those releases.

## Where the value is

The framework already follows OKF's thinking.[^analysis] It keeps knowledge in git-native Markdown, governs it through PRs, prefers deterministic checks to trusting the agent, and logs provenance in the spec header. Where it gates, it is stricter than OKF. Most gaps are about using one format everywhere, not about missing capability.

**The payoff is concentrated in `lessons/`.** It is the one corpus that grows without limit, is read by an unattended agent under a budget, and has no metadata, index or validation. OKF-style frontmatter, a generated `index.md`, a `status` and `stale_after`, and links to the change and eval case would be cheap to add. They pay off as soon as phase (f) runs live.

Cross-project sharing is the article's headline benefit and the open question here. It matters only when the framework runs on several projects, and it runs into decisions 8 and 9, which separate process content from project content. That makes it an owner decision, not a build step (see [Sharing lessons across projects](#sharing-lessons-across-projects)).

## A lesson file in OKF form

This is an invented incident written in today's `lessons/` shape, with the header line moved into OKF frontmatter.[^analysis] It uses a runbook the framework already ships (`quarantine-flaky-test`) and the first metric, CI failure rate (decision 15). The four body sections are exactly those of today's `template/lessons/README.md`.

`lessons/2026-10-order-total-timezone.md`:

```markdown
---
type: Lesson
title: Order-total test fails near UTC midnight
description: A test built "today" from the local clock, so CI runs crossing UTC midnight compared two different dates.
tags: [flaky-test, time, ci_failure_rate]
change: "0042"
detected: {at: 2026-10-03T00:40:00Z, metric: ci_failure_rate, tier: 3, rule: "1 point beyond 3 sigma"}
fixed: {at: 2026-10-05T16:20:00Z, pr: 57}
runbook: quarantine-flaky-test
generated: {by: sdlc-plugin/0.2.19, at: 2026-10-05T15:02:00Z}
status: stable
stale_after: 2027-10-05T00:00:00Z
sources:
  - id: detection
    resource: /changes/0042-order-total-timezone/evidence/detection.json
  - id: eval
    resource: /evals/cases/0042-order-total-timezone/
  - id: fix-pr
    resource: https://github.com/<owner>/<repo>/pull/57
---

# Order-total test fails near UTC midnight

## What happened
CI failure rate crossed 3 sigma on 2026-10-03 [^detection]. All failures were in
`test_order_total_includes_daily_discount`, and all ran between 23:55 and 00:05 UTC.

## Root cause
The test built "today" with `date.today()`, but the code under test uses UTC. Near
midnight the two disagree, so the discount was applied to the wrong day.

## Fix
The test now uses a frozen UTC clock. `quarantine-flaky-test` ran first and was the
right call: it kept main green while the fix went through PR #57 [^fix-pr].

## Prevention
Eval case added [^eval]. Proposed CLAUDE.md line: "Tests never read the wall clock;
use the frozen UTC clock fixture."

[^detection]: Detection record.
[^eval]: Eval case.
[^fix-pr]: Fix PR.
```

### Compared with today's format

- The prose header line (`Change: … · Detected: … · Fixed: …`) moves into frontmatter, so a script can read it without parsing prose.
- `description` and `tags` let `/sdlc-maintain` pick out relevant lessons without opening each file.
- `status` and `stale_after` let a lesson be retired once the code it describes is gone.
- `sources` with keyed footnotes keep citations correct when an agent rewrites the text on a fix round.
- There is no `verified` field. The owner's merge of the fix PR already records that, and the intent template says not to add approval lines.

### The index that goes with it

`lessons/index.md`:

```markdown
---
okf_version: "0.2"
---
# Lessons

## flaky-test
* [Order-total test fails near UTC midnight](/lessons/2026-10-order-total-timezone.md) - Test built "today" from the local clock; fails on runs crossing UTC midnight. Tier 3, Oct 2026.
* [Checkout test depends on test order](/lessons/2026-08-checkout-order.md) - Shared fixture mutated by an earlier test. Tier 2, Aug 2026.

## dependencies
* [Build broke on a transitive minor bump](/lessons/2026-09-lockfile-drift.md) - Unpinned transitive dependency; lockfile now enforced in CI. Tier 3, Sep 2026.

## Retired
* [Cache warm-up timeout](/lessons/2026-07-cache-warmup.md) - deprecated: the cache layer was removed in change 0038.
```

The index is generated from the lessons' frontmatter by a script, never edited by hand. Only a bundle's root index may carry `okf_version`;[^spec] the example treats `lessons/` as the bundle root. If `lessons/` is ever a subfolder of a larger bundle, its index drops the frontmatter block.

### How this changes /sdlc-maintain

Today it reads every lesson file. With the index, it reads one short page first, then opens only the lessons whose tags match the metric or rule in `detection.json`, plus any that look related. With 5 lessons the difference is small. With 80, it is the difference between a diagnosis that fits the run's budget and one that does not.[^analysis]

### What it would take for lessons

A small Python script that rebuilds the index; `/sdlc-deploy` step 0b writing the frontmatter and running that script in the same fix PR; and updates to the lesson shape in `template/lessons/README.md` and to the `/sdlc-maintain` prompt.[^analysis]

## Sharing lessons across projects

OKF's idea of sharing is simple: a bundle is a folder in an agreed format, so another team, project or tool can take it and read it without translation. The framework already splits its knowledge into two kinds (decision 8), and only one of them travels.[^analysis]

| Kind | Examples | Where it lives | Shared across projects? |
|---|---|---|---|
| Process knowledge | Policy skills, agents, review prompt, hooks, gate | The plugin | **Yes.** Every project pinned to the plugin gets it. |
| Project knowledge | `lessons/`, eval cases, dismissals, review memory, the project's `CLAUDE.md` | Each project's own repo | **No.** It never leaves that repo. |

**The consequence.** Say the framework runs on projects A, B and C. Project A learns that tests reading the local clock flake near midnight, and that lesson sits in A's `lessons/`. When B hits the same problem, B's `/sdlc-maintain` cannot see A's lesson and pays for the whole diagnosis again. Format is not what stops the lesson from traveling. Nothing moves it, and nothing reads across repos.

### Why it touches decisions 8 and 9

- **Decision 8 (sticky):** the plugin holds process, the template holds project content. The obvious shortcut, shipping shared lessons inside the plugin, is ruled out. CLAUDE.md says: "Never put project content in the plugin." Shared lessons would need a new home.
- **Decision 9 (reversible):** each project's repo is the source of truth for its own artifacts. A shared store would be a second place the same lesson lives, so the owner would have to say which copy wins. The natural answer: the project holds the original, the shared store holds a copy.
- **A practical limit.** The CI workflow token can only read its own repo. Reading a shared lessons repo from CI needs a token with wider access, such as the GitHub App that decision 5 keeps in reserve for when the built-in token's limits bite.

### The options

1. **Do nothing.** Right while the framework runs one project.
2. **Promote lessons to rules.** When the same kind of lesson appears in a second project, write it as a rule in a policy skill (for example, coding-standards: "tests never read the wall clock") through a normal plugin PR. Every pinned project then gets it. This fits decision 8 as it stands, needs no new mechanism, and captures most of the value.
3. **A shared lessons repo.** Each project's fix PR also sends a copy of the lesson there, and `/sdlc-maintain` reads its `index.md` read-only. This is where OKF's format pays off most, because lessons from different projects would share one shape. It needs the wider-access token and the owner's call on decision 9.

**Recommendation:** option 2 now; option 3 only once several projects run phase (f) live. Nothing needs deciding until a second project exists. If lessons are ever shared outside the owner's own projects, review them first: they can contain project details that the data-conventions rules would classify as internal.[^analysis]

## Context loading: should the often-loaded docs become an OKF-style reference?

The question: would turning the docs Claude loads all the time into an indexed, OKF-style reference keep the information but cost fewer tokens?[^analysis] The short answer is no for `CLAUDE.md`. It is already small, cheap to re-send, and holds exactly the rules that must always be present. The saving is in the large docs that sessions are told to read.

### What Claude Code loads, and when

Claude does not re-read these files on every prompt. It reads them once per session, then re-sends the whole context with every request. The unchanged start of that context is billed at the cache-read rate, 0.1× the normal input price. After `/compact`, the root `CLAUDE.md` is read from disk again and put back.[^analysis]

| When | What |
|---|---|
| Session start, kept all session | The system prompt. `CLAUDE.md` from the user folder, the project root and its parent folders, plus any `@path` imports (the docs indicate these load at launch, though no verbatim quote was found). Auto-memory `MEMORY.md`, up to the first 200 lines or 25 KB. Skill names and descriptions (about 100 tokens each). Subagent descriptions. MCP tool names only. SessionStart hook output. |
| Only when triggered | A `CLAUDE.md` in a subfolder, when a file there is read. `.claude/rules/` files with `paths:`, when a matching file is read. A skill's full `SKILL.md` when invoked, and its supporting files when read. Any doc Claude decides to read. |
| Survives `/compact` | Root `CLAUDE.md` and auto-memory, reloaded from disk. Recently invoked skills, up to 5k tokens each and 25k in total. Subfolder `CLAUDE.md` files and path-scoped rules do not survive; they are summarized away. |
| Headless `claude -p` | Loads `CLAUDE.md` and skills. `--bare` skips `CLAUDE.md`, hooks and plugins unless they are passed explicitly. Most subagents load `CLAUDE.md`; the built-in Explore and Plan agents don't. |

Official guidance is to keep each `CLAUDE.md` under 200 lines, asking of every line "would removing this cause Claude to make mistakes?". `/context` shows what is actually loaded.

### What that means for this repo

Sizes as measured at plugin 0.2.19.[^analysis]

| File | Size (at 0.2.19) | How it gets loaded |
|---|---|---|
| `CLAUDE.md` (root) | 56 lines, 4.7 KB (about 1.2k tokens) | Every session. Well under the 200-line guidance. |
| `template/CLAUDE.md` | 40 lines, 1.8 KB | A project's CI runs load it on the subscription-token path. With an API key the run uses `--bare`, so `CLAUDE.md` is likely not picked up (see [Open questions](#open-questions-still-unverified)). |
| 8 skill descriptions | About 100 tokens each | Every session. Full bodies (2.6 to 5 KB) load on demand. |
| `plugin/commands/*.md` | 5 to 15 KB each | On demand, when the command runs. |
| `docs/OPERATING_MODEL.md` | 50 KB | Not auto-loaded, but `CLAUDE.md` line 3 says "Read `docs/OPERATING_MODEL.md` first". |
| `docs/PROGRESS.md` | 137 KB, 366 lines | Read by build sessions from HANDOFF's "Read in this order" list. Lines 1 to 115 covered the current session; the rest was sessions 3 and 4. |
| `docs/NOTES.md` | 62 KB, 815 lines | Read for platform facts. |
| `docs/DECISIONS.md` | 29 KB | Read so decisions aren't reopened. |

The always-loaded part is about 2k tokens, and it is cached. HANDOFF's reading list points to specific sections, but a default Read returns the whole file. A build session that reads the four large files whole can take in up to about 60k tokens, most of it history it doesn't need.

### The answer

**Leave `CLAUDE.md` as it is.** It is 56 lines, cached, and survives compaction. Its content is always-needed rules ("never edit guardrails", "park, never page"), which should not depend on a fetch that might not happen. The repo already follows the "linter's job" advice: hooks and the gate enforce the rules, and `CLAUDE.md` only states them.

**Split the large docs into small files, each folder with an `index.md`.**

- `docs/NOTES.md` becomes `docs/notes/`: one file per platform fact, with `sources` (docs URL and verbatim quote), `generated.at` and `stale_after`, plus an `index.md`. The existing "re-verify when the Claude Code version moves" becomes a date check. This is the best candidate.
- `docs/DECISIONS.md` becomes one file per decision, with frontmatter such as `status: accepted` or `amended`, `reversibility: sticky` and `amended_by: 21`. The index has one line per decision, which is often enough to know what not to reopen.
- `docs/PROGRESS.md`: split the current session from the archive of earlier sessions.

Code comments and one runtime message cite `docs/NOTES.md` by section number (for example `plugin/ci/auth.py`, `plugin/hooks/_common.py`, `plugin/gate/limits.py`, `tests/test_ci.py`). The split keeps each section's number in its file name so those citations still resolve.

**Point to the indexes from `CLAUDE.md`.** Add a pointer line, for example "`docs/notes/index.md` lists every verified platform fact; read the matching note before relying on one". This is one step removed from Vercel's winning shape, which kept the index itself in the always-loaded file; the rule that `CLAUDE.md` fits on a page rules that out. A pointer relies on Claude following an instruction rather than on a skill being triggered, and the evidence favors instructions: ETH Zurich found them "well followed", and sessions here already follow line 3's "Read OPERATING_MODEL first".

`CLAUDE.md` is a guardrail file that a session never edits. The pointer line goes to the owner as an edit, once the split has merged:

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [CLAUDE.md](../../CLAUDE.md) | New line after line 3 | Line 3 ends "`docs/DECISIONS.md` records the 26 settled choices — do not reopen them without asking." Line 4 is blank. | Insert as line 4: "Indexes first: `docs/notes/index.md` lists every verified platform fact, `docs/decisions/index.md` every settled decision; read the index, then only the files you need." |

**In projects, the same logic applies to `lessons/`** (the example above). `/sdlc-maintain` reads the index first because its prompt says to, then opens only matching lessons.

### How to do it

Split the docs with the Edit tool, not a script: `CLAUDE.md` warns that the auto-mode classifier blocks a scripted rewrite whose payload reads like instructions. HANDOFF's reading list becomes "index first".

The saving is mostly attention and context space, not money. For unattended runs with budget and turn limits, those are the limits that matter.

## Evidence

Both research passes worked from search snippets, because direct page fetches were blocked. Abstract-level numbers agreed across several independent snippets. Figures marked ² appeared only in third-party write-ups.[^analysis]

| Side | Source | Finding |
|---|---|---|
| For | Anthropic, *Effective context engineering for AI agents* (Sep 2025) | Aim for "the smallest possible set of high-signal tokens" and load context "just-in-time". It describes Claude Code as a hybrid: `CLAUDE.md` is loaded up front, and grep and glob fetch the rest. |
| For | Anthropic, *Agent Skills* (Oct 2025) | Progressive disclosure: about 100 tokens of metadata always, a body under 5k tokens when the skill is triggered, and resources only when accessed. |
| For | Claude Code costs docs | Workflow-specific instructions in `CLAUDE.md` "are present even when you're doing unrelated work"; move them into skills. |
| For | Chroma, *Context Rot* (Jul 2025) | Across 18 models, performance gets "increasingly unreliable as input length grows", even on the same task. |
| For | Liu et al., *Lost in the Middle* (TACL 2024) | Accuracy drops when the relevant information sits in the middle of a long context. |
| For | IFScale (Jul 2025) | At 500 instructions, the best model scored 68% and claude-sonnet-4 scored 42.9%. Earlier instructions are favored. |
| For | HumanLayer, *Writing a good CLAUDE.md* | Keep it under 60 lines, with pointer files that each have a one-line description. "Never send an LLM to do a linter's job." |
| For | Karpathy's LLM Wiki; llms.txt; Claude's `MEMORY.md` | All share one shape: a short index read first, with detail pages opened as needed. |
| Against | Vercel, *AGENTS.md outperforms skills in our agent evals* (Jan 2026) | No docs: 53%. Skills: 53%, and "in 56% of cases, the skill was never used". Skills with explicit instructions: 79%. A compressed 8 KB docs index kept in AGENTS.md: 100%. When loading depends on the model choosing to fetch, it fails silently. |
| Against | Anthropic's skill-creator skill | Claude tends to "undertrigger" skills, so descriptions should be "a little bit pushy". |
| Against | Scott Spence, skill activation tests | Skills activated 20% of the time with plain instructions and 84% with a hook that forces an evaluation step. |
| Against | ETH Zurich, *Evaluating AGENTS.md* (Feb 2026) | Context files "do not generally improve task success rates" and raise cost "by over 20%". Overviews "are not helpful", but instructions in them "are well followed". It recommends "only minimal requirements". LLM-generated files lowered success by about 3%². |
| Against | Claude Code docs | Content loaded on demand (subfolder `CLAUDE.md` files, path rules) is summarized away at compaction; root `CLAUDE.md` is not. |
| Cost | Prompt-caching pricing | Cache reads cost 0.1× the input price. Removing a stable 1k-token file saves almost no money. The real costs are attention and context space. |

**Where the sources agree:** keep a short index that is always loaded, put the detail in small files, and don't rely on the model deciding whether to look. Vercel's 100% came from that shape. Its 53% came from skills that depended on being triggered.

## Open questions (still unverified)

- **Row 16:** whether the gate compares each evidence log's command against the base branch's `sdlc.yaml`. If it does not, that check is the hardening row 16 proposes.
- **Row 10:** whether the age of a runbook's `rehearsed_at` is enforced before decision 26's pre-approved rollback runs.
- **`CLAUDE.md` in `--bare` API-key phase runs** (the analysis's "Repo finding"). `plugin/ci/auth.py` adds `--bare` whenever `ANTHROPIC_API_KEY` is set. NOTES §10 and §13 record that bare mode "skips CLAUDE.md, hooks and plugins unless passed explicitly". `run_phase.py` passes `--plugin-dir` and `--settings`, so skills and hooks still load, but nothing passes the project's `CLAUDE.md`. The subscription-token path and the eval runner don't use `--bare`, so they load it. It matters less than it sounds, because the hooks and the gate enforce `CLAUDE.md`'s guardrails. A phase transcript in `evidence/claude-<phase>.json` would confirm it. Session 7 could not check it: every live run of the sample used the OAuth token, so no `--bare` transcript exists. It is filed under PROGRESS "Known gaps", not decided here.

## Decisions this touches

| Decision | How | Reopened? |
|---|---|---|
| 8 Framework distribution (sticky) | The plugin never holds project content, so shared lessons need a home outside it. | No |
| 9 Source of truth (reversible) | A shared store is a second copy; the project's is the original. | The owner's call, only if option 3 is taken |
| 17 Evals and lessons grow from incidents | Lessons get frontmatter and an index; they still grow only from incidents. | No, unchanged |
| 7 Python runtime, no runtime dependency | Every script proposed here is Python standard library. | No, unchanged |
| 20 Nothing pushes to the owner | Nothing here notifies; lessons ride in fix PRs as today. | No, unchanged |

Nothing is reopened by this proposal. Option 3 of the sharing question would need the owner's decision on 9 before any work starts.

## What it would take

Smallest first. Each step stands on its own.

1. **Frontmatter and an index for lessons and eval cases.** Frontmatter with `sources` on new lessons and eval cases; a `lessons/index.md` generator, `plugin/lessons/index.py` (Python, standard library), run by `/sdlc-deploy` step 0b in the same fix PR; `template/lessons/README.md` and the `/sdlc-maintain` prompt updated to read the index first. Files: `plugin/lessons/index.py` (new), `plugin/commands/sdlc-deploy.md`, `plugin/commands/sdlc-maintain.md`, `template/lessons/README.md`, `template/evals/README.md`, tests under `tests/`. Effort: one small plugin release.
2. **Freshness on platform facts and the docs split.** `status` and `stale_after` on NOTES facts; `docs/NOTES.md`, `docs/DECISIONS.md` and `docs/PROGRESS.md` split into small files with an `index.md` each; HANDOFF's reading list made index-first. Markdown only, split with the Edit tool and merged by the owner; the `CLAUDE.md` pointer line is the owner's own edit (the table above). Files: `docs/notes/`, `docs/decisions/`, `docs/PROGRESS.md`, the current HANDOFF. Effort: one session of editing, no code.
3. **The promote-to-rule practice.** One line in `docs/OPERATING_MODEL.md` §9: when the same kind of lesson appears in a second project, it becomes a policy-skill rule through a plugin PR. Files: `docs/OPERATING_MODEL.md`. Effort: one line.
4. **The shared lessons repo.** Only with a wider-access token (decision 5's reserve, the GitHub App) and the owner's decision on 9. Files: a new repository, the fix-PR step in `plugin/commands/sdlc-deploy.md`, the read step in `plugin/commands/sdlc-maintain.md`, a workflow token change. Effort: medium to high; not before several projects run phase (f) live.

Accepted through the normal front door: `changes/<id>-<slug>/intent.md`, `Entry route: idea`, `Framework change: yes`; the roadmap row then carries the change id.

[^blog]: Introducing the Open Knowledge Format (Google Cloud blog, 2026-06-12, v0.1).
[^spec]: OKF SPEC.md v0.2.
[^analysis]: OKF and the SDLC framework, the owner's thinking-session analysis of 2026-09-25 (plugin 0.2.19).
