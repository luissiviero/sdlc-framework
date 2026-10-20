"""The release workflow's steps (build guide step 32.3; decision 13; OPERATING_MODEL section
4, gate (e): the owner's approving review of the build PR, on which the merge App merges
(decision 36), "plus the release label" only when sdlc.yaml declares a real production).

    python cli.py run --root <project> --repo <owner/repo> --pr <number>
                      [--event closed|labeled] [--merge-sha <sha>] [--change-id <id>]
    python cli.py record --root <project> --id <id> --pr <number> [--merge-sha <sha>]

``.github/workflows/sdlc-release.yml`` calls ``run`` on the owner's merge of a build PR and,
when production is declared, on the release label; its second job calls ``record`` after a
release that ran. Neither is a phase run: no ``claude`` starts and no hook fires here, so
``run`` checks the approval itself with the production-gate hook's own function
(``release/approval.py``; article p.36-37). Every step prints one line
``release: <key>: <value>``:

1. ``config``: ``sdlc.yaml: deploy`` (action, production, command);
2. ``change``: ``--change-id``, else the one ``changes/<id>-<slug>/`` the PR touches (zero or
   several -> ``skip``);
3. ``pr``: the PR must be merged and be the change's build PR, head ``sdlc/<id>/c`` (else
   ``skip``: an owner's PR that touches ``changes/<id>-*/`` after the merge never releases
   again);
4. ``phase``: ``status.yaml`` read as on the default branch must be at phase (e) (else
   ``skip``), and the PR must be the change's recorded build PR;
4b. ``gate`` (0.3.1, issue #66): gate (e) must have a result on the merged copy
   (``gate.phase`` ``e`` with any result) and the merged copy's ``evidence/gate-e.json`` must
   not be a record whose ``commands`` check is still deferred to the runner (issue #91: a
   job that died between the session and the runner's step leaves one, which says passed
   and is not). The deploy run sets phase (e) at its start, before the REVIEW.md pass, so a
   build PR merged while that run is still running carries no gate (e) result: ``skip``,
   never a release of code the review has not judged; the pull request the run opens
   afterwards carries the result and is released on its merge;
4c. ``parked`` (0.3.1, issue #68): the merged copy carries a ``parked_reason`` (gate (e)
   parked and the owner merged anyway): the reason is printed, and the release needs the
   release label whatever ``deploy.production`` says;
4a. ``released`` (0.3.1, issue #66): the merged copy, the ref ``refs/sdlc/released/<id>`` on
   the remote or the work branch's copy of ``status.yaml`` (``sdlc/<id>/c``) already records
   a release of this change -> ``skip``: one release per change, whatever pull request,
   label or dispatch fired the workflow. A remote that cannot be read is exit 2 (fail
   closed: a release is never run on a read that did not happen); a remote without the ref,
   the branch or the file proceeds;
5. ``approval``: with production declared or a park, the release label applied by a person
   (the only route: decision 5, a run cannot approve itself); without it ``waiting`` +
   ``route`` and a green exit (the ``labeled`` event re-runs the workflow);
6. ``done`` / ``exit``: ``deploy.action none`` or an empty ``deploy.command`` release nothing;
   otherwise the command runs on the runner and its output streams to the log. After a
   command that exited 0, ``run`` writes ``released=true`` and ``change_id=<id>`` to
   ``$GITHUB_OUTPUT`` for the record job and prints ``record: pending``;
7. ``record`` (0.3.1, issue #66; the ``record`` verb, run by the workflow's second job, the
   only one with ``contents: write`` - the first job, which runs the project's own toolchain
   and ``deploy.command``, holds a read-only token): ``released_at``, ``released_sha`` and
   ``released_pr`` committed into ``status.yaml`` on top of the work branch's tip, pushed to
   ``sdlc/<id>/c`` (so the next pull request from that branch carries them) and to the ref
   ``refs/sdlc/released/<id>`` (no branch: GitHub's "automatically delete head branches"
   cannot remove it, and no pull request ever comes from it), on top of the merge commit
   when the branch is already gone. A push that fails is exit 1, so a release that ran
   without its record is seen; a record already there is exit 0.

``$GITHUB_STEP_SUMMARY`` gets the same lines when it is set.

The command runs without a shell (argument lists only): one command, or several joined by
``&&`` that run in order and stop at the first failure; a word with ``*``, ``?`` or ``[`` is
expanded against the project root like a shell glob (kept literal when nothing matches);
other shell operators (``|``, ``;``, ``||``, redirections) are refused as a configuration
error. The executable is resolved on PATH (``.cmd``/``.exe`` shims on Windows).

Exit codes: 0 done, skip or waiting (``record``: stored or already there) · 1 the release
command failed, or the record could not be pushed (a failed release is red: infrastructure,
not a park) · 2 usage or configuration error, or a remote record that could not be read.
"""

