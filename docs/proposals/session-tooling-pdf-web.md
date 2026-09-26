---
type: Proposal
title: Session tooling for PDFs and web pages
description: How a Claude session on this repository reads a PDF and fetches a web page, adapted from a setup prompt the owner was given, and the OKF reading that makes most fetches unnecessary.
status: proposed
roadmap: R2
sources:
  - id: prompt
    resource: docs/handoffs/inputs/session-6-pdf-web-setup-prompt.md
    title: "The setup prompt the owner was given (2026-09-25); not run as written"
  - id: okf-spec
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
    title: "OKF SPEC.md v0.2, section 6.3 (the references/ convention)"
  - id: notes-1
    resource: docs/NOTES.md
    title: "NOTES section 1 (how Claude Code invokes hook commands) and section 15 (the facts read in session 7)"
  - id: session-7
    resource: docs/PROGRESS.md
    title: "The session-7 record: the environment facts verified on 2026-09-25"
generated: { by: sdlc-framework-session/7, at: 2026-09-25T23:30:00Z }
---

# Session tooling for PDFs and web pages

Sessions on this repository cannot read a PDF or fetch a web page today. The owner's thinking session of 2026-09-25 had to extract the blog post's PDF through `pypdf` in a virtual environment, and its two research sub-agents worked from search snippets because direct page fetches were blocked (the OKF analysis, `docs/proposals/okf-adoption.md`, says so in its evidence table). The owner was then given a setup prompt that installs Poppler through a bash hook, allows `WebFetch` and `WebSearch`, and adds a "Tooling rules" section to `CLAUDE.md` [^prompt]. This proposal adapts it to the repository's rules and states the OKF reading of the same problem, which is why it sits under R1 in `docs/ROADMAP.md`. Nothing here is implemented in session 7.

## What the session verified (2026-09-25, this cloud session)

Read once and recorded in `docs/NOTES.md` section 15 with the date [^session-7]:

| Question the prompt assumes an answer to | What this session found |
|---|---|
| Is Poppler there? | No: `pdftoppm`, `pdftotext` and `pdfinfo` are absent. The `Read` tool's PDF support needs `pdftoppm`, so a PDF given to `Read` fails today. `pypdf` is not installed either. |
| Can a hook install it? | `apt-get` exists and the session runs as root, but the permission mode denied `apt-get update` when the session tried it, and no fact says a SessionStart hook would be allowed what a Bash call was not. Unverified; the hook must never fail the session. |
| "The shell has no general internet access in cloud sessions (only package registries and GitHub)" | Partly true. Outbound HTTPS goes through the environment's proxy: `raw.githubusercontent.com`, `pypi.org` and the Google Cloud blog answered 200 to `urllib`; `en.wikipedia.org`, `code.claude.com` and `api.github.com` answered 403 from the proxy. So the reachable set is a policy list, not "registries and GitHub". |
| "Always fetch with the WebFetch tool" | Not possible here: this repository's `.claude/settings.json` denies `WebFetch`, `Bash(curl *)` and `Bash(wget *)` (the security baseline's rule, article p.37–38), and the `WebFetch` tool was absent from the session's tool list; `WebSearch` was present. `curl` was denied when tried. A `permissions.allow` entry never overrides a `deny` entry, so the prompt's allow list would change nothing until the deny list changes. |
| Does the GitHub API work? | Not through `urllib` (403 from the proxy); the GitHub MCP tools of the session do, as the owner's login (NOTES section 14). |

## The setup prompt, adapted

The prompt is the source, not the instruction. Each adaptation names the rule it follows.

**(a) The hook is Python.** `CLAUDE.md`: Python for every hook, no bash scripts; the owner works on Windows. The prompt's `.claude/hooks/ensure-pdf-tools.sh` becomes `.claude/hooks/ensure_pdf_tools.py`, registered in exec form (`command: python`, `args: [...]`, NOTES section 1: no shell on any platform) [^notes-1]. It installs `poppler-utils` through `apt-get` only where `apt-get` exists and the install is permitted, and never fails the session: every branch exits 0 and the whole body is one `try`. `pdftoppm` is the fix, because `Read` renders pages with it; `pypdf` (a `pip install` into the session, which does reach `pypi.org`) is only a text fallback for a session that cannot install Poppler.

