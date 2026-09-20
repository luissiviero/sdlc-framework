# Owner-machine managed settings (decision 6, layer ii)

`managed-settings.json` in this folder is the file the operating model calls "a user-level
managed settings file on the owner's machine". It is **documented, not installed** by the
framework: it changes every Claude Code session on the machine, so installing it is the
owner's act. The quotes below are from the Claude Code docs consulted on 2026-09-19
(see `docs/NOTES.md` for the full list).

## What the docs say the two keys do

- `allowManagedPermissionRulesOnly` (managed scope only): "Claude Code then ignores `allow`,
  `ask`, and `deny` rules in user, project, local, and `--settings` files, ignores
  `--allowedTools`, hides the always-allow choices in permission prompts, and stops saving new
  rules." — so the allow/deny lists must live **in this file**; the project's
  `.claude/settings.json` rules are ignored while it is installed.
- `allowManagedHooksOnly` (managed scope only): "`true`: only managed hooks run, plus Agent
  SDK hooks and hooks from plugins your managed settings force-enable" through
  `enabledPlugins`, matched on the full `plugin@marketplace` id. Hooks from any other plugin,
  and from `.claude/settings.json`, are blocked. That is why this file force-enables
  `sdlc@sdlc-framework` and registers the marketplace.
- `permissions.disableBypassPermissionsMode: "disable"` (any scope): "Claude Code then
  rejects the `--dangerously-skip-permissions` flag".

## Where the file goes

| OS | Path (from the managed settings docs) |
|---|---|
| Windows | `C:\Program Files\ClaudeCode\managed-settings.json` (needs administrator rights; the legacy `C:\ProgramData\...` path is not read) |
| Linux and WSL | `/etc/claude-code/managed-settings.json` |
| macOS | `/Library/Application Support/ClaudeCode/managed-settings.json` |

Windows alternative without admin rights: the same JSON as a `REG_SZ` value named
`Settings` under `HKCU\SOFTWARE\Policies\ClaudeCode` (lowest-priority managed source).

## Consequences to accept before installing

1. Machine-wide: every repo's `.claude/settings.json` permission rules and hooks are ignored
   on this machine. Unrelated projects lose their local allow-lists (the `allow` block here
   is deliberately broad for that reason) and their own hooks.
2. The article's "engineers cannot edit or override any of it" (p.37) does not hold on a
   single machine where the owner is the administrator; the file is a guard against the
   *agent*, not against the owner.
3. Cloud sessions never read it: there, the repo's `.claude/settings.json` and the plugin it
   declares are the only layers (plus the protected-path hook inside the plugin).
4. The sandbox is not available on native Windows (docs: "Native Windows is not supported.
   On Windows, run Claude Code inside a WSL2 distribution"), so no sandbox block is set here.

## Verify after installing

Run `claude` in any project and check `/status`: it lists the managed settings source. Then,
in a project initialised with `/sdlc-init`, ask Claude to edit `.claude/settings.json`: the
protected-path hook must deny it with the reason "Protected path".
