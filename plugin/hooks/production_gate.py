"""PreToolUse hook on Bash and PowerShell: a production command needs the release approval
(build guide step 29; decision 13; article p.35-37, "Hooks as approval gates").

The article's gate (p.36-37) blocks a Bash command that contains both ``deploy`` and
``production`` unless ``$RELEASE_APPROVAL`` is set, with exit 2 and the reason on stderr. This
hook keeps that trigger and its exit-2 contract and changes three things:

* **what counts as approval** (p.37: "The gate also defines what counts as approval"): the
  label ``sdlc:release-approved`` on the change's build PR, applied by a person on GitHub —
  read through ``plugin/release/approval.py``, never from an environment variable an
  unattended run could set itself, and never a signed tag (a session allowed ``git`` can sign
  one itself; decision 11: a run cannot approve itself). For the same reason any command that
  names the label at all (``gh pr edit --add-label``, ``gh api .../labels``, ``curl``, a
  script) is blocked outright while production is declared;
* **which commands are guarded**: the article's trigger, plus the defaults of the project's
  ``sdlc.yaml: deploy.action`` adapter (``DEFAULT_GUARDED``), plus the project's own
  ``deploy.guarded_commands`` (shell-style globs, case-insensitive). The command is cut into
  parts at the chain operators and substitutions (``&&``, ``||``, ``;``, ``|``, ``&``,
  ``$(``, backticks, ``)``, newlines) and each pattern is matched against every token suffix
  of each part, so ``cd dist && twine upload *``, ``python3.11 -m twine upload``,
  ``bash -c 'twine upload'`` and ``nohup``/``time``/``cmd /c``/``pwsh -Command`` wrappers
  are all caught;
* **it never asks**: the article's hook "can allow, ask, or block" (p.36), but the phase runs
  are unattended (OPERATING_MODEL section 4), so a missing approval blocks with the reason and
  the route to approval (p.36 step 4: "A block should explain itself"), and nobody is
  notified.

It is inert unless ``sdlc.yaml: deploy.production`` is ``true``: then it returns allow without
logging anything. With production declared, every allow and block is appended as one
timestamped JSON line to the hook log (``_common.log_decision``; p.37: "Allow and block
decisions are logged with a timestamp"). An unreadable ``sdlc.yaml`` fails closed (exit 2).

Usage in hooks.json (exec form): python production_gate.py
"""

from __future__ import annotations

import contextlib
import fnmatch
import os
import re
import shlex
import socket
import sys
import threading
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    HOOK_LOG_DEFAULT,
    HOOK_LOG_ENV,
    HOOK_LOG_EVIDENCE,
    ConfigError,
    Decision,
    load_sdlc_config,
    log_decision,
    project_dir,
    run_hook,
)
from release import approval as approval_mod  # noqa: E402

from state import conventions as c  # noqa: E402

HOOK = "production_gate"
TOOLS = ("Bash", "PowerShell")

# Command patterns each deploy adapter guards by default (OPERATING_MODEL section 9). Shell-style
# globs, case-insensitive, matched against every token suffix of each part of a command, so a
# runner or wrapper in front (``python -m``, ``sudo``, ``nohup``, ``bash -c '...'``) does not
# hide it. A pattern without any wildcard gets a trailing ``*`` so it still matches the
# command with more arguments. ``sdlc.yaml: deploy.guarded_commands`` adds to these; the
# article's own trigger (``deploy`` and ``production`` in one command, p.36) holds for every
# adapter. "promote to paper trading" has no default: promotion commands differ per project
# and a broad ``*promote*`` guarded ``git commit -m "promote ..."``, so a paper-trading
# project lists its own promotion command in ``deploy.guarded_commands``.
DEFAULT_GUARDED: dict[str, tuple[str, ...]] = {
    "publish package": (
        "twine upload*",
        "npm publish*",
        "cargo publish*",
        "gem push*",
        "poetry publish*",
        "uv publish*",
        "gh release create*",
    ),
    "deploy service": (
        "kubectl apply*",
        "kubectl rollout*",
        "helm upgrade*",
        "helm install*",
        "docker push*",
        "terraform apply*",
        "pulumi up*",
        "gcloud run deploy*",
        "az webapp deploy*",
        "aws deploy *",
        "flyctl deploy*",
        "fly deploy*",
        "heroku *",
        "vercel --prod*",
        "serverless deploy*",
        "sls deploy*",
        "gh release create*",
    ),
    "schedule job": (
        "crontab *",
        "schtasks *",
        "systemctl enable*",
        "systemctl start*",
        "gh workflow enable*",
    ),
    "promote to paper trading": (),
    "regenerate report": (),
    "none": (),
}

