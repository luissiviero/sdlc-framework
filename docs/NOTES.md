# Notes — platform facts verified against the Claude Code docs

Everything here was read on 2026-09-19 from the official docs at `code.claude.com/docs`
(and the pages named). Quotes are verbatim. Re-verify when the plugin's minimum Claude Code
version moves; the container that built session 1 ran Claude Code 2.1.278.

## 1. How Claude Code on Windows invokes hook commands (handoff deliverable 3; decision 7)

Source: https://code.claude.com/docs/en/hooks (sections "Command hook fields" and "Exec form
and shell form").

- "A command hook runs as exec form when `args` is set, and shell form when `args` is
  omitted."
- "**Shell form** runs when `args` is absent. The `command` string is passed to a shell:
  `sh -c` on macOS and Linux, Git Bash on Windows, or PowerShell when Git Bash isn't
  installed. Set the `shell` field to choose explicitly."
- "**Exec form** runs when `args` is present. Claude Code resolves `command` as an executable
  on `PATH` and spawns it directly with `args` as the argument vector. There is no shell, so
  each `args` element is one argument exactly as written, and path placeholders like
  `${CLAUDE_PLUGIN_ROOT}` are substituted into `command` and into each `args` element as
  plain strings. ... No shell tokenization happens on any platform."
- "On Windows, exec form requires `command` to resolve to a real executable such as a `.exe`.
  The `.cmd` and `.bat` shims that npm, npx, eslint, and other tools install ... can't be
  spawned without a shell."
- Paths: "For the file tools `Write`, `Edit`, and `Read`, `tool_input.file_path` is always
  absolute ... On Windows, the path arrives with backslash separators, even when your hook
  runs under Git Bash ... Normalize separators before comparing: ... `file_path.replace("\\",
  "/")` in Python".
- Blocking: "Exit 2 means a blocking error. On events that can block, exit 2 blocks whether
  or not you print JSON". "Without valid JSON on stdout, Claude Code treats exit code 1 as a
  non-blocking error and proceeds with the action ... If your hook is meant to enforce a
  policy, use `exit 2`."

**Chosen way to run the Python hooks:** exec form, `"command": "python"` with the script
path in `args` via `${CLAUDE_PLUGIN_ROOT}` (see `plugin/hooks/hooks.json`). No shell on any
platform, no quoting, no dependence on Git Bash versus PowerShell. Consequences:
- `python.exe` must be on `PATH` on the owner's PC (the python.org installer and the Store
  alias both provide it); Linux runners and cloud sessions provide `python` too. If a machine
  only has `python3`, change the `command` field once in `hooks.json`.
- The scripts import nothing outside the standard library and the plugin itself, so a missing
  package can never turn a guardrail into a non-blocking error. Policy hooks fail closed
  (exit 2 on any exception); the formatter hook fails open.
