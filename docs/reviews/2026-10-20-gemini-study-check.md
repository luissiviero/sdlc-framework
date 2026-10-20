# An independent check of the Gemini second-opinion study (2026-10-20)

The owner asked a fresh session (branch `ccr-6ed8a82e-cxmftx`) to answer the study's four questions from the repository and from Google's documentation **before** opening `docs/reviews/2026-10-20-gemini-second-opinion-study.md`, then to compare, one row per recommendation, without softening a disagreement. Report only; the owner's answers that followed are choice 246 in `docs/PROGRESS.md`.

## Method

Read before the study: ROADMAP R8, R28 and R62 and the proposals of R8 and R62; decisions 11, 12 and 21; `template/sdlc.yaml`; `plugin/ci/run_phase.py` `session_env` and `commands_env`; `plugin/ci/settings.ci.json`; the workflow templates. The session's own answers were written to its scratch folder before the study was opened.

Google's pages could not be opened from the container: `ai.google.dev` answers 403 at the proxy's `CONNECT` (and WebFetch fails on DNS). Every Gemini fact below is **read in search-result extracts of Google's pages, not verified**. No Gemini call was made: the container holds no key. The model ids are settled by `python plugin/external/cli.py models` on the owner's key (plugin 1.0.18) before any is written into `sdlc.yaml`.

## The session's own answers, in short

1. **Where it gains most:** gate (b), doubling the adversarial reviewer; then gate (e), doubling the REVIEW.md pass. (c) and (d) fold into (e), since nobody reads them before (e) under Standard. The panel's devil's advocate changes decision 21. (a) gains little.
2. **How to keep it read-only:** a step after the session with the key alone, no `tools`, the stateless `generateContent`, a JSON schema, the input built from git with the exclusions and a cap, and the answer treated as data that never reaches a later Claude prompt.
3. **Models:** `gemini-4-argon` for (b) and (e); `gemini-3.8-flash` for the cheap uses.
4. **GitHub:** the API cannot read a private repository; URL context reads public URLs only and is a tool. The runner sends the files.

## The study, recommendation by recommendation

