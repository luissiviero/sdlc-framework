"""PreToolUse hook: deny edits to protected paths (build guide step 15 (1), step 7; article
p.23 'Block edits to protected paths', p.36 example PreToolUse hook).

Always protected (self-protection, decision 6): ``.claude/**``, ``CLAUDE.md``, ``REVIEW.md``,
``sdlc.yaml`` (it holds the project's own protected list) and every file under the plugin
root (the hook scripts). Anywhere on disk, inside or outside the project: ``.claude/settings*.json``
and ``.claude/hooks/**`` (the user-level settings are guardrails too). The project adds its
own list under ``protected_paths:`` in ``sdlc.yaml``. There is no exception: a change to
the guardrails is made by the owner, in a session without this hook, and reviewed like any
other PR. The only sanctioned writer in a run is ``/sdlc-init``'s install script, whose
output rides in the change-0000 PR.

Fails closed: a missing or unreadable sdlc.yaml that exists, a bad payload or any error
denies the edit with the reason.

Usage in hooks.json (exec form): python protected_paths.py --plugin-root <path>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    FILE_TOOLS,
    ConfigError,
    Decision,
    load_sdlc_config,
    matches,
    norm,
    project_dir,
    real,
    rel_to,
    run_hook,
    target_paths,
)

ALWAYS_PROTECTED = (".claude/**", "CLAUDE.md", "REVIEW.md", "sdlc.yaml")
# matched against the whole normalised path, wherever it is (user-level settings included)
GLOBAL_PROTECTED = ("**/.claude/settings.json", "**/.claude/settings.*.json", "**/.claude/hooks/**")

REASON = (
    "Protected path: {what}. Edits to guardrail files (.claude/**, CLAUDE.md, REVIEW.md, "
    "sdlc.yaml, the SDLC plugin) and the project's protected_paths are made by the owner in a "
    "reviewed PR, not by a run. Stop and report what you needed to change and why."
)


def protected_patterns(config: dict) -> list[str]:
    extra = config.get("protected_paths") or []
    if not isinstance(extra, list):
        raise ConfigError("sdlc.yaml: protected_paths must be a list")
    return list(ALWAYS_PROTECTED) + [str(p) for p in extra if str(p).strip()]


def _check_one(path: str, root: str, patterns: list[str], plugin_root: str | None) -> str | None:
    """Reason string when the path is protected, else None."""
    for candidate in {norm(path), real(path)}:
        for pattern in GLOBAL_PROTECTED:
            if matches(pattern, candidate):
                return f"{path} matches '{pattern}'"
        if plugin_root and (candidate == plugin_root or candidate.startswith(plugin_root + "/")):
            return f"{path} is part of the SDLC plugin (hook scripts, commands, templates)"
        rel = rel_to(root, candidate)
        if rel is None:
            continue  # outside the project: not ours to police (beyond GLOBAL_PROTECTED)
        for pattern in patterns:
            if matches(pattern, rel):
                return f"{rel} matches '{pattern}'"
    return None


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None) -> Decision:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-root", default=None)
    args = parser.parse_args(argv)

    if payload.get("tool_name") not in FILE_TOOLS:
        return Decision.allow()
    root = project_dir(payload, env)
    try:
        patterns = protected_patterns(load_sdlc_config(root))
    except ConfigError as exc:
        return Decision.deny(
            f"Protected-path hook cannot read the project's guardrail config ({exc}); "
            "refusing every edit until the owner fixes sdlc.yaml."
        )
    plugin_root = real(args.plugin_root) if args.plugin_root else None
    for path in target_paths(payload.get("tool_input") or {}):
        reason = _check_one(path, root, patterns, plugin_root)
        if reason:
            return Decision.deny(REASON.format(what=reason))
    return Decision.allow()


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PreToolUse", sys.argv[1:]))