- `${CLAUDE_PLUGIN_ROOT}` is also exported as an environment variable to hook processes, and
  is substituted inline in plugin skill and command content and in their `allowed-tools`
  (https://code.claude.com/docs/en/plugins-reference#environment-variables,
  https://code.claude.com/docs/en/skills). The commands call
  `python "${CLAUDE_PLUGIN_ROOT}/state/cli.py" ...` on that basis.
- The `if` field narrows a handler by permission rule ("`if` | no | Permission rule to narrow
  execution (e.g., `"Bash(git *)"`)"); the plan-sync hook uses `Bash(git commit *)` and a
  PowerShell twin because "On Windows without Git Bash ... Claude Code doesn't register the
  Bash tool at all."

Live check still owed (needs a Windows machine): one `/sdlc-init` run on the owner's PC with
the plugin loaded, then an attempted edit of `.claude/settings.json` must show the
"Protected path" denial. The unit tests prove the scripts' behaviour with Windows-style
paths; they cannot prove the spawn on Windows.

## 2. Does the current documentation allow CI authentication with a Max subscription? (decision 1)

Read only; nothing was built on it.

- https://code.claude.com/docs/en/github-actions: "`CLAUDE_CODE_OAUTH_TOKEN`: an OAuth token
  that authenticates with your Claude subscription, available on Pro, Max, Team, and
  Enterprise plans. Generate one by running `claude setup-token` locally." and "If you
  authenticate with a Claude subscription, replace the `anthropic_api_key` line in any example
  with `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`."
- https://code.claude.com/docs/en/authentication: "For CI pipelines, scripts, or other
  environments where interactive browser login isn't available, generate a one-year OAuth
  token with `claude setup-token`" ... "This token authenticates with your Claude
  subscription and requires a Pro, Max, Team, or Enterprise plan."
- https://code.claude.com/docs/en/headless: "Bare mode does not read `CLAUDE_CODE_OAUTH_TOKEN`.
  If your script passes `--bare`, authenticate with `ANTHROPIC_API_KEY` or an `apiKeyHelper`
  instead."
- https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md: "OAuth Token
  Authentication - For Claude Pro and Max users only".
- https://code.claude.com/docs/en/agent-sdk: "Unless previously approved, Anthropic does not
  allow third party developers to offer claude.ai login or rate limits for their products" —
  about products offered to other users, not about the owner's own CI.

**Answer:** the product documentation explicitly supports subscription authentication for
GitHub Actions and headless `claude -p` runs via `claude setup-token`. Not verified: the
consumer terms of service pages were not reachable from the build container (proxy 403/404),
so B3 should re-read them before choosing the token over an API key. Also noted: "For a
secret shared across repositories, authenticate with an API key ... since an OAuth token is
tied to the subscription of the person who ran `claude setup-token`."

## 3. Where the framework runs: owner's PC and Claude Code cloud sessions

Source: https://code.claude.com/docs/en/cloud-environments ("What carries over from your
setup").

- "Cloud sessions start from a fresh clone of your repository. Anything you commit to the
  repo is available. Anything you've installed or configured only on your own machine isn't
  available in the session."
- Repo `.claude/settings.json` hooks and permission rules: "Yes, in a session with one
  repository". "Plugins declared in `.claude/settings.json` | Yes | Installed at session start
  from the marketplace you declared."
- "Settings deployed to your device through MDM or managed settings files don't apply,
  because the session runs on an Anthropic-managed VM".
- "GitHub's `gh` CLI is pre-installed ... `gh` reads `GH_TOKEN` automatically"; some remote
  sessions expose GitHub MCP tools instead. `/sdlc-plan` therefore tries `gh`, then a GitHub
  MCP tool, then prints the compare URL.
- `CLAUDE_CODE_REMOTE=true` identifies a cloud run.

Consequence: a project pins and loads the plugin through its own `.claude/settings.json`
(`extraKnownMarketplaces` → `github: luissiviero/sdlc-framework`, `enabledPlugins:
{"sdlc@sdlc-framework": true}`), written by `/sdlc-init`. That works identically on the PC
and in the cloud. Note: "Claude Code honors entries in a repository's `.claude/settings.json`
... only after you accept the workspace trust dialog for that folder; in a folder you haven't
trusted, including a `-p` run there, it ignores them without a message."

## 4. The managed-settings keys and what they do to decision 6

Source: https://code.claude.com/docs/en/settings-reference,
https://code.claude.com/docs/en/managed-settings.

- `allowManagedPermissionRulesOnly` (Scope: Managed): "Claude Code then ignores `allow`,
  `ask`, and `deny` rules in user, project, local, and `--settings` files, ignores
  `--allowedTools`, hides the always-allow choices in permission prompts, and stops saving
  new rules."
- `allowManagedHooksOnly` (Scope: Managed): "`true`: only managed hooks run, plus Agent SDK
  hooks and hooks from plugins your managed settings force-enable" ... "Force-enabled plugin
  hooks run: hooks from plugins your managed settings force-enable through `enabledPlugins`.
  Claude Code matches on the full `plugin@marketplace` ID" ... "Everything else is blocked:
  user, project, and local hooks, hooks from other plugins, and hooks declared in agent
  frontmatter".
- `permissions.disableBypassPermissionsMode` (Scope: Any file): "Claude Code then rejects
  the `--dangerously-skip-permissions` flag, and ignores an agent definition's
  `permissionMode: bypassPermissions`".
- File locations: Windows `C:\Program Files\ClaudeCode\managed-settings.json` ("Claude Code
  doesn't read the legacy Windows path `C:\ProgramData\ClaudeCode\managed-settings.json`"),
  Linux and WSL `/etc/claude-code/managed-settings.json`, macOS `/Library/Application
  Support/ClaudeCode/managed-settings.json`; Windows registry alternatives under
  `HKLM\SOFTWARE\Policies\ClaudeCode` and the user-writable `HKCU\...`.
- Precedence: managed settings > command line > `.claude/settings.local.json` >
  `.claude/settings.json` > `~/.claude/settings.json`; "Environment variables aren't a level
  in this stack."

Consequences (documented in `docs/owner-machine/README.md`, applied in
`docs/OPERATING_MODEL.md` section 8): the file is machine-wide and must carry the permission
rules and force-enable the plugin; `~/.claude/settings.json` cannot hold these keys; the file
is a guard against the agent, not against the owner (who administers the machine).

## 5. Sandbox

Source: https://code.claude.com/docs/en/sandboxing. "The sandbox is built into Claude Code
and runs on macOS, Linux, and WSL2. Native Windows is not supported." "By default, if the
sandbox cannot start because dependencies are missing or the platform is unsupported, Claude
Code shows a warning and runs commands without sandboxing. To make this a hard failure
instead, set `sandbox.failIfUnavailable` to `true`." The template therefore sets `enabled:
true`, `failIfUnavailable: false`, `allowUnsandboxedCommands: false` ("sandbox where
available"); the article's `failIfUnavailable: true` (p.37) would stop Claude Code from
starting on the owner's PC.

## 6. Permission rule facts the template depends on

Source: https://code.claude.com/docs/en/permissions.

- "A `Read` deny rule also blocks the Edit and Write tools on the same path, including
  creating a new file there. NotebookEdit isn't covered, so add an `Edit` deny rule for paths
  no tool may change."
- "Claude Code checks file permissions against `Edit(path)` and `Read(path)` rules only. If
  you write a path rule for `Write`, `NotebookEdit`, `Glob`, or the legacy `MultiEdit` tool
  instead, Claude Code accepts the rule but never consults it" — so the template uses
  `Edit(...)` deny rules only (a test asserts no `Write(...)` rule).
- "Read and Edit deny rules apply to Claude's built-in file tools, to file commands Claude
  Code recognizes in Bash, such as `cat`, `head`, `tail`, `sed`, and `tee`, and to the targets
  of Bash redirections such as `> file`" but "They don't apply to ... arbitrary subprocesses
  that read or write files indirectly, like a Python or Node script that opens files itself.
  For OS-level enforcement that blocks all processes from accessing a path, enable the
  sandbox." — the same gap applies to the protected-path hook, which sees file tools only.
- "Rules are evaluated in order: deny, then ask, then allow."

## 7. Plugin distribution facts

Source: https://code.claude.com/docs/en/plugins, /plugins-reference, /plugin-marketplaces.

- Manifest `.claude-plugin/plugin.json` with `name`, `version`, `description`, `author`;
  default component directories `commands/`, `skills/`, `agents/`, `hooks/hooks.json`.
  "Plugin skills are always namespaced (like `/my-first-plugin:hello`)" — the commands are
  therefore invoked as `/sdlc:sdlc-init` and `/sdlc:sdlc-plan` when installed from the
  marketplace.
- "Setting `version` means users only receive updates when you change this field, so bump it
  on every release." (marketplace entry and `plugin.json` both carry `0.1.0`; a test keeps
  them equal).
- Local development: "Run Claude Code with the `--plugin-dir` flag to load your plugin."
  Caveat: with the plugin loaded in place from this repo, the protected-path hook protects the
  plugin's own files, so edit the framework in a session without the plugin loaded (or from
  a marketplace-cached copy).
- "**Commands** and **Skills** use the same mechanism now. For new workflows, prefer
  **skills** ... Commands remain supported for single-file prompts." The repo keeps
  `plugin/commands/` as `CLAUDE.md` prescribes.
- Not found in the docs: whether one slash command can invoke another. `/sdlc-init` therefore
  says "generate one the way `/init` does (use the `init` skill if it is available ...)".

## 8. Known gaps carried to B2/B3

- A `Bash` command that writes a protected file through a script is not seen by the
  protected-path hook or by `Edit` deny rules (section 6); the sandbox and the review pass
  (REVIEW.md framework rules) are the remaining nets until the gate check of step 16 exists.
- Skill triggering ("test that it triggers", step 10) and the PR-opening step need a live
  model / GitHub; see `docs/PROGRESS.md`.
