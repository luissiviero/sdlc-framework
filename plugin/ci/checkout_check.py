"""Verify the project checkout before the second step of a job that shares it across a
model's session (plugin 0.2.27; the review of the 0.2.26 diff, M4; the 1.0.0 readiness
review, group B).

The deploy job runs the review pass and then phase (e); the detect job runs phase (f) and
then ``finish``. Between the two, a ``claude`` session held ``Write`` and ``Bash(git *)`` in
the same checkout, so what the second step reads is what the session left: the framework
tree under ``framework/``, the project's ``.git/config`` (its remote, its fetch refspec, any
``url.<x>.insteadOf`` that redirects a fetch) and the remote-tracking refs. The steps that
run this script are:

1. ``python -c "import shutil; shutil.rmtree('framework', ignore_errors=True)"`` — the
   framework checkout the session could reach is removed, not inspected: a check of a tree
   the session controls is defeated by ``update-index --skip-worktree``, a moved tag or a
   planted ``__pycache__`` (the fresh-context review of the 0.2.27 diff).
2. ``actions/checkout`` of the framework again, at the pin the first step read (a step
   output, which lives in the runner) — the runner's own action, a fresh clone.
3. This script, run from that fresh checkout, which refuses (exit 3, the job red before the
   step that holds the secrets):
   - a ``remote.origin.url`` that is not the repository, or a ``remote.origin.fetch`` that
     is not the default ``+refs/heads/*:refs/remotes/origin/*``;
   - any ``url.*.insteadOf`` / ``pushInsteadOf``, ``include``/``includeIf``, ``core.hooksPath``,
     ``core.fsmonitor``, ``core.sshCommand``, ``core.gitProxy``, proxy, ``pushurl``,
     ``uploadpack`` or ``receivepack`` key in the local or the global git config (a session
     can write both; each one redirects a fetch or runs a command under the step's env);
   - a framework checkout whose HEAD is not the commit ``refs/tags/<pin>`` names on the
     framework's origin (``ls-remote``, the network as the truth), or that is not clean;
   - a default branch whose pin, re-read after a fetch by the repository's URL (never the
     remote's name), is not the job's pin.
   Then the default branch's remote-tracking ref holds what origin holds.

What it does not close, recorded: git reads the project's local config for every command,
so a key this denylist does not name could still run something; the head's own workflow
file on a ``pull_request`` event (choice 95). A fresh clone of the project itself would
close the first; the road to 1.0.0 records it as a candidate.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ci import app_token  # noqa: E402 - stdlib only, from this fresh framework checkout

DEFAULT_FETCH_REFSPEC = "+refs/heads/*:refs/remotes/origin/*"
# config keys (lower-cased, regex) that redirect a fetch or run a command under git
DENIED_CONFIG = (
    r"^url\..*\.(insteadof|pushinsteadof)$",
    r"^include\.path$",
    r"^includeif\..*$",
    r"^core\.(hookspath|fsmonitor|sshcommand|gitproxy|askpass|pager|editor)$",
    r"^(http|https)\..*proxy$",
    r"^(http|https)\.proxy$",
    # R49 review: TLS verification off or another CA would expose the next push's token
    r"^(http|https)\..*ssl(verify|cainfo|capath|cert|key)$",
    r"^remote\..*\.(proxy|pushurl|uploadpack|receivepack|vcs)$",
    r"^credential\..*helper$",
    r"^alias\..*$",
    r"^gpg\..*program$",
    r"^diff\..*command$",
    r"^merge\..*driver$",
    r"^filter\..*\.(clean|smudge|process)$",
    # R49 review: a per-worktree config file (``.git/config.worktree``) is one more place to
    # hide a key in; ``config_problems`` reads the worktree scope too, and the switch is refused
    r"^extensions\.worktreeconfig$",
)
EXIT_REFUSED = 3
CLEAN_ENV = {
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
}


def git(cwd: Path, *args: str, env: dict[str, str] | None = None) -> tuple[int, str]:
    import os

    merged = dict(os.environ)
    merged.update(env or {})
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
        check=False, env=merged,
    )  # fmt: skip
    return proc.returncode, (proc.stdout if proc.returncode == 0 else proc.stderr)


# the subset judged in the global config: the runner image's own ~/.gitconfig is not this
# framework's to know (a signing program or a credential helper there is the image's), so
# only the keys that redirect a fetch or include another file are refused at that scope
DENIED_GLOBAL = DENIED_CONFIG[:3]


# The scopes judged, as ``git config --show-scope`` names them: the worktree's own file
# (``.git/config.worktree``, read once ``extensions.worktreeConfig`` is set) is judged as the
# local one. ``system`` and ``command`` stay out: the image's and the runner's own.
SCOPES = (("local", DENIED_CONFIG), ("worktree", DENIED_CONFIG), ("global", DENIED_GLOBAL))
# Decision 33 (R49): before the runner hands the App's token back to a checkout a model's
# session could write (``app_token.session_credential``), the keys that would send the next
# push elsewhere or unprotected count at the global scope too (the session can write
# ~/.gitconfig as well): a proxy, and TLS verification or its CA.
CREDENTIAL_SCOPES = (
    ("local", DENIED_CONFIG),
    ("worktree", DENIED_CONFIG),
    ("global", (*DENIED_GLOBAL, *[p for p in DENIED_CONFIG if p.startswith("^(http|https)")])),
)


def config_problems(root: Path, scopes=SCOPES) -> list[str]:
    """The denied keys of the git config as git resolves it in ``root``, each named with its
    scope: one ``git config --list --show-scope --name-only`` (git 2.26+) over every file git
    reads, so a key hidden in ``.git/config.worktree`` or an included file is seen where
    ``git config --local --list`` would miss it (the R49 review). A git that refuses the
    listing is itself a problem (fail safe: the caller refuses, or stays on the workflow
    token)."""
    return [
        name if scope == UNLISTED else f"git config {scope} carries {name}"
        for scope, name in config_findings(root, scopes)
    ]


UNLISTED = "unlisted"  # the scope of the one finding a failed listing gives


def config_findings(root: Path, scopes=SCOPES) -> list[tuple[str, str]]:
    """``config_problems`` as (scope, key) pairs; a listing git refused is the one pair
    (``UNLISTED``, what git said)."""
    code, out = git(root, "config", "--list", "--show-scope", "--name-only")
    if code != 0:
        first = (out.strip().splitlines() or [""])[0]
        return [(UNLISTED, f"git config --list --show-scope failed (exit {code}): {first}")]
    patterns_of = dict(scopes)
    found: list[tuple[str, str]] = []
    for line in out.splitlines():
        scope, _, name = line.partition("\t")
        patterns = patterns_of.get(scope)
        if patterns and any(re.match(pattern, name.lower()) for pattern in patterns):
            found.append((scope, name))
    return found


def origin_problems(root: Path, origin: str | None) -> list[str]:
    problems: list[str] = []
    code, out = git(root, "config", "--local", "--get-all", "remote.origin.fetch")
    specs = [line.strip() for line in out.splitlines() if line.strip()] if code == 0 else []
    if specs != [DEFAULT_FETCH_REFSPEC]:
        problems.append(
            f"remote.origin.fetch is {specs or 'unset'}, not [{DEFAULT_FETCH_REFSPEC!r}]"
        )
    if origin:
        code, url = git(root, "config", "--local", "--get", "remote.origin.url")
        url = url.strip() if code == 0 else ""
        expected = {origin, origin + ".git", origin.rstrip("/") + "/"}
        if url not in expected:
            problems.append(f"remote.origin.url is {url or 'unset'!r}, not {origin!r}")
    return problems


def framework_problems(framework: Path, pin_ref: str, framework_origin: str | None) -> list[str]:
    problems: list[str] = []
    if not (framework / ".git").exists():
        return [f"{framework} is not a git checkout"]
    code, head = git(framework, "rev-parse", "HEAD")
    head = head.strip() if code == 0 else ""
    if not head:
        problems.append("framework: no HEAD")
    code, dirty = git(framework, "status", "--porcelain", "--ignored", "--untracked-files=all")
    if code == 0 and dirty.strip():
        changed = ", ".join(line.split(maxsplit=1)[-1] for line in dirty.splitlines()[:10])
        problems.append(f"framework checkout is not clean: {changed}")
    code, flagged = git(framework, "ls-files", "-v")
    if code == 0 and any(line[:1] in "Sh" for line in flagged.splitlines()):
        problems.append("framework checkout has skip-worktree or assume-unchanged entries")
    source = framework_origin
    if not source:
        code, source = git(framework, "config", "--local", "--get", "remote.origin.url")
        source = source.strip() if code == 0 else ""
    if not source:
        problems.append("framework: no origin to read the pin's commit from")
        return problems
    code, listed = git(
        framework, "ls-remote", source, f"refs/tags/{pin_ref}^{{}}", f"refs/tags/{pin_ref}",
        env=CLEAN_ENV,
    )  # fmt: skip
    shas = [line.split()[0] for line in listed.splitlines() if line.split()] if code == 0 else []
    if not shas:
        problems.append(f"framework: {source} carries no tag {pin_ref}")
    elif head and head not in shas:
        problems.append(
            f"framework checkout is at {head[:10]}, not at {pin_ref} as {source} carries it "
            f"({shas[0][:10]})"
        )
    return problems


def _plugin_version(text: str) -> str:
    block = re.search(r"(?ms)^plugin:[ \t]*$(.*?)(?=^\S|\Z)", text)
    if not block:
        return ""
    match = re.search(r"(?m)^[ \t]+version:[ \t]*[\"']?([^\"'#\r\n]+)", block.group(1))
    return match.group(1).strip() if match else ""


def default_branch_problems(root: Path, origin: str | None, branch: str, pin_ref: str) -> list[str]:
    """Fetch the default branch by the repository's URL (never ``origin``, whose name the
    config resolves) into its remote-tracking ref, then re-read the pin there."""
    if not branch:
        return ["no default branch named (SDLC_DEFAULT_BRANCH)"]
    source = origin
    if not source:
        code, source = git(root, "config", "--local", "--get", "remote.origin.url")
        source = source.strip() if code == 0 else ""
    if not source:
        return ["no origin URL to fetch the default branch from"]
    tracking = f"refs/remotes/origin/{branch}"
    # decision 33 (R49): past 50 minutes the fetch goes out on the workflow token, not the
    # App's, whose hour may have run out (the step's env carries SDLC_WORKFLOW_TOKEN)
    app_token.fall_back_if_stale(root)
    code, out = git(root, "fetch", source, f"+refs/heads/{branch}:{tracking}", env=CLEAN_ENV)
    if code != 0:
        return [f"cannot fetch the default branch {branch} from {source}: {out.strip()}"]
    code, text = git(root, "--no-replace-objects", "show", f"{tracking}:sdlc.yaml")
    version = _plugin_version(text) if code == 0 else ""
    fresh = f"v{version.removeprefix('v')}" if version else ""
    if fresh != pin_ref:
        return [
            f"the default branch's pin is {fresh or 'unreadable'} after a fresh fetch, the "
            f"job's pin is {pin_ref}"
        ]
    return []


def problems(
    root: Path,
    framework: Path,
    pin_ref: str,
    origin: str | None,
    framework_origin: str | None,
    default_branch: str,
) -> list[str]:
    found = config_problems(root) + origin_problems(root, origin)
    found += framework_problems(framework, pin_ref, framework_origin)
    if not found:
        found += default_branch_problems(root, origin, default_branch, pin_ref)
    return found


def main(argv: list[str] | None = None) -> int:
    import os

    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--root", default=".")
    p.add_argument("--framework", default="framework")
    p.add_argument("--pin-ref", required=True, help="the pin step's output, v<version>")
    p.add_argument("--origin", default=None, help="the project repository's URL")
    p.add_argument("--framework-origin", default=None, help="the framework repository's URL")
    p.add_argument("--default-branch", default=os.environ.get("SDLC_DEFAULT_BRANCH", ""))
    args = p.parse_args(argv)
    if args.pin_ref.startswith("-"):
        print("--pin-ref must be a tag name", file=sys.stderr)
        return EXIT_REFUSED
    root = Path(args.root).resolve()
    found = problems(
        root, root / args.framework, args.pin_ref, args.origin, args.framework_origin,
        args.default_branch,
    )  # fmt: skip
    if found:
        for problem in found:
            print(f"checkout verification failed: {problem}", file=sys.stderr)
        return EXIT_REFUSED
    print(f"verified={args.framework}@{args.pin_ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