```python
"""SessionStart hook: make sure Poppler (pdftoppm, pdftotext, pdfinfo) is there so the
Read tool can open a PDF. Silent, never fails the session, does nothing on a machine
without apt-get (the owner's Windows PC)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def main() -> int:
    try:
        if shutil.which("pdftoppm"):
            return 0
        if not shutil.which("apt-get"):
            return 0  # not Debian/Ubuntu: nothing to do here
        sudo = [] if os.geteuid() == 0 else (["sudo", "-n"] if shutil.which("sudo") else None)
        if sudo is None:
            return 0
        env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
        subprocess.run([*sudo, "apt-get", "update", "-qq"], env=env, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=100)
        subprocess.run([*sudo, "apt-get", "install", "-y", "-qq", "poppler-utils"], env=env,
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=100)
    except Exception:  # noqa: BLE001 - a hook that raises would fail the session
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**(b) Guardrail files are the owner's edit.** `.claude/**` and `CLAUDE.md` are guardrail files (decision 6; `CLAUDE.md` "Things Claude gets wrong"), so the hook registration, the permission entries and the "Tooling rules" section are given as edit tables, not committed by a session, and the prompt's "commit and push" step is dropped. The tables, in the owner's format:

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [.claude/settings.json](../../.claude/settings.json) | after the `permissions` block | no `hooks` key | `"hooks": {"SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "python", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/ensure_pdf_tools.py"], "timeout": 120}]}]}` |
| [.claude/settings.json](../../.claude/settings.json) | `permissions.deny` | `"WebFetch"`, `"Bash(curl *)"`, `"Bash(wget *)"` | unchanged for phases (b)–(f) (see (c)); for interactive and build sessions on this repository the owner decides whether `"WebFetch"` leaves the deny list — an allow entry alone changes nothing |
| [.claude/settings.json](../../.claude/settings.json) | `permissions.allow` | `Bash(git *)`, the three `python -m` rules | add `"WebFetch"`, `"WebSearch"` only if the deny entry above goes; otherwise add `"WebSearch"` alone |
| [.claude/hooks/ensure_pdf_tools.py](../../.claude/hooks/ensure_pdf_tools.py) | new file | none | the hook above (whether `${CLAUDE_PROJECT_DIR}` is substituted inside exec-form `args` the way NOTES section 1 records for `${CLAUDE_PLUGIN_ROOT}` is verified once when the owner applies the row) |
| [CLAUDE.md](../../CLAUDE.md) | a new section after "Things Claude gets wrong" | none | the "Tooling rules" section below |

The "Tooling rules" section, adapted from the prompt (one rule kept verbatim, see (e)):

```markdown
## Tooling rules
- PDFs: Poppler is installed by a SessionStart hook (`.claude/hooks/ensure_pdf_tools.py`). Text: `pdftotext -layout`; a page as an image (`pdftoppm -png -r 150`) only to see a chart or a figure. If `pdftoppm` is missing, run the hook once and retry; if it is still missing, `pip install pypdf` and extract the text.
- Web pages: fetch with the WebFetch tool when this repository allows it; never with curl, wget or a Python/Node HTTP library. The reachable hosts are the environment's policy list (docs/NOTES.md section 15), not the whole web.
- If a fetch is refused, list the refused URLs in the final report; tell sub-agents the same.
- When delegating research to sub-agents, tell them the rules above explicitly; never work from search snippets silently.
- Anything a session needs more than once is ingested into `docs/reference/` in a reviewed PR (docs/proposals/session-tooling-pdf-web.md); a session reads the mirror, not the network.
```

**(c) This repository only, never the template.** The allow entries belong to this repository's `.claude/settings.json` and not to `template/.claude/settings.json`: phases (b)–(f) run unattended with `--permission-prompts none`, and a fetched page inside an autonomous run is a prompt-injection path the security baseline closes (`plugin/skills/security-baseline`, rule 7: no outbound call except the allowed domains; `WebFetch`, `curl` and `wget` denied; the researcher agent is Read/Grep/Glob for the same reason). At most the interactive phase (a) in a project could fetch, and that is the project owner's setting, not the template's default.

**(d) Environment claims are facts to verify, not to copy** (`docs/NOTES.md` is where a platform fact lives, with its source and date; PROGRESS choice 93). The prompt's "no general internet access" and "always WebFetch" were checked once in this session and recorded in `docs/NOTES.md` section 15 with the read date (the table above). Any later session reads the note instead of re-testing, and re-tests only when the note's date is older than the environment's last change.

**(e) One rule kept verbatim:** "if a fetch is refused, list the refused URLs in the final report; tell sub-agents the same." The prompt's validation step ("fetch a Wikipedia page with WebFetch and confirm it returns content") is replaced by that rule, because the fetch is refused here today.

## The OKF reading: mirror once, read files

OKF's `references/` convention mirrors external material into the bundle as first-class concepts, with `sources`, `generated.at` and `stale_after` in the frontmatter, and consumers read files, never the network [^okf-spec]. This repository already does that for its one standing input: `docs/reference/ai-native-sdlc-playbook.txt` is the page-tagged text of the article, cited by PDF page from every doc and prompt, and no session has ever fetched the PDF. So the proposal's rule is:

1. **Any PDF or page a session needs more than once is ingested** in a reviewed PR into `docs/reference/<slug>.md` (in a project: `references/<slug>.md`) with the frontmatter `type: Reference`, `title`, `sources` (the URL or the file, its `last_modified` when known), `generated: {by, at}` and `stale_after` (a date after which the mirror is re-read against its source). The blog post and the OKF spec of R1 are the first two candidates; `docs/reference/index.md` lists the mirrors with one line each.
2. **Poppler and `WebFetch` are ingestion tools** for interactive and build sessions on this repository, not for phases (b)–(f), which stay offline by the security baseline.
3. **One-off research keeps the live fetch**, where the settings allow it, and the refused-URL rule of (e).

Cost: an ingestion is a normal PR the owner reviews, so a mirrored page is read once by a person before any session relies on it, which is the same review the security baseline asks of any input to an unattended run.

## Decisions this touches

| Decision | How | Reopened? |
|---|---|---|
| 6 (where the guardrails live) | `.claude/settings.json` and `CLAUDE.md` stay owner-edited; the tables above are proposals | No |
| 7 (Python for every hook, no runtime dependency) | The hook is Python and standard library; Poppler is a session tool, not a runtime dependency of the plugin | No |
| 23 (GitHub only) | Unchanged; the GitHub API is read through the session's tools, not `urllib` | No |
| The security baseline (skill; article p.37–38) | Phases (b)–(f) keep the deny list; only this repository's interactive sessions may fetch | No |
| 5 (the workflow token; a GitHub App in reserve) | Unchanged | No |

Nothing is reopened.

## What it would take

1. The owner applies the edit tables of (b) (two files, one new hook file), about ten minutes; a session then verifies once that `Read` opens `docs/reference/ai-native-sdlc-playbook.pdf` and records the result in NOTES section 15.
2. `docs/reference/index.md` and the frontmatter on the existing mirror (one PR by a session: two small files, no code).
3. The ingestion rule as one line in `docs/OPERATING_MODEL.md` section 8 (conventions) and the "Tooling rules" section of `CLAUDE.md` (owner edit).
4. Optional, later: the first two mirrors of R1's sources (the blog post, the OKF spec) once R1 is accepted.

Accepted through the normal front door: `changes/<id>-<slug>/intent.md`, `Entry route: idea`, `Framework change: yes`; the roadmap row then carries the change id.

[^prompt]: The setup prompt the owner was given, kept as `docs/handoffs/inputs/session-6-pdf-web-setup-prompt.md`.
[^okf-spec]: OKF SPEC.md v0.2, section 6.3.
[^notes-1]: `docs/NOTES.md` section 1: a command hook with `args` runs in exec form, no shell on any platform.
[^session-7]: `docs/PROGRESS.md`, session 7, and `docs/NOTES.md` section 15, the entries dated 2026-09-25 (session 7).