| # | The study recommends | Verdict | Evidence | What to change |
|---|---|---|---|---|
| 1 | #290 departs from R8; undo its session part | **agree, and it goes further** | R8: "passed to that step's environment alone. The Claude session never sees it" (`docs/proposals/external-design-check.md`, "How it runs"). On `main` at `57b5a85`: `session_env` stripped nothing for Gemini, nine phase steps passed the key (`template/.github/workflows/sdlc-design.yml` and eight more), and `plugin/ci/settings.ci.json` listed `generativelanguage.googleapis.com` for every pinned project. | The larger risk is the owner's key itself: a session reads it with `python` and can push it into a commit or a PR body, since github.com is allowed; the study names only data leaving through the Gemini host. The study also leaves out the local host lines that #293 and #294 added to both `.claude/settings.json` files. |
| 2 | Rank 1: gate (b), doubling the adversarial reviewer | agree | R8's "The problem" (changes 0002 and 0003) | none |
| 3 | Rank 2: gate (e), doubling the review pass | agree | `sdlc-deploy.yml`, the review step before phase (e) | Run after the phase (e) step, on the head the owner merges. A call after the review step judges a head that phase (e) then moves. |
| 4 | Rank 3: the panel double, later, through a decision file that amends 21 | partly | Decision 21; R28 also amends 21 (its ROADMAP row) | One decision with R28's amendment of 21, not two in a row; on Argon, not Flash: the panel allows at most 4 calls a change (`template/sdlc.yaml`, `gate.max_panel_calls`), and it decides in the owner's name. |
| 5 | Rank 4: R62 as the safest first use | agree | `docs/proposals/docs-citation-reader.md` | none |
| 6 | Not for (a), (c), (d), the conciliator, the simplifier or the researcher | agree | `docs/OPERATING_MODEL.md` §4.1 | none |
| 7 | A runner step after the session; the input built from git; blind | **partly** | The deploy job distrusts what a session left: it removes the framework checkout and checks it out afresh before its second step (`sdlc-deploy.yml`, "Remove the framework checkout the session could reach"); the design job has no such step after its session. "The change folder" holds `evidence/adversarial-review-b.json`, `gate-b.json` and `decisions-b.md`. | A **job of its own** after the phase job, on a fresh runner that never held a session, with the key in its one step. The bundler leaves out the change's `evidence/`, or the second opinion is not blind. |
| 8 | Writes `evidence/external-review-<phase>.json` and a PR body section; "Gemini's text never enters a Claude prompt by itself" | **disagree on where the record goes** | A committed file under `changes/<id>/evidence/` is read by the next sessions (build, fix, the reviewer), and the commit moves HEAD past the one the gate judged. `pr/description.py` rewrites the PR body every round. A comment by the automation identity is "not applied" in a fix round (`plugin/commands/sdlc-fix.md`, step 1). | One PR comment by the workflow token, the job summary and the JSON as a workflow artifact; nothing committed. The rest agreed: no `tools`, a JSON schema, one request. |
| 9 | Never parks; "not run: <reason>" | agree | Decision 11 | none |
| 10 | `plugin/external/`: client (`generateContent`, "now called legacy"), bundler, briefs, record; usable by hand | partly | The "legacy" label was not found on a Google page *[later the same day: found in Google's cookbook; the study was right on the label, see "Google's own sources through other hosts"]*; the Interactions API is the one that keeps state on Google's side | Keep `generateContent` because it is stateless. The bundler reads **tracked content at the head** (`git show <sha>:<path>`), never the working tree. |
| 11 | `sdlc.yaml: external_review: {provider, model, phases}` | partly | One provider | `external_review: {model, phases}`; `max_chars` optional; absent means off. |
| 12 | R8's tally, decided after five changes | agree | R8's "How it is judged" | none |
| 13 | Order: the correction, then R62 or (b), (e), the panel | agree | — | none |
| 14 | `gemini-4-argon` for ranks 1 and 2, `gemini-3.8-flash` for 3 and 4 | partly | *[Later the same day: both ids found in Google's cookbook and SDK, below.]* Extracts of Google's model pages: Argon stable, GA on 2026-10-13, about 1M tokens; 3.8 Flash 1,048,576 in and 65,536 out. Cached copies of the models list disagree on the newest model. Not verified. | Argon for the panel too (row 4); the ids settled on the key before use. |
| 15 | Under $2 a change | agree | Same prices in the extracts: Argon $2 / $10 to 2026-11-30, then $4 / $20; 3.8 Flash $0.75 / $3.75 to 2026-12-31, then $1.50 / $7.50. Not verified. | none |
| 16 | Link billing before project code; "the paid tier excludes that" | **partly, a gap** | The extracts of the pricing and logging pages name a paid, invite-only **Contributor** tier that trades up to 50% off for Google's use of the data, and a **55-day** abuse-monitoring log on the paid tier that authorised staff may read | Add both: never accept the Contributor invite on the key's project; know the 55-day log. |
| 17 | Q4: the runner sends the bundle | agree | URL context: public URLs only, 20 a request, and a tool. One blog says the consumer Gemini Code Assist GitHub app stopped on 2026-07-17 (not verified); the enterprise one needs Google Cloud and posts its own reviews, so it writes. | none |
| 18 | Item 3: the Windows variable and the cloud secret, for calls by hand | **disagree** | A persistent Windows variable reaches every local Claude Code session; a cloud environment secret reaches every cloud session: #290's exposure on the PC and in the cloud | Neither persistently: the owner sets the key in one terminal window when running the client by hand. |
| 19 | Item 4: the sample's paste of the 1.0.17 file | **disagree, out of date** | The sample's `main` at `4a429c4` carries `version: 1.0.17` (sample #89, #90, #91) | The 1.0.18 pin with `external_review`, then the 1.0.18 workflow copies, and the sample's own secret if the owner wants Gemini there. |

## Google's own sources through other hosts (the owner's question, later the same day)

The owner asked why the study's session could read Google's pages. It could not: its "Method" says `ai.google.dev` failed on DNS and every fact came from search results, as here. The proxy denies `ai.google.dev`, `docs.cloud.google.com`, `blog.google`, `aistudio.google.com` and `policies.google.com`, and its rule is not to route around a denied host, so no relay or mirror was used. Three of Google's own sources on allowed hosts were read in full instead:
- **The Gemini API's discovery document** (`generativelanguage.googleapis.com/$discovery/rest?version=v1beta`, revision 20261019), the machine-readable contract of the REST API;
- **Google's cookbook** (`github.com/google-gemini/cookbook` at `5506746`, 2026-10-19) and **SDK** (`github.com/googleapis/python-genai` at `4c1abcc`, 2026-10-20), cloned as data;
- **The Vertex AI (Agent Platform) pricing page** on `cloud.google.com`.

What they settle:
- **The request's shape is right**: `generationConfig.responseMimeType`, `responseSchema` (an OpenAPI subset), `maxOutputTokens`; the answer's `modelVersion`, `usageMetadata` and `Part.thought`.
- **The model ids exist**: `gemini-4-argon` (the cookbook: "Our flagship frontier reasoning model built for complex software engineering"; thinking levels low, medium (the default), high) and `gemini-3.8-flash`, in Google's own code of 2026-10-19 and 2026-10-20. Whether the owner's key can call them is still the `models` command's to say.
- **The prices**: the Vertex page gives the extracts' figures ($2 / $10 for Argon until 2026-11-30, then $4 / $20; $0.75 / $3.75 for 3.8 Flash until 2026-12-31, then $1.50 / $7.50). That is Vertex's list, read in full; the Developer API's list was not.
- **Row 10 corrected**: Google's cookbook does call `generateContent` "the legacy `generateContent` API ... kept as a reference" and the Interactions API "the recommended way" (`quickstarts/Get_started_Generate_Content.ipynb`). The study was right on the label. The choice stands: the discovery document still serves `generateContent`, and the Interactions API keeps state on Google's side (`store=True` by default).

What they change in plugin 1.0.18 (made in #304):
1. **`store: false` on every request.** The discovery document lists a `store` field that "configures the logging behavior for a given request" and "takes precedence over the project-level logging config". Without it, a project with AI Studio logging on would keep the code sent in its logs, from which a dataset can be shared.
2. **A cut-off answer is named.** On a non-streaming `generateContent` call the output cap is 32,768 tokens, thinking included (the cookbook's migration guide for Argon), and an answer can stop with `MAX_TOKENS` or `CONTINUATION`. The record now says so instead of "the answer is not JSON". The cap stays at 32,768, the call's maximum, and no `thinkingLevel` is sent, so Argon thinks at its default, medium; "high" would spend 16K to 64K tokens of that cap on thinking (the same guide).
3. **The model's stage is recorded.** Each answer carries `modelStatus` (`STABLE`, `PREVIEW`, `LEGACY`, `DEPRECATED`, with a retirement time); the record keeps it and the comment names a stage other than `STABLE`.
4. **Longer timeouts.** The guide asks for client timeouts of 15 to 20 minutes for "high" thinking: the client now waits 900 seconds, and the job's limit is 20 minutes.

Still not read: the Developer API's terms and its logging page (the paid tier's terms, the Contributor tier, the 55-day abuse log) and the URL context page. Rows 16 and 17 rest on search extracts as before.

## Sources (search-result extracts, not opened)

- [Gemini API models](https://ai.google.dev/gemini-api/docs/models), [Gemini 4 Argon](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon), [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
- [Pricing](https://ai.google.dev/gemini-api/docs/pricing), [Data logging and sharing](https://ai.google.dev/gemini-api/docs/logs-policy), [Additional terms](https://ai.google.dev/gemini-api/terms)
- [URL context](https://ai.google.dev/gemini-api/docs/url-context)
- [Gemini Code Assist deprecation (blog, not Google)](https://kieranmaynard.com/blog/gemini-code-assist-deprecation.html)
