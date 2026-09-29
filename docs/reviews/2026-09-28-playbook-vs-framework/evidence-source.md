# Evidence: the live article against the PDF in docs/reference/

> Whether the article text audited here (the 2026-09-02 print in `docs/reference/`) still matches the live page fetched on 2026-09-28.

## Bottom line

**The live article is the same as the audited text, except for these points:**
1. **A new "Prefer a PDF?" download box** now sits at the top of the article body, just before "Code is no longer the bottleneck". Live text: "Prefer a PDF? This playbook is also available for download — the same six stages, plays, and worked examples, laid out for reading offline or sharing with your team. Download the PDF ↓". PDF p.1–2 have nothing like it. It links to a designed PDF, `AI Native SDLC Playbook_designv2 (1).pdf`. Its Webflow asset id `6aba7363…` decodes to an upload time of 2026-09-28 14:02:11 UTC, which fits the page's JSON-LD `"dateModified": "Sep 28, 2026"`. The box adds no playbook content.
2. **The title's capitalisation changed.** PDF p.1 (h1, breadcrumb and PDF metadata title) reads "The AI-**Native** SDLC playbook". The live h1, `<title>`, og:title and JSON-LD headline read "The AI-**native** SDLC playbook". The body text used "AI-native" in both versions.
3. **"Reading time" is not a real change.** It shows "46 min" on PDF p.1 and "5 min" in the fetched HTML. The "5" is a static placeholder: an inline script replaces it at load time with the word count ÷ 250. Running the same count on today's HTML gives about 11,631 words, or roughly 47 min.

Nothing else changed in the article itself: headings, prose, table, code, figures, captions, resources and acknowledgments are all the same, so the other auditors' page-cited conclusions hold for the live article. The only other differences are page chrome outside the article. The "Related posts" list has different posts on each date (PDF p.50–51 vs the live list), and the live page adds "Ask questions about this page" and "Copy as markdown" under "Explore here".

## Method (scripts and outputs in a scratch folder of the session, not kept)
- **Live article text:** I parsed `page.html` into blocks (h1–h4, p, li, td/th, figcaption, pre, div) from the h1 to the acknowledgments. That gives 952 sentences, 72 headings, 13 `<pre>` blocks and 4 `<img>`. The script is `html_blocks.py` and the output is `blocks.json`.
- **PDF text:** I extracted the text with PyMuPDF and removed the repeated page chrome ("/ The AI-Native SDLC playbook", Blog, Explore here, Contact sales, Try Claude). I also cut the related-post cards and the site footer (p.50 "Related posts", the p.51 cards, p.52–53). That gives 835 sentences.
- **Comparisons:**
  - Sentences, both directions (`cmp.py`). A sentence counts as matched when its normalised form (lower case, punctuation removed) appears in the other text. I then aligned each unmatched sentence word by word against its best match in the other text (`resid2.py`) and reviewed every one by hand.
  - Whole-article bag of words (`cmp.py`).
  - Code blocks line by line with punctuation kept: all 148 of 148 live code lines appear verbatim in the PDF.
  - Heading order.
  - The provided `textdiff.txt`, classified block by block (`classify2.py`, `cat.py`).
- **Bag of words, live minus PDF:** only the words of the "Prefer a PDF?" box and the Copy-link URL, plus three URLs that wrap in the PDF (`sett ings`, `integra tions`, `c ompliance` on p.51).
- **Bag of words, PDF minus live:** only these items:
  - the table-of-contents numbers "01…09" (p.4);
  - numbered-list markers "1."–"8.", about 90 in total;
  - "46" from the reading time;
  - one repeated table header "STAGE TRADITIONAL SDLC AI-NATIVE SDLC" at a page break (p.6);
  - invisible clipped glyph fragments at the foot of p.17 and p.29 ("h hif i f h hi h k h di", "di h f h l"; Type3 font, y≈764–778, not visible in the page image).

## Claims checked