from __future__ import annotations

import argparse
import glob
import inspect
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate import gate as gate_mod  # noqa: E402
from gate import risk as risk_mod  # noqa: E402
from hooks._common import ConfigError, config_flag, load_sdlc_config  # noqa: E402
from release import approval as approval_mod  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops, yamlish  # noqa: E402
from state import status as status_mod  # noqa: E402

CHANGE_FILE_RE = re.compile(r"^changes/(\d{4})-[^/]+/")
UNSUPPORTED = ("||", "|", ";", ">", ">>", "<", "&", "2>", "2>&1", "(", ")")
DEFAULT_TIMEOUT = 900  # seconds, when sdlc.yaml has no gate.command_timeout
RECORD_GIT_TIMEOUT = 120  # seconds per git call of the record (a fetch or a push)
RECORD_PUSH_ATTEMPTS = 3  # a push rejected by a concurrent push is retried on the new tip
RECORD_COMMIT = "release({id}): record the release of pull request #{pr}"
# decision 35: the record job stores the (e) merge's risk acceptance when no release ran
ACCEPTANCE_COMMIT = "release({id}): record the risk acceptance of pull request #{pr}'s merge"
RELEASED_REF = "refs/sdlc/released/{id}"  # not a branch: survives the head branch's deletion


class UsageError(RuntimeError):
    pass


def _github() -> tuple[Any, str]:
    return approval_mod.load_github()


