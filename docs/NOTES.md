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
- `python` must resolve on `PATH` wherever hooks run (check with `python --version` on the
  PC; the build container and cloud sessions have it). If a machine only has `python3`,
  change the `command` field once in `hooks.json`.
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

Live check still owed (needs a Windows machine; PROGRESS live-check item 6): one `/sdlc-init`
run on the owner's PC with the plugin loaded, then an attempted edit of `.claude/settings.json`
must show the "Protected path" denial. The denial itself passed in a cloud session (section 3a);
`python tasks.py check` passed on Windows on 2026-09-21; only the hook spawn by Claude Code on
Windows is unproven.

## 2. Does the current documentation allow CI authentication with a Max subscription? (decision 1)

The research below (2026-09-19) was read-only; the arrangement applied on 2026-09-21 follows it.

- https://code.claude.com/docs/en/github-actions: "`CLAUDE_CODE_OAUTH_TOKEN`: an OAuth token
  that authenticates with your Claude subscription, available on Pro, Max, Team, and
  Enterprise plans. Generate one by running `claude setup-token` locally." and "If you
  authenticate with a Claude subscription, replace the `anthropic_api_key` line in any example
  with `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`."
- https://code.claude.com/docs/en/authentication: "For CI pipelines, scripts, or other
  environments where interactive browser login isn't available, generate a one-year OAuth
  token with `claude setup-token`" ... "This token authenticates with your Claude
  subscription and requires a Pro, Max, Team, or Enterprise plan."
- https://code.claude.com/docs/en/authentication: "Bare mode does not read `CLAUDE_CODE_OAUTH_TOKEN`.
  If your script passes `--bare`, authenticate with `ANTHROPIC_API_KEY` or an `apiKeyHelper`
  instead." (the sentence is on the authentication page, not the headless page)
- https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md: "OAuth Token
  Authentication - For Claude Pro and Max users only".
- https://code.claude.com/docs/en/agent-sdk: "Unless previously approved, Anthropic does not
  allow third party developers to offer claude.ai login or rate limits for their products" —
  about products offered to other users, not about the owner's own CI.

**Answer:** the product documentation explicitly supports subscription authentication for
GitHub Actions and headless `claude -p` runs via `claude setup-token`. Not verified: the
consumer terms of service pages were not reachable from the build container (proxy 403/404),
so the terms themselves remain unread; the product docs are what the framework relies on. Also noted: "For a
secret shared across repositories, authenticate with an API key ... since an OAuth token is
tied to the subscription of the person who ran `claude setup-token`."

**Applied on 2026-09-21 (step 3's credential arrangement, within decision 1; the step itself
closes on a green smoke run):** the CI runs accept either credential, and the choice is made
from usage data, not in advance.

