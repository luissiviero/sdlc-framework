"""PreToolUse hook: deny edits to protected paths (build guide step 15 (1), step 7; article
p.23 'Block edits to protected paths', p.36 example PreToolUse hook).

Always protected (self-protection, decision 6): ``.claude/**``, ``CLAUDE.md``, ``REVIEW.md``,
``sdlc.yaml`` (it holds the project's own protected list) and every file under the plugin
root (the hook scripts). The project adds its own list under ``protected_paths:`` in
``sdlc.yaml``. There is no exception: a change to the guardrails is made by the owner, in a
session without this hook, and reviewed like any other PR.

Usage in hooks.json (exec form): python protected_paths.py --plugin-root <path>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    FILE_TOOLS,
    Decision,
    load_sdlc_config,
    matches,
    norm,
    project_dir,
    rel_to,
    run_hook,
    target_paths,
)

ALWAYS_PROTECTED = (".claude/**", "CLAUDE.md", "REVIEW.md", "sdlc.yaml")


def protected_patterns(config: dict) -> list[str]:
    extra = config.get("protected_paths") or []
    if not isinstance(extra, list):
        extra = []
    return list(ALWAYS_PROTECTED) + [str(p) for p in extra if str(p).strip()]


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None) -> Decision:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-root", default=None)
    args = parser.parse_args(argv)

    if payload.get("tool_name") not in FILE_TOOLS:
        return Decision.allow()
    root = project_dir(payload, env)
    patterns = protected_patterns(load_sdlc_config(root))
    plugin_root = norm(args.plugin_root) if args.plugin_root else None

    for path in target_paths(payload.get("tool_input") or {}):
        path_n = norm(path)
        if plugin_root and (path_n == plugin_root or path_n.startswith(plugin_root + "/")):
            return Decision.deny(
                f"Protected path: {path} is part of the SDLC plugin (hook scripts and "
                "settings). Guardrails are changed by the owner in a reviewed PR, not by a run."
            )
        rel = rel_to(root, path_n)
        if rel is None:
            continue  # outside the project: not ours to police
        for pattern in patterns:
            if matches(pattern, rel):
                return Decision.deny(
                    f"Protected path: {rel} matches '{pattern}'. Edits to guardrail files "
                    "(.claude/**, CLAUDE.md, REVIEW.md, sdlc.yaml) and the project's "
                    "protected_paths are made by the owner, not by a run. Stop and report "
                    "what you needed to change and why."
                )
    return Decision.allow()


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PreToolUse", sys.argv[1:]))
