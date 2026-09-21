"""Preflight for auto-accept (build guide step 18; article p.17–18: "As the guardrails from the
later plays mature (a tuned CLAUDE.md, skills that encode policy, hooks that block unsafe
actions, and a test suite Claude can run), auto-accept becomes the default for routine
work").

    python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root . [--id 0001]

Says whether the implementation run of phase (c) may start with
``--permission-mode acceptEdits``. Every precondition is checked deterministically:
  1. CLAUDE.md exists and names the three one-command targets of sdlc.yaml (step 13);
  2. the policy skills exist — the plugin's own under ``plugin/skills/`` or the project's
     overrides under ``.claude/skills/`` (step 20);
  3. the blocking hooks are loadable: the plugin's ``hooks.json`` parses, every script it
     names exists, and ``python`` resolves on PATH (step 15; NOTES section 1);
  4. the project settings declare the plugin, carry the guardrail deny rules and disable
     bypass-permissions mode (step 7); bypass mode is never used, whatever the answer;
  5. the repository is not paused (step 19);
  6. the one-command test target runs green (step 14).
The report also carries ``setup_command``: the project's one-command install from
``sdlc.yaml: commands.setup``, which the CI phase jobs run before the phase. It is reported
so the owner sees what the runner installs; it is not a precondition.

With ``--id`` it also reports the adversarial reviewer's routine / non-routine
classification for the change and the iteration cap it implies (the classification tightens
the gate; it never changes the permission mode and never interrupts the owner, decision 11).

Exit 0 = allow (``permission_mode: acceptEdits``), 4 = refuse (``permission_mode: default``,
with the reasons), 2 = usage error. Prints JSON.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <plugin root>/plugin
REPO_ROOT = PLUGIN_DIR.parent  # the plugin root Claude Code installs (marketplace source "./")
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate import limits  # noqa: E402
from gate.checks import PLACEHOLDER_COMMAND_RE, CheckResult, GateContext, run_command  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

POLICY_SKILLS = (
    "coding-standards",
    "security-baseline",
    "ux-conventions",
    "data-conventions",
    "definition-of-done",
)
PLUGIN_ID = "sdlc@sdlc-framework"
REQUIRED_DENY = ("Edit(.claude/**)", "Edit(CLAUDE.md)", "Edit(REVIEW.md)", "Edit(sdlc.yaml)")
ALLOW_MODE = "acceptEdits"
REFUSE_MODE = "default"


def _ok(name: str, reason: str, **details: Any) -> CheckResult:
    return CheckResult(name, True, reason, details=details)


def _fail(name: str, reason: str, need: str, **details: Any) -> CheckResult:
    return CheckResult(name, False, reason, need, details)


def setup_command(config: dict[str, Any]) -> str:
    """``sdlc.yaml: commands.setup``: the one-command install the CI phase jobs run before
    the phase (plugin/ci/project_setup.py). Reported, never checked here — a project with
    nothing to install declares "" and the step is skipped."""
    cmds = config.get("commands")
    value = cmds.get("setup") if isinstance(cmds, dict) else None
    return value.strip() if isinstance(value, str) else ""


def _commands(config: dict[str, Any]) -> dict[str, str]:
    cmds = config.get("commands")
    out: dict[str, str] = {}
    if isinstance(cmds, dict):
        for key in ("build", "test", "lint"):
            value = cmds.get(key)
            if isinstance(value, str) and value.strip() and not PLACEHOLDER_COMMAND_RE.match(value):
                out[key] = value.strip()
    return out


# --- 1. CLAUDE.md with the three commands  -------------------------------------------------------
def check_claude_md(root: Path, config: dict[str, Any]) -> CheckResult:
    path = root / "CLAUDE.md"
    if not path.is_file():
        return _fail("claude_md", "CLAUDE.md is missing", "Run /sdlc-init (step 13).")
    text = path.read_text(encoding="utf-8", errors="replace")
    cmds = _commands(config)
    missing = [k for k in ("build", "test", "lint") if k not in cmds]
    if missing:
        return _fail(
            "claude_md",
            f"sdlc.yaml has no usable {', '.join(missing)} target",
            "Give the project one-command build/test/lint targets (re-run /sdlc-init).",
        )
    absent = [
        k for k, cmd in cmds.items() if cmd not in text and cmd.replace('"', '\\"') not in text
    ]
    if absent:
        return _fail(
            "claude_md",
            f"CLAUDE.md does not name the {', '.join(absent)} command of sdlc.yaml",
            "Re-run /sdlc-init so CLAUDE.md's Commands section matches sdlc.yaml, or fix "
            "CLAUDE.md in a reviewed PR.",
        )
    return _ok("claude_md", "CLAUDE.md names the three one-command targets")


# --- 2. policy skills  ---------------------------------------------------------------------------
def check_policy_skills(root: Path, plugin_root: Path) -> CheckResult:
    found: dict[str, str] = {}
    missing: list[str] = []
    for name in POLICY_SKILLS:
        project = root / ".claude" / "skills" / name / "SKILL.md"
        shipped = plugin_root / "plugin" / "skills" / name / "SKILL.md"
        if project.is_file():
            found[name] = "project override"
        elif shipped.is_file():
            found[name] = "plugin"
        else:
            missing.append(name)
    if missing:
        return _fail(
            "policy_skills",
            f"policy skill(s) missing: {', '.join(missing)}",
            "Install the pinned plugin version that ships them, or add project overrides "
            "under .claude/skills/<name>/SKILL.md (step 20).",
            found=found,
            missing=missing,
        )
    return _ok("policy_skills", "every policy skill is available", found=found)


# --- 3. hooks loadable  --------------------------------------------------------------------------
def check_hooks(plugin_root: Path) -> CheckResult:
    hooks_json = plugin_root / "plugin" / "hooks" / "hooks.json"
    if not hooks_json.is_file():
        return _fail(
            "hooks",
            f"{hooks_json} not found",
            "The plugin install is incomplete; reinstall the pinned plugin.",
        )
    try:
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
    except ValueError as exc:
        return _fail("hooks", f"hooks.json does not parse: {exc}", "Reinstall the plugin.")
    scripts: list[str] = []
    for event, groups in (data.get("hooks") or {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                if hook.get("type") != "command" or hook.get("command") != "python":
                    return _fail(
                        "hooks",
                        f"{event}: a hook is not a `python` exec-form command",
                        "Hooks must be exec form with `python` (NOTES section 1).",
                    )
                for arg in hook.get("args", []):
                    if str(arg).endswith(".py"):
                        scripts.append(str(arg).replace("${CLAUDE_PLUGIN_ROOT}", str(plugin_root)))
    absent = [s for s in scripts if not Path(s).is_file()]
    if absent:
        return _fail(
            "hooks",
            f"hook script(s) missing: {', '.join(absent)}",
            "Reinstall the pinned plugin.",
        )
    if not scripts:
        return _fail("hooks", "hooks.json registers no hook", "Reinstall the pinned plugin.")
    python = shutil.which("python")
    if not python:
        return _fail(
            "hooks",
            "`python` does not resolve on PATH, so the hooks cannot spawn",
            "Put `python` on PATH (or change the `command` field in hooks.json once, NOTES "
            "section 1); without the hooks there is no blocking layer, so no auto-accept.",
        )
    return _ok("hooks", f"{len(scripts)} hook scripts present; python at {python}", scripts=scripts)


# --- 4. project settings  ------------------------------------------------------------------------
def check_settings(root: Path) -> CheckResult:
    path = root / ".claude" / "settings.json"
    if not path.is_file():
        return _fail("settings", ".claude/settings.json is missing", "Run /sdlc-init (step 7).")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return _fail("settings", f"settings.json does not parse: {exc}", "Fix it in a reviewed PR.")
    problems = []
    perms = data.get("permissions") or {}
    if perms.get("disableBypassPermissionsMode") != "disable":
        problems.append("permissions.disableBypassPermissionsMode is not 'disable'")
    deny = perms.get("deny") or []
    for rule in REQUIRED_DENY:
        if rule not in deny:
            problems.append(f"deny rule {rule} missing")
    if not (data.get("enabledPlugins") or {}).get(PLUGIN_ID):
        problems.append(f"enabledPlugins does not enable {PLUGIN_ID}")
    if problems:
        return _fail(
            "settings",
            "; ".join(problems),
            "Re-run /sdlc-init (it only adds the missing rules) and merge the result.",
            problems=problems,
        )
    return _ok("settings", "bypass disabled, guardrail deny rules and the plugin declared")


# --- 5. pause flag  ------------------------------------------------------------------------------
def check_not_paused(config: dict[str, Any]) -> CheckResult:
    if config.get("paused") is True:
        return _fail(
            "paused",
            "the repository is paused (sdlc.yaml: paused: true)",
            "Set `paused: false` in sdlc.yaml when runs may resume.",
        )
    return _ok("paused", "not paused")


# --- 6. the test target is green  ----------------------------------------------------------------
def check_test_target(root: Path, config: dict[str, Any]) -> CheckResult:
    cmds = _commands(config)
    if "test" not in cmds:
        return _fail("test_target", "no usable test target", "Re-run /sdlc-init (step 14).")
    gate_cfg = config.get("gate") if isinstance(config.get("gate"), dict) else {}
    try:
        timeout = int(gate_cfg.get("command_timeout", 900))
    except (TypeError, ValueError):
        timeout = 900
    run = run_command(cmds["test"], root, timeout)
    if run["exit_code"] != 0:
        return _fail(
            "test_target",
            "the test target is not green"
            + (" (timed out)" if run["exit_code"] is None else f" (exit {run['exit_code']})"),
            "Auto-accept needs a green suite to lean on (article p.18); fix the project first.",
            run=run,
        )
    return _ok("test_target", "the test target exits 0", run=run)


# --- classification (informational)  -------------------------------------------------------------
def classification(root: Path, config: dict[str, Any], change_id: str | None) -> dict[str, Any]:
    if not change_id:
        return {}
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        return {"change_id": change_id, "error": "no change folder"}
    st = status_mod.read_status(change_dir)
    ctx = GateContext(root, change_dir, "c", st, config, None, False)
    cls = limits.classification_for(ctx)
    return {
        "change_id": change_id,
        "classification": cls,
        "iteration_cap": limits.iteration_cap(ctx, cls),
        "iterations_so_far": st.iterations,
        "verdict_file": art.ADVERSARIAL_VERDICT.format(phase="b"),
    }


def run_preflight(root: Path, plugin_root: Path, change_id: str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    plugin_root = Path(plugin_root).resolve()
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        config, cfg_error = {}, str(exc)
    else:
        cfg_error = "" if config else "sdlc.yaml not found: run /sdlc-init first"
    checks: list[CheckResult] = []
    if cfg_error:
        checks.append(_fail("sdlc_yaml", cfg_error, "Run /sdlc-init."))
    else:
        checks.append(_ok("sdlc_yaml", "sdlc.yaml read"))
        checks.append(check_claude_md(root, config))
    checks.append(check_policy_skills(root, plugin_root))
    checks.append(check_hooks(plugin_root))
    checks.append(check_settings(root))
    if not cfg_error:
        checks.append(check_not_paused(config))
        if all(ch.ok for ch in checks):  # the slow one, only when the rest holds
            checks.append(check_test_target(root, config))
    allow = all(ch.ok for ch in checks)
    return {
        "schema_version": 1,
        "root": str(root),
        "plugin_root": str(plugin_root),
        "allow": allow,
        "permission_mode": ALLOW_MODE if allow else REFUSE_MODE,
        "never": "bypassPermissions",
        "reasons": [f"{ch.name}: {ch.reason}" for ch in checks if not ch.ok],
        "setup_command": setup_command(config),
        "checks": [ch.as_dict() for ch in checks],
        "change": classification(root, config, change_id) if not cfg_error else {},
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-preflight",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", default=".")
    p.add_argument("--plugin-root", default=str(REPO_ROOT))
    p.add_argument("--id", default=None, help="change id: report its classification and cap")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_preflight(Path(args.root), Path(args.plugin_root), args.id)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["allow"] else 4


if __name__ == "__main__":
    sys.exit(main())