- **Subscription token** (`claude setup-token` → repository secret `CLAUDE_CODE_OAUTH_TOKEN`):
  nothing to pay beyond the plan; the docs support it for Pro (quotes above). Its cost is the
  plan window: "If you authenticate with an OAuth token, runs use your Claude subscription
  instead of API billing" (https://code.claude.com/docs/en/github-actions), so every
  unattended phase run competes with the owner's own sessions for the same window and cannot
  be capped in dollars; the token expires after one year ("generate a one-year OAuth token
  with `claude setup-token`", https://code.claude.com/docs/en/authentication); and it is not
  read in bare mode (section 2 above), so a token run is `claude -p` without `--bare`.
  Generating the token spends no quota; only the runs that use it do.
- **API key** (Console → repository secret `ANTHROPIC_API_KEY`): billed per token in dollars
  on top of the plan, isolated from every plan window, and capped twice
  (https://platform.claude.com/docs/en/manage-claude/workspaces,
  https://code.claude.com/docs/en/cli-reference): a dedicated Console workspace with the key
  scoped to it — "Spend limits: Cap monthly spending for a workspace. Set these on the
  workspace's Spend limits settings tab", "You cannot set limits on the Default Workspace",
  "API keys can be scoped to a single workspace" — and, per run, `--max-budget-usd`: "Maximum
  dollar amount to spend on API calls before stopping (print mode only). Spend from subagents
  counts toward the cap ... the cap-enforcement behaviors require Claude Code v2.1.217 or
  later" (a client-side estimate; the workspace limit is the authoritative one). What a
  request gets when the workspace cap is reached is not documented. Bare mode, "useful for CI
  and scripts where you need the same result on every machine", reads only the key: "In bare
  mode, Claude Code never reads OAuth credentials or the system keychain. For the Anthropic
  API, set `ANTHROPIC_API_KEY` in the environment" (https://code.claude.com/docs/en/headless);
  and "In non-interactive mode (`-p`), the key is always used when present"
  (https://code.claude.com/docs/en/env-vars), so when both secrets exist the key wins.

Order decided with the owner: start with the token (session 3's first live runs are few and
launched by hand), read `/usage` after them, and move to the key once the merge-triggered
jobs run unattended or the window shows the strain. Every workflow the framework ships
therefore takes both secrets and prefers the key: `.github/scripts/substrate_smoke.py` is
the pattern (`--bare` only on the key path), and B3's `plugin/ci/run_phase.py` follows it.
The consumer terms were not read from the build container (above); the product docs support
the token for Pro, which is what the framework relies on.

Owner setup (not automatable from the repo):
1. Token path: on the PC, `claude setup-token`, approve in the browser, copy the printed
   token → GitHub → each repository the framework drives (`sdlc-framework`,
   `sdlc-sample-python`) → Settings → Secrets and variables → Actions → new repository
   secret `CLAUDE_CODE_OAUTH_TOKEN`.
2. Key path, when the time comes: Console → Settings → Workspaces → Create workspace
   `sdlc-ci`, set a monthly cap and an alert on its Spend limits tab; create an API key scoped
   to it; store it as the repository secret `ANTHROPIC_API_KEY` in the same repositories.
   The token secret can stay; the key takes precedence.
3. In `sdlc-framework`, run the dispatch-only workflow `substrate-smoke.yml` (Actions →
   "Substrate smoke test" → Run workflow); it installs the pinned CLI from npm
   (`npm install -g @anthropic-ai/claude-code@2.1.278`, on Node 22 as the setup page
   requires; the curl installer with `bash -s <version>` is the documented alternative) and
   runs `.github/scripts/substrate_smoke.py`: `claude -p [--bare] --model opus --max-turns 2
   --max-budget-usd 0.25 --output-format json <prompt>` (`--bare` on the key path only; on the
   token path the turn draws on the owner's Opus window), then prints `auth`, `total_cost_usd`,
   the model names from `modelUsage` and the reply. Exit codes: 2 when neither secret is set,
   1 when the CLI exits non-zero, reports `is_error` or returns no JSON, 0 on success. A green
   run closes build guide step 3.
   The script is unit-tested with a fake CLI (`tests/test_substrate_smoke.py`); the workflow
   was not executed in the session that added it (no Actions runner there). Its key-path
   command line was dry-run locally on CLI 2.1.278 with an invalid key: the flags parsed, the
   JSON result carried `total_cost_usd`, `result`, `is_error` and `modelUsage`, and the CLI
   exited 1 with `api_error`.

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
- "GitHub's `gh` CLI is pre-installed ... `gh` reads `GH_TOKEN` automatically". Observed in
  the session that built this repo (Claude Code on the web, 2026-09-19): no `gh` binary, GitHub
  reached through `mcp__github__*` tools instead. `/sdlc-plan` therefore tries `gh`, then a
  GitHub MCP tool, then prints the compare URL.
- `CLAUDE_CODE_REMOTE=true` identifies a cloud run.

Consequence: a project pins and loads the plugin through its own `.claude/settings.json`
(`extraKnownMarketplaces` → `github: luissiviero/sdlc-framework`, `enabledPlugins:
{"sdlc@sdlc-framework": true}`), written by `/sdlc-init`. That works identically on the PC
and in the cloud. Note (settings-reference, `extraKnownMarketplaces` entry): "Claude Code
honors entries in a repository's `.claude/settings.json` or `.claude/settings.local.json`
only after you accept the workspace trust dialog for that folder; in a folder you haven't
trusted, including a `-p` run there, it ignores them without a message." Allow rules follow
the same trust gate (permissions page: "What runs before you trust a folder"); deny rules
apply immediately. Consequence for B3: a headless `claude -p` run in a fresh checkout does
not install the plugin from the project's settings by itself; the CI job must load the pinned
plugin explicitly (`--plugin-dir` on the checked-out framework) — which is layer (iii) of
decision 6 anyway.

### 3a. Observed on 2026-09-20: the cloud session did not install the declared plugin

First live run on `luissiviero/sdlc-sample-python` (Claude Code 2.1.278, Claude Code on the
web). `claude plugin list` printed "No plugins installed"; the debug log said:

```
Skipping orphaned enabledPlugins entry sdlc@sdlc-framework: marketplace not registered
installPluginsForHeadless: no marketplaces declared
```

and stderr: "Ignoring 4 permissions.allow entries from .claude/settings.json: this workspace
has not been trusted. Run Claude Code interactively here once and accept the trust dialog, or
set projects["/home/user/sdlc-sample-python"].hasTrustDialogAccepted: true in
/root/.claude.json."

Cause, from https://code.claude.com/docs/en/permissions ("What runs before you trust a
folder"): repository `extraKnownMarketplaces` entries are "Not used, and no dialog is
offered" in the two untrusted situations, and "Claude Code shows the trust dialog in
interactive sessions only. A `claude -p` run or an SDK session never shows it". A cloud
session behaves like the latter, so the "Yes" in the cloud-environments table (§3 above)
holds only once the folder counts as trusted.

Documented remedies: "For the rows that need this exact folder trusted, trust it by hand:
set `projects["<path>"].hasTrustDialogAccepted` to `true` in `~/.claude.json`", or register
and install explicitly: "Claude Code provides non-interactive `claude plugin marketplace`
subcommands for scripting and automation" (`claude plugin marketplace add <owner/repo>`),
and "In a non-interactive shell, such as a provisioning script, pass `--yes` to
`claude plugin install`". Cloud environments run a **setup script** "when a new cloud
session starts, before Claude Code launches", and the environment cache keeps what it
installs.

**Chosen remedy for cloud sessions** (owner configures once, in the environment dialog at
claude.ai/code):

```
claude plugin marketplace add luissiviero/sdlc-framework
claude plugin install sdlc@sdlc-framework --yes
```

The project's `.claude/settings.json` declaration stays: it is what a trusted local session
uses, and it documents the pin. For B3 (`claude -p` in GitHub Actions) the same applies: the
workflow either runs those two lines or loads the checked-out framework with `--plugin-dir`.

Confirmed on 2026-09-21 with the setup script in place: `claude plugin list` shows
`sdlc@sdlc-framework`; the debug log reads `Read manifest hooks for plugin sdlc
(enabled=true): ./plugin/hooks/hooks.json` and `Registered 5 hooks from 2 plugins`; the
cloud image has both `python` and `python3` (3.11.15) on PATH; a schema-valid Edit of
`.claude/settings.json` was denied by the hook. The log also says "installed plugins' hooks
modules not loaded: rollout flag (tengu_plugin_hooks_modules) is off" — that is a separate,
module-style hook mechanism; command hooks from `hooks.json` are unaffected.

Also observed: the sample container lacks bubblewrap and socat, so the template's sandbox
block is inert there ("Sandbox disabled: ... dependencies are missing"); the setup script
may install them if OS-level isolation is wanted in the cloud.

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
  no tool may change." ("The check requires Claude Code v2.1.208 or later on edits, and
  v2.1.228 or later on writes" — so the framework's minimum Claude Code version was 2.1.228 until B3; it is 2.1.278 since session 3, see §11c.)
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
- A `Bash(git push --force *)` deny cannot catch `git push origin --force`, `+main` or
  `git -C . push -f` (rule prefixes match the command text only), so the template carries no
  such rule; the branch ruleset (decision 4) is the real guard for `main`.

## 7. Plugin distribution facts

Source: https://code.claude.com/docs/en/plugins, /plugins-reference, /plugin-marketplaces.

- Manifest `.claude-plugin/plugin.json` with `name`, `version`, `description`, `author`;
  default component directories `commands/`, `skills/`, `agents/`, `hooks/hooks.json`, each
  overridable by a manifest key ("`skills`: `./custom/skills/`", "`commands`", "`agents`",
  "`hooks`: `./config/hooks.json`"). "Plugin skills are always namespaced (like
  `/my-first-plugin:hello`)" — the commands are therefore invoked as `/sdlc:sdlc-init` and
  `/sdlc:sdlc-plan` when installed from the marketplace.
- Path traversal: "Claude Code doesn't let a plugin reference files outside its own
  directory" and "Claude Code also doesn't copy files outside the plugin directory into the
  cache when it installs the plugin, so when a script inside a copied plugin reads a path
  above the plugin root, it doesn't find those files either." A marketplace entry may point
  at the marketplace root: "several plugin entries share one `skills/` folder at the
  marketplace root (`source: "./"`)". Therefore the **repository root is the plugin root**
  (`.claude-plugin/plugin.json` at the root points components at `./plugin/...`, the
  marketplace entry's `source` is `./`), so `template/` travels with the plugin and
  `/sdlc-init` finds it at `${CLAUDE_PLUGIN_ROOT}/template`. The cached copy therefore also
  contains `docs/` and `tests/` (about 3 MB, mostly the reference PDF).
- "Setting `version` means users only receive updates when you change this field, so bump it
  on every release." (marketplace entry and `plugin.json` both carry `0.1.0`; a test keeps
  them equal).
- Local development: "Run Claude Code with the `--plugin-dir` flag to load your plugin."
  (`claude --plugin-dir <this repo>`). Caveat: with the plugin loaded in place from this repo,
  the protected-path hook protects the whole repository (it is the plugin root), so edit the
  framework in a session without the plugin loaded, or from a marketplace-cached copy.
- "**Commands** and **Skills** use the same mechanism now. For new workflows, prefer
  **skills** ... Commands remain supported for single-file prompts." The repo keeps
  `plugin/commands/` as `CLAUDE.md` prescribes.
- Not found in the docs: whether one slash command can invoke another. `/sdlc-init` therefore
  says "generate one the way `/init` does (use the `init` skill if it is available ...)".

## 8. Hook output contract (checked against the decision-control table)

"UserPromptSubmit, UserPromptExpansion, PostToolUse, PostToolUseFailure, PostToolBatch, Stop,
SubagentStop, ConfigChange, PreCompact | Top-level `decision` | `decision: "block"`,
`reason`" and, for PreToolUse, "`hookSpecificOutput` | `permissionDecision`
(allow/deny/ask/defer), `permissionDecisionReason`". The formatter hook therefore returns
top-level `decision`/`reason` on PostToolUse; the policy hooks return `hookSpecificOutput`
plus exit code 2. "For `PreToolUse` permission decisions, the most restrictive answer
applies, in the order `deny`, `defer`, `ask`, `allow`."

## 9. Known gaps carried to B2/B3

- A `Bash` command that writes a protected file through a script is not seen by the
  protected-path hook or by `Edit` deny rules (section 6); the sandbox and the review pass
  (REVIEW.md framework rules) are the remaining nets until the gate check of step 16 exists.
- The plan-sync hook sees the index, the working tree for `-a`/`--include`, and pathspecs
  named after `commit`; a commit driven from a script the hook cannot parse is not checked.
  The REVIEW.md compliance pass is the second net.
- Change ids are allocated from the local `changes/` folder plus the remote's `sdlc/<id>/*`
  branches (best effort); two changes started at the same moment on two machines can still
  collide, and the second push then fails on the branch name, which is the signal to re-run.
- Skill triggering ("test that it triggers", step 10) and the PR-opening step need a live
  model / GitHub; see `docs/PROGRESS.md`.

## 10. Facts added in session 2 (B2), read on 2026-09-21

### 10a. Subagents and plugin agents (step 17)

Source: https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/plugins-reference.

- "Each subagent runs in its own context window with a custom system prompt, specific tool
  access, and independent permissions." and "Each subagent starts with a fresh, isolated
  context window. It doesn't see your conversation history, the skills you've already
  invoked, or the files Claude has already read." — this is the fresh context the article's
  verifier (p.27) and adversarial reviewer (p.42) need; the four agents rely on it.
- `tools`: "Tools the subagent can use. Inherits every tool available to subagents if
  omitted"; `disallowedTools`: "Tools to deny, removed from inherited or specified list".
  The agents list their tools explicitly (the verifier: `Bash, Read`, as on p.25).
- "Plugin agents support `name`, `description`, `model`, `effort`, `maxTurns`, `tools`,
  `disallowedTools`, `skills`, `memory`, `background`, `omitClaudeMd`, and `isolation`
  frontmatter fields." `permissionMode`, `hooks` and `mcpServers` are "Ignored for plugin
  subagents" — so an agent cannot widen its own permissions; the project's settings and the
  plugin's hooks apply to it like to the main session.
- Manifest: "`agents` | `string|array` | Custom agent files (replaces default `agents/`)";
  the repo lists the four files explicitly (a directory string fails `claude plugin
  validate`, observed in session 1). Names: "a file at `agents/review/security.md` in
  plugin `my-plugin` registers as `my-plugin:review:security`", so ours are
  `sdlc:verifier`, `sdlc:code-simplifier`, `sdlc:researcher`, `sdlc:adversarial-reviewer`.
- "Claude automatically delegates tasks based on the task description in your request, the
  `description` field in subagent configurations, and current context. To encourage
  proactive delegation, include phrases like 'use proactively' in your subagent's
  description field." — the descriptions say when to use each agent, in the same style as
  the intent skill whose trigger passed the live check.
- `maxTurns`: "Maximum number of agentic turns before the subagent stops. When the subagent
  reaches the limit, Claude Code returns its output marked as partial" — set on every agent
  as its own run limit (step 19).

### 10b. Outer bound for headless runs: `--max-turns` and `--max-budget-usd` (step 19)

Source: https://code.claude.com/docs/en/cli-reference, https://code.claude.com/docs/en/headless.

- "`--max-turns`: Limit the number of agentic turns (print mode only). Exits with an error
  when the limit is reached. No limit by default."
- "`--max-budget-usd`: Maximum dollar amount to spend on API calls before stopping (print
  mode only). Spend from subagents counts toward the cap ... the cap-enforcement behaviors
  require Claude Code v2.1.217 or later".
- "With `--output-format json`, the response payload includes `total_cost_usd` and a
  per-model cost breakdown, so scripted callers can track spend per invocation" ("client-side
  estimates").
- "`--permission-mode`: Begin in a specified permission mode. Accepts `default`,
  `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`, or `manual` as an alias for
  `default`". For `-p`
  "the built-in starting permission mode is Manual on every plan, so pass the permission mode
  you want". `acceptEdits`: "Claude writes files without prompting ... other shell commands
  and network requests still need an `--allowedTools` entry or a `permissions.allow` rule".
- "Pass `--permission-prompts none` when nobody is available to answer permission prompts
  ... Anything that would prompt is denied" (v2.1.259+). The framework's declared minimum
  was 2.1.228 (section 6); B3 adopted this flag and set the minimum to 2.1.278 (§11c), or leaves the
  flag out on older runners (a `-p` run with no host denies such prompts anyway).
- `--bare` "is the recommended mode for scripted and SDK calls" but "Bare mode does not read
  `CLAUDE_CODE_OAUTH_TOKEN`" (section 2) and skips CLAUDE.md, hooks and plugins unless
  passed explicitly (`--plugin-dir`, `--settings`).

**Consequences for B3's `claude -p` jobs:** every phase job passes `--max-turns` and
`--max-budget-usd` as the outer bound, `--permission-mode acceptEdits` only when
`plugin/gate/preflight.py` allows it, `--permission-prompts none`, and pipes the JSON
result's `total_cost_usd` into `gate/cli.py record-spend` so the per-change budget of step 19
is enforced across phases. The gate's own limits (iterations, wall-clock, budget, pause) are
the inner bound and are the ones that park with evidence; the CLI bound just stops.

## 11. Facts added in session 3 (B3), read on 2026-09-21

Sources were read by an Opus research sub-agent. `docs.github.com` is blocked by the cloud
session's egress policy, so the GitHub quotes below come from the documentation's source
repository (`github/docs` on raw.githubusercontent.com, the same text the site renders; page
paths given), the official OpenAPI description (`github/rest-api-description`),
`actions/checkout`, `cli/cli` and `octokit/graphql-schema`; `code.claude.com` was reachable.

### 11a. GitHub Actions (build guide step 30; OPERATING_MODEL §4.2)
- Token events (page /actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow):
  "When you use the repository's `GITHUB_TOKEN` to perform tasks, events triggered by the
  `GITHUB_TOKEN` will not create a new workflow run, with the following exceptions:" ...
  "`workflow_dispatch` and `repository_dispatch` events always create workflow runs."
  Newer nuance on the same page: `pull_request` `opened`/`synchronize`/`reopened` events
  caused by the token "create workflow runs in an approval-required state", while "Other
  `pull_request` activity types (such as `labeled`, `edited`, or `closed`) do not create
  workflow runs." Consequence unchanged: every automated transition dispatches the next
  workflow explicitly (decision 5).
- Merge trigger (page /actions/reference/workflows-and-actions/events-that-trigger-workflows):
  "To run a workflow when a pull request merges, use the `pull_request` `closed` event type
  along with a conditional that checks the `merged` value of the event." —
  `if: github.event.pull_request.merged == true`; "You can use the `branches` or
  `branches-ignore` filter to configure your workflow to only run on pull requests that
  target specific branches."
- Label trigger: `pull_request` activity types include `labeled`; the docs' example reads
  the name with `if: github.event.label.name == 'bug'`. The top-level `label` event is about
  label definitions, not applications.
- `permissions:` keys: `actions`, `checks`, `contents`, `issues`, `pull-requests` (each
  `read|write|none`); "If you specify the access for any of these permissions, all of those
  that are not specified are set to `none`." Which permission each REST endpoint needs is
  rendered onto the site from internal data and was **not verifiable** from the reachable
  sources: the workflows request `contents`, `pull-requests`, `issues`, `checks` and
  `actions: write` and the first live run verifies them.
- `concurrency` (page /actions/reference/workflows-and-actions/workflow-syntax): "A
  concurrency group can be any string or expression. The expression can only use `github`,
  `inputs` and `vars` contexts." and "there can be at most one running and one pending job
  in a concurrency group at any time" — a newer pending run replaces the pending one even
  with `cancel-in-progress: false`; group names are case-insensitive.
- `workflow_dispatch` inputs are read as `inputs.<name>` or `github.event.inputs.<name>`
  ("identical except that the `inputs` context preserves Boolean values"); REST
  `POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches` ("You can replace
  `workflow_id` with the workflow file name", 204); `gh workflow run <file> -f k=v --ref
  <branch>`. `repository_dispatch`: "Any data that you send through the `client_payload`
  parameter will be available in the `github.event` context"; at most 10 top-level
  properties and 65,535 characters.
- Labels: `POST /repos/{owner}/{repo}/labels` answers 201, or 422 (validation failed) when
  the name exists — not idempotent, so `plugin/pr/github.py` treats 422 as "exists";
  `POST /repos/{owner}/{repo}/issues/{issue_number}/labels` adds labels (PR numbers are
  issue numbers).
- Check runs: `POST /repos/{owner}/{repo}/check-runs` with `name`, `head_sha`, `conclusion`,
  `output.title/summary`; "To create a check run, you must use a GitHub App. OAuth apps and
  authenticated users are not able to create a check suite." — the workflow token acts as
  an app, a personal token cannot: check runs are posted only from CI.
- `schedule`: "Scheduled workflows run on the latest commit on the default branch. The
  shortest interval you can run scheduled workflows is once every 5 minutes."; "By default,
  scheduled workflows run in UTC."; "In a public repository, scheduled workflows are
  automatically disabled when no repository activity has occurred in 60 days."; delays are
  common "at the start of every hour", so the digest runs at 06:17 UTC. Every `schedule`,
  `workflow_dispatch` and label trigger needs the workflow file on the default branch.
- `actions/checkout` inputs: `repository` ("Repository name with owner"), `ref` ("The
  branch, tag or SHA to checkout."), `path` ("Relative path under $GITHUB_WORKSPACE to
  place the repository"); the README's side-by-side example checks out a second **public**
  repository without a token; a private one needs a PAT. `luissiviero/sdlc-framework` is
  public, so the phase jobs check it out at the tag `v<sdlc.yaml plugin.version>` with no
  token — the framework must be tagged at every version the projects pin.
- Notifications (pages under /subscriptions-and-notifications): "By default, you also
  automatically watch all repositories that you create and are owned by your personal
  account."; default subscriptions include "Opened a pull request or issue", "Been assigned",
  "Commented on a thread", "Had your username @mentioned"; the watch menu's **Custom** option
  adds chosen events "in addition to participating and @mentions". Whether editing an issue
  body notifies subscribers is **not stated** in the docs, so the digest design does not
  depend on it: the digest issue is opened by the workflow token, the owner never comments
  on it, and the owner sets the repository watch to participating-only (OPERATING_MODEL §7).
  Pinning an issue exists only in GraphQL (`pinIssue(input: PinIssueInput!)`).

### 11b. Claude Code flags used by `plugin/ci/run_phase.py`
Source: https://code.claude.com/docs/en/cli-reference, https://code.claude.com/docs/en/headless,
https://code.claude.com/docs/en/sandboxing, https://code.claude.com/docs/en/agent-sdk/typescript.
- `--plugin-dir`: "Load a plugin from a directory or `.zip` archive, or several from a folder
  of plugins, for this session only. Each flag takes one path."
- `--settings`: "Load a settings file (`.json` or `.yaml`) for this session. Can be repeated
  to load multiple files in order. Values from later files override earlier ones." The
  headless page's bare-mode table lists "Settings | `--settings <file-or-json>`", so the
  key-path run (`--bare`) gets `plugin/ci/settings.ci.json` explicitly.
- `--allowedTools`: "Tools that execute without prompting for permission."; prefix form
  `Bash(git diff *)` ("The space before `*` is important"). `--disallowedTools`: "A bare
  tool name removes the matching tools from Claude's context".
- `--output-format json`: "the response payload includes `total_cost_usd` and a per-model
  cost breakdown ... client-side estimates"; the SDK result type carries `session_id`,
  `duration_ms`, `is_error`, `num_turns`, `result`, `total_cost_usd`.
- Sandbox: keys `sandbox.enabled`, `sandbox.network.allowedDomains`,
  `sandbox.failIfUnavailable` ("By default, if the sandbox cannot start because dependencies
  are missing or the platform is unsupported, Claude Code shows a warning and runs commands
  without sandboxing. To make this a hard failure instead, set `sandbox.failIfUnavailable`
  to `true`."). Linux needs `bubblewrap` and `socat`; on ubuntu-24.04 runners "the default
  AppArmor policy prevents bubblewrap from creating the user namespaces it needs" (check
  `kernel.apparmor_restrict_unprivileged_userns`; install an AppArmor profile for `bwrap`);
  `plugin/ci/runner_setup.py` does both, and the CI settings set `failIfUnavailable: true`
  (the template keeps `false` for the owner's PC, §5).

### 11c. Sub-agent model facts (Model rule of `HANDOFF.md`; re-read 2026-09-21)
- Resolution order (https://code.claude.com/docs/en/sub-agents): per-invocation `model`,
  then the definition's `model` frontmatter (`inherit` = the main conversation's model),
  then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's model; "Before v2.1.251,
  `CLAUDE_CODE_SUBAGENT_MODEL` came first in this order". "Setting `CLAUDE_CODE_SUBAGENT_MODEL`
  by itself doesn't change the model the built-in Explore and Plan subagents run on" — a
  per-invocation model does.
- "To check which model a subagent is running on, run `/tasks`. Claude Code names the model
  on the subagent's row ... Requires Claude Code v2.1.242 or later."
- `/usage` (https://code.claude.com/docs/en/costs): the Session block shows "Usage by
  model"; the plan figures are "computed from local session history on this machine"; what a
  cloud session shows is not documented.
- Cloud environments (https://code.claude.com/docs/en/cloud-environments): "Each session
  copies the environment's values once, at startup ... sessions already running keep the
  values they started with."; there is "no settings page or direct URL for the selector";
  `~/.claude/settings.json` is "not read" in a cloud session.
- `--permission-prompts none` (cli-reference): `none` means nobody can answer, Claude Code
  denies prompts instead; "Requires Claude Code v2.1.259 or later." The framework's minimum
  Claude Code version is therefore **2.1.278**, the CLI the workflows install.