| id | claim | verdict | evidence | severity | suggested correction |
|---|---|---|---|---|---|
| A0-1 | Live body prose = PDF prose | MATCH | All 952 live sentences are in the PDF except 40. Of those 40, 4 belong to the new PDF box or the Copy-link URL. The other 36 are layout splits, each resolved by word alignment: text interleaved by a page break or side box, or hyperlink text that the print moved (for example "Claude Code" p.2, "plan mode" p.15, "MCP" p.18, "hook" p.23, "git worktree"/"subagent" p.24, "Code Review"/"claude-code-action" p.33, "Claude Tag"/"Agent SDK" p.43, "Claude Security" p.45, "Stage 5: Deploy"/"Stage 1: Plan" p.46). All 70 PDF-only sentences are the same kinds of interleaving. | – | – |
| A0-2 | Headings/sections identical and in same order | MATCH | Live has 72 h1–h4 headings; each is found in the PDF in the same order. Stage headings: Plan p.9, Design p.12, Build p.15, Test p.26, Deploy p.32, Maintain p.41. "Plays" p.7, "Closing thoughts" and "Resources and acknowledgments" p.50. The table of contents has the same 9 entries (live list; PDF p.4 prints them as "01–09"). | – | – |
| A0-3 | Stage-comparison table identical | MATCH | Live has 3 th and 18 td. Every cell is found in the PDF on p.5–6. The only difference is the header repeated at the page break: "STAGE TRADITIONAL SDLC AI-NATIVE SDLC workshops and sign-offs, written up by hand" (p.6). | – | – |
| A0-4 | Code examples identical | MATCH | 13 `<pre>` blocks, 148 lines; each line is verbatim in the PDF text, including `cron: '0 2 * * *'` (p.30), `exit 2` in production-gate.sh (p.36), `permissions.deny` (p.37) and bands.yaml (p.44). | – | – |
| A0-5 | Title | PARTIAL | PDF p.1: "The AI-Native SDLC playbook". Live h1 and `<title>`: "The AI-native SDLC playbook". | LOW | Quote the live title as "The AI-native SDLC playbook". |
| A0-6 | Reading time | MATCH (not a content change) | PDF p.1: "Reading time 46 min". Fetched HTML: `<div data-readtime="minutes">5</div>`. The inline script sets `minutesElement.textContent = Math.round(wordCount / wordsPerMinute)` with wordsPerMinute = 250. Recomputed on today's HTML it gives about 47. | – | – |
| A0-7 | New "Prefer a PDF?" box | UNSUPPORTED in PDF (new on live) | Live `<div class="sd-pdf">` is the first element of the article body and links to `…/6aba736348bdf4f08183f463_AI%20Native%20SDLC%20Playbook_designv2%20(1).pdf`. It is absent from PDF p.1–2. | LOW | None needed. Know that a designed PDF ("designv2") now exists, with its own page numbering. It is not the print we cite. |
| A0-8 | The designv2 PDF can be compared | UNVERIFIED | `curl -I` to cdn.prod.website-files.com returns "CONNECT tunnel failed, response 403" through the proxy (the CDN is blocked). Its contents and page numbers are unknown. Artifact "p.N" citations refer to the 2026-09-02 print, not to designv2. | LOW | If readers will use the designv2 PDF, map page numbers to it later. |
| A0-9 | Figure 1 = PDF p.3 | MATCH | Live img `6a8739a1…_44592f18.png` sits after the 3-bullet list ("…meet weekly or monthly.") and before "Let's use a security bottleneck…". Its figcaption is "Build is no longer the constraint — the human-speed steps around it are. Human-speed stages keep their length while build collapses to hours." PDF p.3 has an image (1400×538 px) directly after "…meet weekly or monthly." with the same caption below it. | – | – |
| A0-10 | Figure 2 = PDF p.5 | MATCH | Live img `6a8858c2…_53b010df.png` (`max-width:2048px`) sits after "You'll also hear this shift called…" and before the h3 "The shifts across the six stages of an AI-native SDLC". It has no figcaption. PDF p.5 has an image (2048×1296 px) after the same paragraph and before the same heading, also uncaptioned. | – | – |
| A0-11 | Figure 3 = PDF p.8 | MATCH | Live img `6a8855c7…_5d5a3c05.png` (`max-width:2048px`) sits after "First, you prompt each step by hand…from scratch." and before the "01 Plan" stage header. Its figcaption is "The plays are listed with stage; the arrows give the order to adopt them in. The two are not the same. Start with any clay play — nothing points into it, so it needs nothing first. For any other play, the arrows pointing into it are the plays to adopt before it." PDF p.8 has an image (2048×1638 px) after the same paragraph with the same caption. | – | – |
| A0-12 | Figure 4 = PDF p.49 | MATCH | Live img `6a8760ad…_fe6d780d.png` (`max-width:1400px`) sits after "…See: how Claude Tag runs on-call for CI/CD at Anthropic." and before the h2 "Closing thoughts". Its figcaption is "The channel is the audit trail: request, diagnosis, human authorization and fix all stay where the incident was handled." PDF p.49 has an image (1400×637 px) after the same paragraph; the caption runs onto the top of p.50 (y=31). | – | – |
| A0-13 | Exactly 4 content figures, same assets | MATCH (asset identity inferred) | The article rich-text contains exactly 4 `<img>`. There are 0 picture/srcset/iframe/video/canvas elements. The 2 inline `<svg>` are aria-hidden icons in the two "sd-key" callout boxes. All 4 figures have `alt=""` on live. The pixel widths in the PDF (1400, 2048, 2048, 1400) match the live max-widths (none, 2048, 2048, 1400). The asset-id timestamps decode to 2026-08-20 17:30, 2026-08-21 13:55, 2026-08-21 13:42 and 2026-08-20 20:16 UTC, all before the 2026-09-02 print. This is an inference: I could not download the images (CDN 403). | – | – |
| A0-14 | `docs/reference/ai-native-sdlc-playbook.txt` = PDF text with correct page tags | MATCH | 53 of 53 `===== PAGE n =====` sections. The word bag of every page section equals the PyMuPDF words of the same PDF page, except for the artifacts in A0-15. No section matches a different page better. Spot checks, verbatim on the same PDF page: p.6 "who asked for what, what the agent produced, and who approved it."; p.7 "Each play names its dependencies under "Prerequisites," which the dependency graph further illustrates."; p.8 "Start with any clay play — nothing points into it, so it needs nothing first."; p.16 "The plan joins the audit trail, and the PR review play (Stage 5:"; p.33 "Findings do not approve or block a PR on their own, and branch protection still requires approval from a code owner."; p.42 "A trigger such as a control-band breach, a ticket, a channel message or a schedule invokes Claude without a person in the path."; p.43 "The script is version controlled and unit tested, and detection stays entirely deterministic, with no model involved."; p.44 "When a fix ships, add an eval for the incident…"; p.45 "When the post-deploy 5xx rate breaches 3σ with a deployment in the window, the agent triggers the existing rollback pipeline."; p.49 "Any team member can test hypotheses…". p.9 and p.13 hold the same words but differ in hyphenation or reading order only. | – | – |
| A0-16 | `textdiff.txt`: 184 blocks | MATCH (all 184 are print/layout artifacts, none substantive) | See the classification below. Every word a block adds or removes is found elsewhere in the other text (a move), or is a list or number marker, a case change, a whitespace or glued-label change, hidden glyphs, or site chrome. The three real header differences (A0-5, A0-6, A0-7) fall outside textdiff's range, which starts at "Code is no longer the bottleneck". | – | – |

