# Gemini as a second opinion in phases (a) to (e): a study and its recommendations (2026-10-20)

The owner asked, after the Gemini key reached the phase runs (PR #290, plugin 1.0.17): can Gemini be read-only, and where in phases (a) to (e) should it double the Claude roles as a second opinion, never as a substitute? Four questions: which tasks gain most from a second opinion, how to build it, which Gemini model fits each task, and whether Gemini can read the repository from GitHub or must be sent the files. Report only; nothing was built. The owner will have a fresh session check these recommendations before anything is implemented.

## Method

One session (branch `ccr-8b4eb57f-uy0e8e`), the one that built #290. Read: ROADMAP R8 and `docs/proposals/external-design-check.md`, R62 and `docs/proposals/docs-citation-reader.md`, R28's row, the comment on `panel_advocate_model` in `template/sdlc.yaml`, `plugin/ci/run_phase.py` `commands_env` and `session_env`, `plugin/ci/settings.ci.json`. The Gemini facts come from web searches limited to Google's domains (`ai.google.dev`, `blog.google`, `docs.cloud.google.com`, `discuss.ai.google.dev`), with third-party pages where Google's own pages were not in the results. `ai.google.dev` could not be opened from the session's container (DNS lookup failed), so no Google page was read in full; every model fact below is "read in search results, not verified". No Gemini call was made: the key is not in the session's environment.

## A correction first: #290 departs from R8

R8 (written at the owner's request on 2026-10-09) puts the key in "a GitHub Actions secret (`GEMINI_API_KEY`), passed to that step's environment alone. The Claude session never sees it: the session's environment is built without it, and a test proves that." The step is the runner's, after the model's session, outside the sandbox.

#290 did the opposite: every step that runs a model hands the session `GEMINI_API_KEY`, and the CI sandbox allows `generativelanguage.googleapis.com` for every project pinned to 1.0.17. The session that built it did not read ROADMAP first. Two consequences:

- **Data can leave through the new host.** Any project on 1.0.17 can reach the Gemini host from the session, with or without a key: a manipulated session could upload content with someone else's key through the Files API. `api.anthropic.com` already opens a channel of that kind; #290 adds a second one that a project without Gemini does not need.
- **Gemini's answer reaches the session.** A session that calls Gemini itself reads the answer as part of its own context, so a second opinion is neither blind nor kept apart from the work it judges.

**Recommendation:** take R8's shape and undo #290's session part: the secret only in the runner step's environment, `GEMINI_API_KEY` stripped from the session's environment with a test, and the host removed from `plugin/ci/settings.ci.json`. This replaces the owner's item "the Gemini host only when the key is set" with something stronger: the host is never in the session's sandbox.

## 1. Which tasks gain most from a second opinion

Every judge today is a Claude model; R7 spreads them over two versions (Fable 5.1 designs, Opus 5.5 reviews) of one vendor. The template says why that matters: "a panel reduces variance, not bias: three judges on one model share its blind spots" (`template/sdlc.yaml`, the comment above `panel_advocate_model`). A model of another vendor helps most where the work is reading and judging, and where a missed problem costs most later.

| Rank | Where | The Claude role it doubles | Why |
|---|---|---|---|
| 1 | **Gate (b): the design** (`intent.md`, `spec.md`, `plan.md`, the files the plan lists) | The adversarial reviewer | A design gap found at (b) costs one review round; found at (e) it costs a build. Changes 0002 and 0003 passed the in-run reviewer and still needed two or three review rounds at (b) (R8's proposal, "The problem"). This is R8 as written. |
| 2 | **Gate (e): the build diff**, before the owner's review | The (e) review pass (`REVIEW.md`, decision 12) | Gate (e) is the owner's last gate before the merge; a second reader of the code (correctness, security, the plan's conformance against the diff) is the next largest gain. R8 leaves "other phases" to its tally; this study recommends (e) as the next one. |
| 3 | **Panel items** (decision 21) | A second devil's advocate, blind to the other two verdicts | Answers the template's own remark above. It changes the panel's ledger, the `panel_blind` hook and what the conciliator reads, so it needs a decision file that amends 21; after ranks 1 and 2 have a tally. |
| 4 | **This repository's docs pull requests** | None (R62, a new reader) | Small value per run, but the safest first live use: a public repository, nothing to disclose, no Claude tokens. It proves the client, the secret and the record before a project's code is sent anywhere. |

Not recommended:
- **(a) the intent:** the owner writes it.
- **(c) and (d):** the verifier runs the code, which Gemini cannot do here; rank 2 reads the tests against the acceptance criteria.
- **The conciliator:** it decides; a second decider blurs who decided.
- **The code-simplifier and the researcher:** little that a second opinion would change.

## 2. How to build it

- **A deterministic runner step, not a tool of the session.** It runs after the model's session and its gate, like the commands step since 0.3.0. The runner builds the input from git (the merge base, the head, the change folder), so Claude neither chooses nor sees what Gemini reads, and Gemini never sees Claude's verdict: blind, as the panel's two verdicts are.
- **Read-only by construction.** One request: a brief, the files, a JSON response schema. No `tools` field (no function calling, no code execution, no URL context, no search). The runner validates the answer against the schema and writes `evidence/external-review-<phase>.json` (the provider, the model id the API reports, the verdict, one line per concern with the file and the claim, the tokens, the time) and a "Second opinion" section in the PR body. Nothing else is written. Gemini's text never enters a Claude prompt by itself; the owner carries a real concern into a "Request changes" review, as with any finding.
- **It never parks** (decision 11 unchanged) and is not a panel member (decision 21 unchanged until rank 3). A failed call (no key, an outage, a quota, a timeout, a refusal, the cost ceiling) is recorded as "not run: <reason>", and the job stays green.
- **The key in that step alone** (above), with a test that the session's environment never holds it.
- **One small module**, Python with the standard library (decision 7), for example `plugin/external/`:
  - the HTTPS client, one function, so a later move from `generateContent` (stateless; Google now calls it "legacy" but fully supported) to the Interactions API stays local;
  - the bundler, with a size cap and the `.env*` and `secrets/` exclusions of the settings' deny rules, plus the secrets hook's patterns;
  - the briefs, taken from the adversarial reviewer's attack angles (R7's seventh angle included);
  - the record.

  The same client can run as a command for by-hand use: that is the owner's "read-only wrapper" item.
- **Turned on by the owner** in `sdlc.yaml` (decision 6), as R8 proposes, with the phases added: for example `external_review: {provider: gemini, model: <id>, phases: [b, e]}`. Absent means off, so no other project changes.
- **Judged by R8's tally:** for each change, did the second opinion raise a concern that proved real and that the in-run reviewer had not named? After five changes the owner keeps it advisory, promotes it (a new decision) or drops it.
- **Order:** the #290 correction; then R62 or gate (b) as the first live use; then gate (e); then the panel double with its decision file.

## 3. Which Gemini model

Read in search results of Google's pages on 2026-10-20, not verified (see Method). The key's own model list (`GET /v1beta/models`) settles the ids before any is written into `sdlc.yaml`.

| Model | Status (as read) | Price per 1M tokens, input / output (thinking billed as output) | Context | Recommended for |
|---|---|---|---|---|
| `gemini-4-argon` | Stable, announced 2026-10-13 as generally available; **not on the free tier** | $2 / $10 until 2026-11-30, then $4 / $20 | about 1M | **Ranks 1 and 2**: Google's flagship for complex software work, and only a few calls per change |
| `gemini-3.8-flash` | Stable, 2026-09-02 | $0.75 / $3.75 until 2026-12-31, then $1.50 / $7.50 | about 1M in, 65K out; thinking levels low, medium, high | **Ranks 3 and 4**: more calls, less at stake |
| `gemini-3.1-pro-preview` | Preview | $2 / $12 | about 1M | Not recommended: Argon supersedes it, and preview ids are shut down (Gemini 3 Pro Preview was) |
| Flash-Lite (3.5, 3.1) | Stable | about $0.25 to $0.30 input | | Not recommended: too weak for a review |

**Cost estimate, not measured:** a review at (b) or (e) of about 100K tokens in and 10K out (thinking included) is about $0.30 on Argon at the introductory price and $0.60 after it, so under $2 a change. The record keeps the tokens of every call; the design states a per-change ceiling.

**The terms decide whether project code may be sent.** As read: on the free tier Google may use prompts and responses to improve its products, and human reviewers may read them; the paid tier excludes that, and the data terms follow whether billing is linked on the key's Google project. Argon is paid only. R8's open row "read the terms of the key's tier before the first call" is answered this way: link billing on the key's project before any project code is sent.

## 4. Can Gemini read the repository from GitHub?

Not reliably. Gemini's URL context tool reads public URLs only, at most 20 per request (as read on Google's URL context page), and Google's developer forum reports it as hit or miss on GitHub pages. A private project, or a branch at a given commit, would not work. With a context of about 1M tokens, sending the bundle is easy: the diff, the change folder, the files the plan lists, `CLAUDE.md`, `REVIEW.md`. **The runner sends it, not Claude**, so the input is deterministic, the session cannot shape Gemini's prompt, and the key stays out of the session.

## The owner's four items, as this study sees them

| Item | This study's reading |
|---|---|
| 1. The Gemini host only when the key is set | Replaced by the #290 correction: the host off the session's sandbox for everyone; the runner step calls Gemini outside it |
| 2. The read-only wrapper | The client module above, also runnable by hand |
| 3. The Windows variable and the cloud environment secret | The owner's settings; with the runner design, needed only to call the wrapper by hand |
| 4. The sample | The owner's paste of the 1.0.17 file the 5953b5a0 session prepared; the sample gets Gemini only when its `sdlc.yaml` turns `external_review` on |

## What the owner settles before anything is built

1. Take R8's shape and undo #290's session part (the key and the host)?
2. R8's place: it now starts after R7 is measured on two changes, Order 46 in ROADMAP. Now, or there?
3. Phases: (b) and (e) first, the panel double later through a decision file that amends 21?
4. Is billing linked on the key's Google project (the paid tier)?

## Sources

- [Gemini API models](https://ai.google.dev/gemini-api/docs/models)
- [Gemini 4 Argon, model page](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon)
- [Gemini 4 Argon: Built to solve your hardest problems](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-argon/)
- [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms_preview)
- [Data logging and sharing](https://ai.google.dev/gemini-api/docs/logs-policy)
- [Developer's guide to Gemini 3.8 Flash](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash)
- [Gemini 3.1 Pro](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-pro)
- [Gemini 3 developer guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- [URL context](https://ai.google.dev/gemini-api/docs/interactions/url-context.md.txt)
- [Does URL context even work? (forum)](https://discuss.ai.google.dev/t/does-url-context-even-work-can-you-fix-it/91770)
- [Structured outputs](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
- [Migrating to the Interactions API](https://ai.google.dev/gemini-api/docs/migrate-to-interactions)
- [Free tier vs paid tier after billing activation (forum)](https://discuss.ai.google.dev/t/clarification-on-gemini-api-free-tier-vs-paid-tier-after-billing-activation/96995)
- [Gemini API pricing, October 2026 (benchlm.ai)](https://benchlm.ai/google/api-pricing)
- [Gemini 4 Argon: benchmarks, pricing and access (DataCamp)](https://www.datacamp.com/blog/gemini-4-argon)
- [Gemini 3.8 Flash (OpenRouter)](https://openrouter.ai/google/gemini-3.8-flash)
