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
  of each part — each suffix also read with the program's path and ``.exe``/``.cmd`` suffix
  stripped and with the options between the program and its verb dropped (0.2.27) — so
  ``cd dist && twine upload *``, ``python3.11 -m twine upload``, ``bash -c 'twine upload'``,
  ``nohup``/``time``/``cmd /c``/``pwsh -Command`` wrappers, ``/usr/local/bin/twine upload``,
  ``twine.exe upload``, ``npm.cmd publish``, ``terraform -chdir=x apply``, ``kubectl
  --context p apply`` and ``gh -R o/r release create`` are all caught;
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
    config_flag,
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


def approve_in_time(
    root: str, config: dict, env, git, github, change_id: str | None = None
) -> approval_mod.Approval:
    """``release_approval`` under the time budget; a timeout is "not approved". ``change_id``
    is the change this hook call resolved from the branch (``_log_path`` reads the same),
    so the approval is the recorded build PR of that change and no other (0.2.27)."""
    if github is None:
        github, _why = approval_mod.load_github()  # None: release_approval reports why
    box: dict[str, Any] = {}

    def work() -> None:
        try:
            box["result"] = approval_mod.release_approval(
                root, config, env, git=git, github=github, change_id=change_id
            )
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


# Program-name suffixes a Windows or a packaged install adds: ``twine.exe``, ``npm.cmd``.
PROGRAM_SUFFIXES = (".exe", ".cmd", ".bat", ".com", ".ps1")


def _program(token: str) -> str:
    """The bare program name of a token: ``/usr/local/bin/twine``, ``C:\\x\\twine.exe`` and
    ``.\\npm.cmd`` all read ``twine`` / ``npm``; a token that is not a path or has no such
    suffix is returned unchanged."""
    name = token.replace("\\", "/").rsplit("/", 1)[-1]
    for suffix in PROGRAM_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
            break
    return name


def _without_leading_options(tokens: list[str]) -> list[list[str]]:
    """The token lists that read the same command with the options between the program and
    its verb dropped: ``terraform -chdir=x apply`` → ``terraform apply``; ``kubectl
    --context p apply`` → ``kubectl apply`` (an option without ``=`` may take the next
    token as its value, so both readings are kept: the guard errs on the closed side)."""
    if len(tokens) < 2:
        return []
    out: list[list[str]] = []
    heads = [[tokens[0]]]
    rest = tokens[1:]
    while rest and rest[0].startswith("-"):
        option, rest = rest[0], rest[1:]
        if "=" not in option and rest and not rest[0].startswith("-"):
            # ``--context p apply``: with ``p`` as the value, or as the verb itself
            out.append(heads[0] + rest)
            rest = rest[1:]
        out.append(heads[0] + rest)
    return [tokens_ for tokens_ in out if len(tokens_) > 1]


def _suffixes(part: str) -> list[str]:
    """Every token-boundary suffix of a part, lower-cased: ``nohup python3.11 -m twine
    upload x`` gives ``... twine upload x``, ``upload x`` and ``x`` among others; each
    suffix also with its first token reduced to the bare program name (a path, ``.exe``,
    ``.cmd``) and with the options between the program and its verb dropped (0.2.27: the
    1.0.0 readiness review found ``terraform -chdir=x apply``, ``kubectl --context p
    apply``, ``/usr/local/bin/twine upload`` and ``twine.exe upload`` unguarded)."""
    tokenisations = [[t for t in TOKEN_RE.split(part.lower()) if t]]
    try:  # the shell's own reading too: a quoted value with a space is one token there
        quoted = [t for t in shlex.split(part.lower(), posix=True) if t]
    except ValueError:
        quoted = []
    if quoted and quoted != tokenisations[0]:
        tokenisations.append(quoted)
    seen: list[str] = []
    for tokens in tokenisations:
        for i in range(len(tokens)):
            tail = tokens[i:]
            readings = [tail, [_program(tail[0])] + tail[1:]]
            for reading in list(readings):
                readings.extend(_without_leading_options(reading))
            for reading in readings:
                joined = " ".join(reading)
                if joined not in seen:
                    seen.append(joined)
    return seen


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


def _branch_change(root: str, git) -> tuple[str | None, Path | None]:
    """(the change id of the checked-out ``sdlc/<id>/<phase>`` branch, its folder), one git
    call; (None, None) off a change branch or when git fails or times out."""
    try:
        code, out = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    except TimeoutError:
        return None, None
    parsed = c.parse_branch(out.strip()) if code == 0 and out.strip() else None
    if not parsed:
        return None, None
    return parsed[0], c.find_change_dir(Path(root), parsed[0])


def _log_path(root: str, env: dict[str, str] | None, git, change_dir: Path | None = None) -> Path:
    """Where this call's decisions go, computed once per hook call so ``log_decision`` never
    runs git itself: the change's evidence/hook-log.jsonl on a change branch, else
    ``<root>/changes/.hook-log.jsonl`` (also when git fails or times out). ``$SDLC_HOOK_LOG``
    wins inside ``log_decision``, so no git call is made when it is set."""
    fallback = Path(root) / HOOK_LOG_DEFAULT
    env = os.environ if env is None else env
    if env.get(HOOK_LOG_ENV):
        return fallback
    if change_dir is None:
        _change_id, change_dir = _branch_change(root, git)
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
    change: tuple[str | None, Path | None] | None = None

    def branch_change() -> tuple[str | None, Path | None]:
        """The change of the checked-out branch, one git call, once per hook call."""
        nonlocal change
        if change is None:
            change = _branch_change(root, git)
        return change

    def where() -> Path:
        """The log path, computed on first use and once only (never inside log_decision)."""
        nonlocal log_path
        if log_path is None:
            log_path = _log_path(root, env, git, branch_change()[1])
        return log_path

    try:
        config = load_sdlc_config(root)
        deploy = config.get("deploy") or {}
        if not isinstance(deploy, dict):
            raise ConfigError("sdlc.yaml: deploy must be a mapping")
        if not config_flag(config, "deploy", "production"):
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
        result = approve_in_time(root, config, env, git, github, branch_change()[0])
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