def _call(github: Any, name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    return approval_mod._call(github, name, *args, **kwargs)


def _read_status(change_dir: Path, production: bool = False) -> tuple[Any, str]:
    """(Status, note). ``read_status(change_dir, on_default_branch=True)`` when the state
    module has the parameter (plus ``production=production`` when it has that one too);
    otherwise the plain read and a note saying so."""
    from state import status as status_mod

    reader = status_mod.read_status
    try:
        params = inspect.signature(reader).parameters
    except (TypeError, ValueError):
        params = {}
    if "on_default_branch" in params:
        kwargs: dict[str, Any] = {"on_default_branch": True}
        if "production" in params:
            kwargs["production"] = production
        return reader(change_dir, **kwargs), ""
    note = "state/status.py read_status has no on_default_branch: plain read"
    return reader(change_dir), note


def command_chain(command: str, root: Path, posix: bool | None = None) -> list[list[str]]:
    """The argument lists of ``deploy.command``: one per ``&&``-joined step."""
    posix = (os.name != "nt") if posix is None else posix
    lexer = shlex.shlex(command, posix=posix, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError as exc:
        raise UsageError(f"deploy.command cannot be parsed: {exc}") from exc
    chain: list[list[str]] = [[]]
    for token in tokens:
        if token == "&&":
            chain.append([])
            continue
        if token in UNSUPPORTED or token.startswith((">", "<", "|", ";")):
            raise UsageError(
                f"deploy.command uses the shell operator {token!r}; the release command runs "
                "without a shell: give one command, or steps joined by &&"
            )
        if not posix and len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
            token = token[1:-1]
        chain[-1].append(token)
    if any(not step for step in chain):
        raise UsageError("deploy.command has an empty step")
    return [_expand(step, root) for step in chain]


def _expand(step: list[str], root: Path) -> list[str]:
    out = [step[0]]
    for word in step[1:]:
        if any(ch in word for ch in "*?["):
            found = sorted(glob.glob(word, root_dir=str(root)))
            out += found or [word]
        else:
            out.append(word)
    return out


def _timeout(config: Mapping[str, Any]) -> int:
    gate_cfg = config.get("gate") if isinstance(config.get("gate"), dict) else {}
    try:
        return int(gate_cfg.get("command_timeout", DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


def run_command(command: str, root: Path, timeout: int) -> tuple[int, str]:
    """Run the chain; (exit code of the first failing step or 0, what happened)."""
    for argv in command_chain(command, root):
        exe = shutil.which(argv[0], path=os.environ.get("PATH")) or argv[0]
        sys.stdout.flush()
        try:
            proc = subprocess.run([exe, *argv[1:]], cwd=str(root), timeout=timeout)
        except FileNotFoundError:
            return 127, f"{argv[0]}: not found"
        except subprocess.TimeoutExpired:
            return 124, f"{argv[0]}: timed out after {timeout}s"
        except OSError as exc:
            return 126, f"{argv[0]}: {exc}"
        if proc.returncode != 0:
            return proc.returncode, f"{argv[0]} exited {proc.returncode}"
    return 0, "ok"


# --- the release record (issue #66) ----------------------------------------------------------
class RemoteUnreadable(RuntimeError):
    """The remote record could not be read: the release fails closed (exit 2)."""


def _released_line(st: Any) -> str:
    pr = f" (pull request #{st.released_pr})" if st.released_pr else ""
    sha = f" as {st.released_sha}" if st.released_sha else ""
    return f"released{sha} at {st.released_at or '?'}{pr}"


def _status_at(root: Path, ref: str, rel_status: str, git: Callable[..., tuple[int, str]]):
    """The ``Status`` in ``<ref>:<rel_status>``, or None when the commit has no such file;
    ``RemoteUnreadable`` when the file is there and cannot be read."""
    code, text = git(root, "show", f"{ref}:{rel_status}")
    if code != 0:
        return None
    try:
        data = yamlish.loads(text)
        if not isinstance(data, dict):
            raise ValueError("not a mapping")
        return status_mod.Status.from_dict(data)
    except (ValueError, TypeError) as exc:
        raise RemoteUnreadable(f"{ref}: {rel_status} could not be read: {exc}") from exc


def _remote_ref(
    root: Path, ref: str, git: Callable[..., tuple[int, str]], heads: bool = False
) -> bool:
    """Whether ``origin`` carries ``ref``; ``RemoteUnreadable`` when it cannot be asked."""
    args = ("ls-remote", "--heads", "origin", ref) if heads else ("ls-remote", "origin", ref)
    code, out = git(root, *args)
    if code != 0:
        raise RemoteUnreadable(f"origin could not be read (git ls-remote exited {code})")
    return bool(out.strip())


def _fetch(root: Path, ref: str, git: Callable[..., tuple[int, str]]) -> None:
    code, _ = git(root, "fetch", "--quiet", "origin", ref)
    if code != 0:
        raise RemoteUnreadable(f"{ref} could not be fetched (git fetch exited {code})")


def remote_record(
    root: Path, change_id: str, rel_status: str, git: Callable[..., tuple[int, str]]
) -> tuple[Any, str]:
    """(the release record the remote carries, or None; where it came from or why there is
    none). The ref ``refs/sdlc/released/<id>`` first, then the work branch ``sdlc/<id>/c``.
    A remote that cannot be asked, fetched or read raises ``RemoteUnreadable``: the caller
    fails closed. No ``origin`` remote (a by-hand run on a bare checkout) is "no remote"."""
    code, remotes = git(root, "remote")
    if code != 0 or "origin" not in remotes.split():
        return None, "no origin remote"
    ref = RELEASED_REF.format(id=change_id)
    branch = c.work_branch(change_id, "c")
    if _remote_ref(root, ref, git):
        _fetch(root, ref, git)
        st = _status_at(root, "FETCH_HEAD", rel_status, git)
        if st is not None and st.released:
            return st, ref
        if st is None or not st.risk_acceptances:
            raise RemoteUnreadable(f"{ref} is on the remote but carries no release record")
        # decision 35: the record job stored the (e) merge's risk acceptance there before
        # any release ran (a declared production waiting for its label); the work branch is
        # still read, since a push of two refspecs is not atomic
    if not _remote_ref(root, branch, git, heads=True):
        return None, f"neither {ref} nor the work branch {branch} is on the remote"
    _fetch(root, f"refs/heads/{branch}", git)
    st = _status_at(root, "FETCH_HEAD", rel_status, git)
    if st is None:
        return None, f"{branch} carries no {rel_status}"
    if st.released:
        return st, branch
    return None, f"no release record on {branch}"


def _records_all(st: Any, release: bool, acceptance: dict[str, Any] | None) -> bool:
    """Whether ``st`` already carries what the record job stores: the release record (when
    ``release``) and the acceptance line of the same merge (when one is given)."""
    if release and not st.released:
        return False
    if acceptance is None:
        return True
    return any(
        line.get("pr") == acceptance.get("pr")
        and (line.get("details") or {}).get("phase")
        == (acceptance.get("details") or {}).get("phase")
        for line in st.risk_acceptances
    )


def store_release_record(
    root: Path,
    change_id: str,
    rel_status: str,
    pr_number: int,
    merge_sha: str | None,
    git: Callable[..., tuple[int, str]],
    release: bool = True,
    acceptance: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Commit the release record into ``status.yaml`` and push it: (stored, what happened).

    The commit sits on the work branch's tip when ``sdlc/<id>/c`` is still on the remote
    (a later pull request from it then carries the record), else on the ref's tip when the
    ref is there, else on the merge commit the release checked out; it is pushed to the
    branch (when there) and always to the ref
    ``refs/sdlc/released/<id>``, which no branch deletion touches. A temporary worktree keeps
    the checkout as it is; a push rejected by a concurrent push is retried on the new tip,
    ``RECORD_PUSH_ATTEMPTS`` times. The push takes its credential from its environment
    (``approval.make_git`` → ``state/gitops.py network_env``, the job's ``GITHUB_TOKEN``):
    no checkout persists one in ``.git/config`` (decision 33, R49), so a worktree needs
    nothing of its own. A record already there, on the ref or the branch, is "stored".

    Decision 35 (1.0.15): ``acceptance`` is the (e) merge's ``risk_acceptances`` line, stored
    in the same commit; with ``release`` False the commit carries that line alone (the
    merge accepted a risk and no release ran: none is configured, or a declared production
    waits for its label), and ``remote_record`` reads such a ref as carrying no release.
    """
    branch = c.work_branch(change_id, "c")
    ref = RELEASED_REF.format(id=change_id)
    try:
        on_ref = _remote_ref(root, ref, git)
        if on_ref:
            _fetch(root, ref, git)
            st = _status_at(root, "FETCH_HEAD", rel_status, git)
            if st is not None and _records_all(st, release, acceptance):
                return True, f"{ref} already records it" + (
                    f": {_released_line(st)}" if st.released else ""
                )
        on_branch = _remote_ref(root, branch, git, heads=True)
    except RemoteUnreadable as exc:
        return False, str(exc)
    why = "not attempted"
    for _attempt in range(RECORD_PUSH_ATTEMPTS):
        if on_branch or on_ref:
            try:
                _fetch(root, f"refs/heads/{branch}" if on_branch else ref, git)
            except RemoteUnreadable as exc:
                return False, str(exc)
            base = "FETCH_HEAD"
        else:
            base = "HEAD"  # the merge commit the release checked out
        worktree = Path(tempfile.mkdtemp(prefix="sdlc-release-"))
        try:
            code, _ = git(root, "worktree", "add", "--detach", "--quiet", str(worktree), base)
            if code != 0:
                return False, f"a worktree on {base} could not be made (exit {code})"
            try:
                change_dir = (worktree / rel_status).parent
                st = status_mod.read_status(change_dir)
            except (OSError, ValueError) as exc:
                return False, f"{base}: {rel_status} could not be read: {exc}"
            if _records_all(st, release, acceptance):
                where = branch if on_branch else (ref if on_ref else "the merge commit")
                return True, f"{where} already records it" + (
                    f": {_released_line(st)}" if st.released else ""
                )
            if release and not st.released:
                st.record_release(pr_number, merge_sha)
            if acceptance is not None:
                risk_mod.record_acceptance(st, acceptance)
                st.touch()
                st.validate()
            status_mod.write_status(change_dir, st)
            identity = []
            code, name = git(worktree, "config", "user.name")
            if code != 0 or not name.strip():
                identity = [
                    "-c", f"user.name={gitops.BOT_LOGIN}",
                    "-c", f"user.email={gitops.BOT_EMAIL}",
                ]  # fmt: skip
            message = (RECORD_COMMIT if release else ACCEPTANCE_COMMIT).format(
                id=change_id, pr=pr_number
            )
            code, _ = git(worktree, "add", "--", rel_status)
            if code == 0:
                code, _ = git(
                    worktree, *identity, "commit", "--quiet", "--only", "-m",
                    message, "--", rel_status,
                )  # fmt: skip
            if code != 0:
                return False, f"the record could not be committed on {base} (exit {code})"
            # the branch fast-forwards or is rejected (a concurrent push: the next attempt
            # re-applies the record on the new tip); the ref is forced, since it only has to
            # point at a commit that carries the record, and a rejected branch push may have
            # left it on an earlier attempt's commit
            targets = [f"+HEAD:{ref}"] + ([f"HEAD:refs/heads/{branch}"] if on_branch else [])
            code, _ = git(worktree, "push", "--quiet", "origin", *targets)
            if code == 0:
                _code, sha = git(worktree, "rev-parse", "--short", "HEAD")
                where = f"{ref} and {branch}" if on_branch else f"{ref} ({branch} is gone)"
                return True, f"stored on {where} ({sha.strip() or 'pushed'})"
            pushed_to = " and ".join(t.split(":", 1)[1] for t in targets)
            why = f"the push to {pushed_to} was rejected"
            why += f" (git push exited {code})"
        finally:
            git(root, "worktree", "remove", "--force", str(worktree))
            shutil.rmtree(worktree, ignore_errors=True)
    return False, why


def merge_acceptance(
    change_dir: Path,
    st: Any,
    pr: Mapping[str, Any],
    pr_number: int,
    merge_sha: str | None,
    config: dict[str, Any],
    env: Mapping[str, str] | None = None,
    repo: str | None = None,
    reviews: Callable[[], dict[str, Any]] | None = None,
) -> tuple[dict[str, Any] | None, str] | None:
    """Decision 35: the ``risk_acceptances`` line of the (e) merge, from the merged copy's
    gate records (the items no earlier act accepted, ``risk.banner_entries``) and GitHub's
    record of the act (who, when, the body it showed); (None, why) when no act of the
    owner's account accepted (``unpark.is_owner_actor``, decision 34's one rule), None when
    nothing was asked. The owner's own merge accepts, as before R22 (fallback C1, or a merge
    through the bypass). Since R22 a merge by anyone else - the merge App is a ``[bot]`` and
    never accepts a risk - is accepted by the owner's approving review, on which the merge
    App merged (choice 242, point 2): ``reviews`` reads the pull request's reviews, and the
    owner's latest review that approves or requests changes must approve."""
    from state import unpark  # noqa: PLC0415

    items = risk_mod.new_items(risk_mod.banner_entries(change_dir, "e", st))
    if not items:
        return None
    by = str(pr.get("merged_by") or "").strip()
    if not unpark.is_owner_actor(by, config, env, repo):
        approval = _owner_approval(reviews, config, env, repo)
        if approval is not None:
            line = risk_mod.acceptance_line(
                "e",
                items,
                str(approval.get("author")),
                str(approval.get("at") or "").strip() or gate_mod._now(),
                int(pr_number),
                str(approval.get("commit") or "") or merge_sha,
                risk_mod.banner_shown(pr.get("body"), items),
                via=risk_mod.ACCEPT_VIA_APPROVAL,
            )
            return line, ""
        return None, (
            f"not accepted: merged by {by or 'an unknown account'}, not the owner's account, "
            f"and no approving review by the owner (decisions 34, 35 and 36): {', '.join(items)}"
        )
    line = risk_mod.acceptance_line(
        "e",
        items,
        by,
        str(pr.get("merged_at") or "").strip() or gate_mod._now(),
        int(pr_number),
        merge_sha,
        risk_mod.banner_shown(pr.get("body"), items),
    )
    return line, ""


DECISIVE_REVIEWS = ("APPROVED", "CHANGES_REQUESTED", "DISMISSED")


def _owner_approval(
    reviews: Callable[[], dict[str, Any]] | None,
    config: dict[str, Any],
    env: Mapping[str, str] | None,
    repo: str | None,
) -> dict[str, Any] | None:
    """The owner's latest review that approves, requests changes or was dismissed, when it
    approves (the merge step's reading, ``ci/merge_step.py owner_approval``); None without a
    reader, on a failed read, or when it does not approve."""
    from state import unpark  # noqa: PLC0415

    if reviews is None:
        return None
    got = reviews()
    if not isinstance(got, dict) or not got.get("ok"):
        return None
    latest = None
    for review in got.get("reviews") or []:
        if str(review.get("state") or "").upper() not in DECISIVE_REVIEWS:
            continue
        if unpark.is_owner_actor(review.get("author"), config, env, repo):
            latest = review
    if latest is None or str(latest.get("state")).upper() != "APPROVED":
        return None
    return latest


def _step_output(env: Mapping[str, str], lines: dict[str, str]) -> str | None:
    """Append ``key=value`` lines to ``$GITHUB_OUTPUT`` (the record job reads them); the
    reason when they could not be written, else None."""
    target = env.get("GITHUB_OUTPUT")
    if not target:
        return None
    try:
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            for key, value in lines.items():
                fh.write(f"{key}={value}\n")
    except OSError as exc:
        return f"{target}: {exc}"
    return None


def record(
    args: argparse.Namespace,
    *,
    env: Mapping[str, str] | None = None,
    git: Callable[..., tuple[int, str]] | None = None,
    out: Callable[[str], None] = print,
) -> int:
    """The ``record`` verb: the workflow's second job, after a release that ran."""
    env = os.environ if env is None else env
    git = git or approval_mod.make_git(RECORD_GIT_TIMEOUT)
    lines: list[str] = []

    def say(key: str, value: str) -> None:
        line = f"release: {key}: {value}"
        lines.append(line)
        out(line)

    code = _record(args, git, say)
    _summary(lines, env)
    return code


def _record(args, git, say) -> int:
    root = Path(args.root).resolve()
    if not c.ID_RE.match(args.id or ""):
        say("error", f"--id must be four digits, got {args.id!r}")
        return 2
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        say("error", f"no changes/{args.id}-<slug>/ folder at {root}")
        return 2
    rel_status = str(status_mod.status_path(change_dir).relative_to(root)).replace("\\", "/")
    release = str(getattr(args, "released", "true") or "").strip().lower() == "true"
    acceptance = None
    raw = str(getattr(args, "acceptance", "") or "").strip()
    if raw:
        try:
            acceptance = json.loads(raw)
            risk_mod.validate_acceptances([acceptance])
        except ValueError as exc:
            say("error", f"--acceptance is not a risk_acceptances line: {exc}")
            return 2
    if not release and acceptance is None:
        say("record", "nothing to store: no release ran and no risk was accepted")
        return 0
    try:
        stored, what = store_release_record(
            root, args.id, rel_status, int(args.pr), args.merge_sha, git, release, acceptance
        )
    except TimeoutError as exc:
        stored, what = False, f"git took too long: {exc}"
    if stored:
        say("record", what)
        return 0
    lost = "the release ran without its record" if release else "the risk acceptance is unrecorded"
    say("record", f"not stored: {what}; {lost}")
    return 1


def _summary(lines: list[str], env: Mapping[str, str]) -> None:
    target = env.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    try:
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("## sdlc release\n\n")
            fh.write("".join(f"- `{line}`\n" for line in lines))
            fh.write("\n")
    except OSError:
        pass  # the summary is a convenience; the log has the same lines


def release(
    args: argparse.Namespace,
    *,
    env: Mapping[str, str] | None = None,
    github: Any = None,
    git: Callable[..., tuple[int, str]] | None = None,
    record_git: Callable[..., tuple[int, str]] | None = None,
    out: Callable[[str], None] = print,
) -> int:
    """``git`` is the approval's runner (``approval.run_git``, 30 s per call); ``record_git``
    reads the remote's release record (a fetch may take longer: ``RECORD_GIT_TIMEOUT``)."""
    env = os.environ if env is None else env
    lines: list[str] = []

    def say(key: str, value: str) -> None:
        line = f"release: {key}: {value}"
        lines.append(line)
        out(line)

    code = _release(args, env, github, git, record_git, say)
    _summary(lines, env)
    return code


def _release(args, env, github, git, record_git, say) -> int:
    root = Path(args.root).resolve()
    # (1) configuration
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        say("error", str(exc))
        return 2
    if not config:
        say("error", f"no sdlc.yaml at {root}")
        return 2
    deploy = config.get("deploy") or {}
    if not isinstance(deploy, dict):
        say("error", "sdlc.yaml: deploy must be a mapping")
        return 2
    action = str(deploy.get("action") or "none").strip().lower()
    try:
        production = config_flag(config, "deploy", "production")
    except ConfigError as exc:
        say("error", f"{exc}; the release fails closed")
        return 2
    command = str(deploy.get("command") or "").strip()
    say(
        "config",
        f"action={action} production={str(production).lower()} "
        f"command={'set' if command else 'empty'} event={args.event}",
    )
    if github is None:
        github, why = _github()
        if github is None:
            say("error", why)
            return 2
    # (2) the change
    change_id = args.change_id
    if change_id:
        if not c.ID_RE.match(change_id):
            say("error", f"--change-id must be four digits, got {change_id!r}")
            return 2
    else:
        files = _call(github, "pr_files", args.repo, args.pr, cwd=str(root))
        if not files.get("ok"):
            say("error", f"cannot list the files of #{args.pr}: {files.get('reason')}")
            return 2
        ids = sorted(
            {m.group(1) for f in files.get("files") or [] if (m := CHANGE_FILE_RE.match(f))}
        )
        if len(ids) != 1:
            why = "no change folder" if not ids else f"several change folders ({', '.join(ids)})"
            say("skip", f"pull request #{args.pr} touches {why}")
            return 0
        change_id = ids[0]
    say("change", change_id)
    # (3) the pull request must be merged
    pr = _call(github, "pr_by_number", args.repo, args.pr, cwd=str(root))
    if not pr.get("ok"):
        say("error", f"cannot read #{args.pr}: {pr.get('reason')}")
        return 2
    if not pr.get("merged"):
        say("skip", f"pull request #{args.pr} is not merged")
        return 0
    build_head = c.work_branch(change_id, "c")
    if pr.get("head_ref") != build_head:
        say(
            "skip",
            f"pull request #{args.pr} (head {pr.get('head_ref') or '?'}) is not the build PR "
            f"{build_head} of change {change_id}",
        )
        return 0
    merge_sha = args.merge_sha or pr.get("merge_commit_sha")
    say("pr", f"#{args.pr} merged{f' as {merge_sha}' if merge_sha else ''}")
    # (4) the change is at phase (e), read as on the default branch
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        say("skip", f"no changes/{change_id}-<slug>/ folder at {root}")
        return 0
    try:
        raw = status_mod.read_status(change_dir)  # the merged copy as it is: no derivation
        st, note = _read_status(change_dir, production)
    except Exception as exc:  # noqa: BLE001 - a broken status.yaml is a configuration error
        say("error", f"{change_id} status.yaml could not be read: {exc}")
        return 2
    if note:
        say("note", note)
    if st.phase != "e":
        say("skip", f"change {change_id} is at phase {st.phase}, not e")
        return 0
    if st.build_pr is not None and int(st.build_pr) != int(args.pr):
        # the recorded build PR is the one the approval belongs to (0.2.27)
        say(
            "skip",
            f"pull request #{args.pr} is not the build PR #{st.build_pr} status.yaml records",
        )
        return 0
    say("phase", "e")
    # (4b) gate (e) must have a result on the merged copy, and a record whose commands check
    # the runner ran (issue #66; issue #91's deferred mark)
    if raw.gate.phase != "e" or not raw.gate.result:
        say(
            "skip",
            f"change {change_id} has no gate (e) result on the merged copy "
            f"(gate: {raw.gate.phase or '-'}/{raw.gate.result or '-'}): the build PR was merged "
            "while the deploy run was still running, before its REVIEW.md pass; the pull "
            "request that run opens carries the result and releases on its merge",
        )
        return 0
    gate_file = change_dir / art.EVIDENCE_DIR / art.GATE_RESULT.format(phase="e")
    try:
        gate_record = json.loads(gate_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        gate_record = None
    if not isinstance(gate_record, dict):
        say(
            "skip",
            f"change {change_id} has no readable evidence/{gate_file.name} on the merged "
            "copy: gate (e)'s record is what the release judges, and it is not there",
        )
        return 0
    if gate_mod.deferred_commands(gate_record):
        say(
            "skip",
            f"gate (e) of change {change_id} recorded its commands check (or its evidence "
            "logs, item 3b) as deferred to the runner and the runner never ran it (issue "
            "#91): the gate is not passed; re-run phase (e), then merge the pull request it "
            "opens",
        )
        return 0
    say("gate", f"e/{raw.gate.result}")
    # (4c) a parked change merged anyway (issue #68): the reason is shown, the label required
    parked = (raw.parked_reason or "").strip()
    if parked:
        say("parked", f"gate ({raw.gate.phase}) parked change {change_id}: {parked}")
    # (4d) decision 35: the owner's merge accepted the risk lines the build PR's banner
    # showed; the record job stores the line, whatever the release does next
    accepted = merge_acceptance(
        change_dir, raw, pr, args.pr, merge_sha, config, env, args.repo,
        reviews=lambda: _call(github, "pr_reviews", args.repo, args.pr, cwd=str(root)),
    )  # fmt: skip
    if accepted is not None:
        line, why = accepted
        if line is None:
            say("risk", why)
        else:
            items = ", ".join(line["details"]["items"])
            shown = "shown" if line["details"]["banner_shown"] else "NOT shown"
            act = "approving review" if line["via"] == risk_mod.ACCEPT_VIA_APPROVAL else "merge"
            say("risk", f"accepted by {line['by']}'s {act}: {items} (banner {shown})")
            problem = _step_output(
                env, {"risk_acceptance": json.dumps(line, sort_keys=True), "change_id": change_id}
            )
            if problem:
                say("error", f"the record job's outputs could not be written ({problem})")
                return 1
    # (4a) one release per change (issue #66): the merged copy, then the remote's record
    rel_status = str(status_mod.status_path(change_dir).relative_to(root)).replace("\\", "/")
    if raw.released:
        say("skip", f"change {change_id} was already {_released_line(raw)}")
        return 0
    record_git = record_git or approval_mod.make_git(RECORD_GIT_TIMEOUT)
    try:
        recorded, where = remote_record(root, change_id, rel_status, record_git)
    except (RemoteUnreadable, TimeoutError) as exc:
        say("error", f"the remote's release record could not be read ({exc}); the release "
            "fails closed")  # fmt: skip
        return 2
    if recorded is not None:
        say("skip", f"change {change_id} was already {_released_line(recorded)} ({where})")
        return 0
    say("note", f"no release record: {where}")
    # (5) the release approval (decision 13): production, or a park the owner merged over
    if production or parked:
        labels = pr.get("labels")
        result = approval_mod.release_approval(
            root,
            config,
            env,
            pr_number=args.pr,
            repo=args.repo,
            git=git,
            github=github,
            pr_labels=list(labels) if isinstance(labels, list) else None,
        )
        if not result.approved:
            if parked:
                say(
                    "waiting",
                    f"change {change_id} was merged while parked ({parked}); a parked change "
                    f"releases only after {approval_mod.RELEASE_LABEL}, whatever "
                    f"deploy.production says ({result.detail})",
                )
            else:
                say("waiting", result.detail)
            say("route", f"apply {approval_mod.RELEASE_LABEL} on #{args.pr}")
            return 0
        say("approval", f"{result.how} ({result.detail})")
    # (6) the adapter's action
    if action == "none":
        say("done", "nothing to release (deploy.action none)")
        return 0
    if not command:
        say("done", "release prepared in the PR; deploy.command is empty, nothing runs")
        return 0
    say("run", command)
    try:
        code, what = run_command(command, root, _timeout(config))
    except UsageError as exc:
        say("error", str(exc))
        return 2
    say("exit", str(code))
    if code != 0:
        say("failed", what)
        return 1
    say("done", f"deploy.command exited 0 (deploy.action {action})")
    # (7) the record is the second job's: it holds the write token this job never does
    problem = _step_output(env, {"released": "true", "change_id": change_id})
    if problem:
        say("error", f"the record job's outputs could not be written ({problem}): the release "
            "ran and would run again on the next event")  # fmt: skip
        return 1
    say("record", f"pending: the record job stores it on {c.work_branch(change_id, 'c')} and "
        f"{RELEASED_REF.format(id=change_id)}")  # fmt: skip
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-release",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="verb", required=True)
    run = sub.add_parser("run", help="the release workflow's step")
    run.add_argument("--root", default=".")
    run.add_argument("--repo", required=True, help="owner/repo")
    run.add_argument("--pr", required=True, type=int, help="the build PR's number")
    run.add_argument("--event", choices=("closed", "labeled"), default="closed")
    run.add_argument(
        "--merge-sha", default=None, help="shown on the pr line only; never an approval"
    )
    run.add_argument("--change-id", default=None)
    rec = sub.add_parser("record", help="the record job's step, after a release that ran")
    rec.add_argument("--root", default=".")
    rec.add_argument("--id", required=True, help="the change id the run step printed")
    rec.add_argument("--pr", required=True, type=int, help="the build PR's number")
    rec.add_argument("--merge-sha", default=None, help="recorded as released_sha")
    rec.add_argument(
        "--released",
        default="true",
        help="'true' when the release ran (the default, as before 1.0.15); anything else "
        "stores only --acceptance",
    )
    rec.add_argument(
        "--acceptance",
        default="",
        help="decision 35: the (e) merge's risk_acceptances line as JSON, from the run step",
    )
    return p


def main(argv: list[str] | None = None, **inject: Any) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:  # argparse: usage error
        return 2 if exc.code else 0
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
    if args.verb == "record":
        inject.pop("github", None)
        inject.pop("record_git", None)
        return record(args, **inject)
    return release(args, **inject)


if __name__ == "__main__":
    sys.exit(main())