# Chain operators: the article trigger is judged per chained part (p.36).
CHAIN_RE = re.compile(r"&&|\|\||;|\||\r?\n")
# Everything that starts another command: the chain operators, a background ``&`` (also the
# PowerShell call operator), command substitution ``$(`` and backticks, a closing ``)``.
SPLIT_RE = re.compile(r"&&|\|\||;|\||&|\$\(|`|\)|\r?\n")
# Token boundaries inside a part: whitespace, quotes, backticks and parentheses.
TOKEN_RE = re.compile(r"[\s'\"`()]+")
# Any mention of the release label: the approval is the owner's act on GitHub.
LABEL_RE = re.compile(re.escape(approval_mod.RELEASE_LABEL), re.IGNORECASE)
COMMAND_SHOWN = 100  # characters of the command quoted in the block text
# Time budget (hooks.json gives the hook 60 s): each git call and each GitHub request gets
# CALL_TIMEOUT seconds, and the whole approval check APPROVAL_DEADLINE seconds, after which
# the decision is block ("cannot verify the approval in time"), never a silent allow. A
# PreToolUse hook that outlives its timeout does not block (docs/NOTES.md section 8), so the
# worst case - the one git call of the log path, the deadline, the log writes - stays under
# 50 s (WORST_CASE).
CALL_TIMEOUT = 10
APPROVAL_DEADLINE = 35
WORST_CASE = CALL_TIMEOUT + APPROVAL_DEADLINE


@contextlib.contextmanager
def _bounded_github(github: Any):
    """Cap ``pr.github``'s own timeouts at CALL_TIMEOUT while the check runs: its
    ``_request`` reads the module constant ``TIMEOUT`` per call (urlopen's explicit timeout
    overrides a socket default) and ``_gh`` reads ``GH_TIMEOUT``. The socket default covers
    anything else. Everything is restored afterwards."""
    saved = {n: getattr(github, n) for n in ("TIMEOUT", "GH_TIMEOUT") if hasattr(github, n)}
    previous = socket.getdefaulttimeout()
    try:
        for name in saved:
            setattr(github, name, CALL_TIMEOUT)
        socket.setdefaulttimeout(CALL_TIMEOUT)
        yield
    finally:
        for name, value in saved.items():
            setattr(github, name, value)
        socket.setdefaulttimeout(previous)


def approve_in_time(root: str, config: dict, env, git, github) -> approval_mod.Approval:
    """``release_approval`` under the time budget; a timeout is "not approved"."""
    if github is None:
        github, _why = approval_mod.load_github()  # None: release_approval reports why
    box: dict[str, Any] = {}

    def work() -> None:
        try:
            box["result"] = approval_mod.release_approval(root, config, env, git=git, github=github)
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller's thread
            box["error"] = exc

    with _bounded_github(github):
        worker = threading.Thread(target=work, name="release-approval", daemon=True)
        worker.start()
        worker.join(APPROVAL_DEADLINE)
    if worker.is_alive():
        return approval_mod.Approval(
            False, "none", f"cannot verify the approval in time (over {APPROVAL_DEADLINE}s)"
        )
    if "error" in box:
        if isinstance(box["error"], TimeoutError):
            return approval_mod.Approval(
                False, "none", f"cannot verify the approval in time: {box['error']}"
            )
        raise box["error"]
    return box["result"]