### A0-15 (LOW): Extraction artifacts in the .txt that matter when quoting it
- **Hyphens lost at PDF line breaks:**
  - "processheavy" (txt line 76, p.2)
  - "nonlinear" (324, p.7)
  - "versioncontrolled" (389 and 430, p.9–10; 2354, p.49)
  - "protospec" (389, p.9)
  - "autoaccept" (796, p.17)
  - "regressiontested" (1216, p.26)
  - "nonnegotiable" (1694, p.36)
  - "postmortem" (2025, p.42)
  - "preapproved" (2088, p.43)
  - "contextdependent" (2308, p.48)
  - "oncall" (2359, p.49)

  The PDF and the live page both have these words hyphenated: "process-heavy", "non-linear", "version-controlled", "proto-spec", "auto-accept", "regression-tested", "non-negotiable", "post-mortem", "pre-approved", "context-dependent", "on-call".
- **Uppercase labels split into letters** (for example "T R A D I T I O N A L", "WO R K E D E X A M P L E") on p.4, 9, 13, 15, 24, 27, 32, 37–39, 42, 46.
- **Page chrome glued into sentences:**
  - lines 377–378: "…captured / Blog / The AI-Native SDLC / playbook once, … as a versionExplore here / controlled artifact…"
  - also lines 468, 907, 998, 1504–1505, 1856, 1954, and run-ons such as "theTry" and "BlogDesign".

