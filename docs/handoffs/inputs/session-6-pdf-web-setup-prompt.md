Set up this repo so every Claude session (1) can read PDFs and (2) fetches web pages the right way. Do all steps, then report back in at most 3 bullets.

## 1. PDF reading: SessionStart hook that installs Poppler

Create `.claude/hooks/ensure-pdf-tools.sh` with exactly this content, and make it executable (`chmod +x`):

```bash
#!/usr/bin/env bash
# Ensures Poppler (pdftoppm, pdftotext, pdfinfo) is available so Claude can read PDFs.
# Runs silently at session start. Never fails the session.

command -v pdftoppm >/dev/null 2>&1 && exit 0     # already installed
command -v apt-get  >/dev/null 2>&1 || exit 0     # not Debian/Ubuntu (e.g. Windows PC): skip

SUDO=""
[ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo -n"

{
  $SUDO apt-get update -qq &&
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq poppler-utils
} >/dev/null 2>&1 || true

exit 0
```

Register it in `.claude/settings.json` (the shared, committed file, not `settings.local.json`). Merge into any existing `hooks` and `permissions` blocks; do not remove anything already there:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/ensure-pdf-tools.sh\"",
            "timeout": 120
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": ["WebFetch", "WebSearch"]
  }
}
```

The `permissions.allow` entries let subagents fetch pages without stopping for approval.

## 2. Rules in CLAUDE.md

Add this section to the repo's `CLAUDE.md` (create the file if missing):

```markdown
## Tooling rules

- PDFs: Poppler is installed by a SessionStart hook. For text use `pdftotext -layout`; render a page with `pdftoppm -png -r 150` only when you need to see a chart or figure. If `pdftoppm` is missing, run `.claude/hooks/ensure-pdf-tools.sh` once, then retry.
- Web pages: always fetch with the WebFetch tool. Never use curl, wget, or Python/Node HTTP libraries for web pages; the shell has no general internet access in cloud sessions (only package registries and GitHub).
- When delegating research to subagents, tell them the rule above explicitly.
- If WebFetch is refused for a page, do not work from search snippets silently: list the refused URLs in the final report so the user can open or attach them.
```

## 3. Validate

- `bash -n .claude/hooks/ensure-pdf-tools.sh`, then run the script and confirm exit code 0.
- Confirm `.claude/settings.json` is valid JSON (e.g. `python3 -m json.tool`).
- Confirm `which pdftoppm` succeeds.
- Fetch https://en.wikipedia.org/wiki/Poppler_(software) with WebFetch and confirm it returns content.

## 4. Commit

Commit the changed files with the message `Add PDF tooling hook and web-fetch rules for Claude sessions` and push.