def guarded_patterns(action: str, deploy: dict[str, Any]) -> list[str]:
    extra = deploy.get("guarded_commands") or []
    if not isinstance(extra, list):
        raise ConfigError("sdlc.yaml: deploy.guarded_commands must be a list of patterns")
    patterns = list(DEFAULT_GUARDED.get(action, ())) + [str(p) for p in extra if str(p).strip()]
    return [p if any(ch in p for ch in "*?[") else p + "*" for p in patterns]


def command_parts(command: str) -> list[str]:
    """The parts of a command that can each start a program on their own."""
    return [p.strip() for p in SPLIT_RE.split(command or "") if p.strip()]


def chain_parts(command: str) -> list[str]:
    """The parts between chain operators only (the article trigger's unit)."""
    return [p.strip() for p in CHAIN_RE.split(command or "") if p.strip()]


def _suffixes(part: str) -> list[str]:
    """Every token-boundary suffix of a part, lower-cased: ``nohup python3.11 -m twine
    upload x`` gives ``... twine upload x``, ``upload x`` and ``x`` among others."""
    tokens = [t for t in TOKEN_RE.split(part.lower()) if t]
    return [" ".join(tokens[i:]) for i in range(len(tokens))]


def _tokens(part: str) -> list[str]:
    try:
        return shlex.split(part, posix=False)
    except ValueError:
        return part.split()


def article_trigger(part: str) -> bool:
    """The article's own condition (p.36): a word starting with ``deploy`` and a word starting
    with ``production``, case-insensitive; ``--env=production``, ``--production`` and a path
    such as ``./scripts/deploy.sh`` count (tokens are split on ``=``, ``:``, ``/``, ``\\``)."""
    words: list[str] = []
    for token in _tokens(part):
        for piece in re.split(r"[=:/\\]", token.lower()):
            words.append(piece.lstrip("-\"'(`"))
    return any(w.startswith("deploy") for w in words) and any(
        w.startswith("production") for w in words
    )


def guarded(command: str, patterns: list[str]) -> tuple[str, str] | None:
    """(the guarded part, what matched it) or None."""
    lowered = [(p, p.lower()) for p in patterns]
    for part in command_parts(command):
        for suffix in _suffixes(part):
            for pattern, low in lowered:
                if fnmatch.fnmatchcase(suffix, low):
                    return part, pattern
    for part in chain_parts(command):
        if article_trigger(part):
            return part, "deploy + production (article p.36)"
    return None


def names_the_label(command: str) -> str | None:
    """The first part of the command that mentions the release label, or None."""
    for part in command_parts(command):
        if LABEL_RE.search(part):
            return part
    return None


def _log_path(root: str, env: dict[str, str] | None, git) -> Path:
    """Where this call's decisions go, computed once per hook call so ``log_decision`` never
    runs git itself: the change's evidence/hook-log.jsonl on a change branch, else
    ``<root>/changes/.hook-log.jsonl`` (also when git fails or times out). ``$SDLC_HOOK_LOG``
    wins inside ``log_decision``, so no git call is made when it is set."""
    fallback = Path(root) / HOOK_LOG_DEFAULT
    env = os.environ if env is None else env
    if env.get(HOOK_LOG_ENV):
        return fallback
    try:
        code, out = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    except TimeoutError:
        return fallback
    parsed = c.parse_branch(out.strip()) if code == 0 and out.strip() else None
    change_dir = c.find_change_dir(Path(root), parsed[0]) if parsed else None
    return change_dir / HOOK_LOG_EVIDENCE if change_dir is not None else fallback