Suggested correction: quote the article from the PDF page image or from live.txt when a hyphen matters. The page tags are right.

## textdiff.txt classification (all 184 = (a) print/layout artifact)

| category | what it is | blocks |
|---|---|---|
| A | The print moves hyperlink text out of the sentence to a stray line; the list number at a box boundary goes with it | 1, 2, 15, 33, 43, 54, 55, 56, 74, 76, 77, 83, 117, 130, 150, 162, 166, 167, 170 |
| B | Table-of-contents placement: the PDF prints "TABLE OF CONTENTS 01…09" and puts the entry titles later, mid-sentence | 3, 4 |
| C | Table header repeated at the p.5→6 page break | 8 |
| D | Label glued in live.txt ("TraditionalAn", "AI-nativeThe", "SidebarLegacy", "ExampleManaged", "termspermissions.deny"), stage badge "05", "Stage 5: Deploy / Stage 1: Plan" link text | 11, 24, 35, 53, 79, 91, 114, 115, 136, 137, 138, 141, 149, 164, 168 |
| E | Side boxes reordered: Getting started / Prerequisites / Infrastructure / How to execute it / How to measure it (Leading/Lagging indicator) / What is enforced / What the evidence is, plus the prose they interleave with | 7, 12, 13, 14, 16, 17, 20, 21, 22, 25, 26, 28, 32, 36, 37, 38, 39, 40, 41, 42, 50, 51, 57, 58, 61, 64, 65, 66, 69, 70, 73, 75, 82, 87, 88, 89, 92, 93, 94, 99, 100, 102, 103, 108, 116, 121, 124, 125, 126, 127, 128, 129, 134, 139, 142, 143, 144, 146, 147, 151, 152, 156, 160, 161, 169, 177, 178, 179, 181 |
| F | Numbered-list markers "1."–"8." and stage badges "01Plan…06" | 9, 18, 19, 27, 29, 30, 31, 44, 45, 46, 47, 48, 49, 59, 60, 62, 67, 68, 71, 72, 84, 85, 86, 95, 96, 97, 98, 104, 105, 106, 107, 112, 118, 119, 120, 122, 123, 131, 132, 133, 153, 154, 155, 157, 158, 159, 171, 172, 173, 174, 175, 176 |
| G | Invisible clipped glyph fragments at page foot (p.17, p.29) | 52, 101 |
| H | "Related posts / Explore more product news…" site chrome on PDF p.50 in place of the p.49 figure caption position | 183, 184 |
| I | Case, whitespace or punctuation only ("STAGE TRADITIONAL SDLC" vs "Stage Traditional SDLC", "Leading indicator Share" vs "Leading indicatorShare", "See: ." vs "See:") | 5, 6, 10, 23, 34, 63, 78, 80, 81, 90, 109, 110, 111, 113, 135, 140, 145, 148, 163, 165, 180, 182 |

## Top findings (non-MATCH, ranked)
1. **LOW, A0-7/A0-8: a new designed PDF exists.** Since 2026-09-28 (the asset upload time, which matches the page's dateModified), the live article opens with a "Prefer a PDF? … Download the PDF ↓" box linking to `AI Native SDLC Playbook_designv2 (1).pdf`. That PDF could not be fetched (CDN 403), so its page numbers are UNVERIFIED. Every "p.N" citation in the artifacts and reports refers to the 2026-09-02 Chrome print in `docs/reference/`, not to designv2.
2. **LOW, A0-5: title case.** The live title is "The AI-native SDLC playbook"; the PDF and CONTEXT.md have "The AI-Native SDLC playbook". Cosmetic.
3. **LOW, A0-15: the reference .txt drops hyphens at line breaks and glues page chrome into a few sentences.** Examples: "versioncontrolled", "oncall", "postmortem", "preapproved"; "as a versionExplore here" on p.9. Page tags are correct on all 53 pages. Verify verbatim quotes that contain hyphenated words against the PDF image or live.txt.

(A0-6, "46 min" vs "5 min", is not a finding: the 5 is a placeholder that JavaScript replaces.)