def block_text(command: str, action: str, detail: str, pr_number: int | None) -> str:
    shown = " ".join(command.split())
    if len(shown) > COMMAND_SHOWN:
        shown = shown[:COMMAND_SHOWN] + "..."
    where = f"the build PR #{pr_number}" if pr_number else "the build PR"
    return (
        f"Production gate (build guide step 29; article p.36-37): `{shown}` is a guarded "
        f"production command for deploy adapter '{action}' and no release approval exists"
        f"{f' ({detail})' if detail else ''}. Route: the owner applies the label "
        f"`{approval_mod.RELEASE_LABEL}` on {where} from GitHub, then re-runs; the hook "
        "never asks (the run is unattended, OPERATING_MODEL section 4) and nobody has been "
        "notified."
    )


def label_block_text(command: str) -> str:
    shown = " ".join(command.split())
    if len(shown) > COMMAND_SHOWN:
        shown = shown[:COMMAND_SHOWN] + "..."
    return (
        f"Production gate (build guide step 29): `{shown}` names the label "
        f"`{approval_mod.RELEASE_LABEL}`: the release approval is the owner's act on GitHub; "
        "a run cannot apply the label to itself (decision 11). Nobody has been notified."
    )


def decide(
    payload: dict,
    argv: list[str],
    env: dict[str, str] | None = None,
    git=None,
    github=None,
) -> Decision:
    if payload.get("tool_name") not in TOOLS:
        return Decision.allow()
    command = str((payload.get("tool_input") or {}).get("command") or "")
    git = git or approval_mod.make_git(CALL_TIMEOUT)
    root = project_dir(payload, env)
    shown = command[:200]
    log_path: Path | None = None

    def where() -> Path:
        """The log path, computed on first use and once only (never inside log_decision)."""
        nonlocal log_path
        if log_path is None:
            log_path = _log_path(root, env, git)
        return log_path

    try:
        config = load_sdlc_config(root)
        deploy = config.get("deploy") or {}
        if not isinstance(deploy, dict):
            raise ConfigError("sdlc.yaml: deploy must be a mapping")
        if deploy.get("production") is not True:
            return Decision.allow()  # inert: no production declared, nothing logged
        action = str(deploy.get("action") or "none").strip().lower()
        patterns = guarded_patterns(action, deploy)
    except ConfigError as exc:
        log_decision(
            HOOK, "block", f"fail closed: {exc}", payload, env, default_path=where(), command=shown
        )
        raise
    where()  # the log path's one git call, before the approval's time budget starts
    if names_the_label(command) is not None:
        text = label_block_text(command)
        log_decision(
            HOOK,
            "block",
            text,
            payload,
            env,
            default_path=where(),
            command=shown,
            action=action,
            matched=approval_mod.RELEASE_LABEL,
        )
        return Decision.deny(text)
    hit = guarded(command, patterns)
    if hit is None:
        log_decision(
            HOOK,
            "allow",
            "not a guarded command",
            payload,
            env,
            default_path=where(),
            command=shown,
            action=action,
        )
        return Decision.allow()
    _part, matched = hit
    try:
        result = approve_in_time(root, config, env, git, github)
    except Exception as exc:  # noqa: BLE001 - logged, then run_hook fails closed
        log_decision(
            HOOK,
            "block",
            f"fail closed: the approval check raised {exc!r}",
            payload,
            env,
            default_path=where(),
            command=shown,
            action=action,
            matched=matched,
        )
        raise
    if result.approved:
        log_decision(
            HOOK,
            "allow",
            f"release approval: {result.how} ({result.detail})",
            payload,
            env,
            default_path=where(),
            command=shown,
            action=action,
            matched=matched,
            how=result.how,
            pr=result.pr_number,
        )
        return Decision.allow()
    text = block_text(command, action, result.detail, result.pr_number)
    log_decision(
        HOOK,
        "block",
        text,
        payload,
        env,
        default_path=where(),
        command=shown,
        action=action,
        matched=matched,
        how=result.how,
        pr=result.pr_number,
    )
    return Decision.deny(text)


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PreToolUse", sys.argv[1:], log=False))
