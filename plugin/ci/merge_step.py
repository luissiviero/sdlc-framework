"""Gate (deploy) is the owner's approving review; the merge App merges on it (decision 36; R22).

    python framework/plugin/ci/merge_step.py doorbell --root . --repo owner/name
    python framework/plugin/ci/merge_step.py not-build --root . --repo owner/name
    python framework/plugin/ci/merge_step.py merge --root . --repo owner/name --pr N

Run by ``template/.github/workflows/sdlc-merge.yml`` on a checkout of the default branch, so
the owner's ``sdlc.yaml`` (never the pull request's) names the owner. No model runs here.

**doorbell** (``pull_request_review`` ``submitted``): an approving review by the owner's
account (``state/unpark.py is_owner_actor``, decision 34) on an open build PR (head
``sdlc/<id>/build``, or ``sdlc/<id>/c`` of a change in flight before R45, in this
repository) dispatches ``sdlc-merge.yml`` on the default branch with the pull request's
number. It holds no key and judges nothing else: the dispatched job
re-checks everything from the API, so a review-triggered run, whose workflow file may come
from the pull request, never reaches the merge App's key (the R22 proposal, "What to
settle", the App row). Any other review is a green skip that says why.

**not-build** (``pull_request``): every pull request that is not a framework build PR gets a
passing ``sdlc/review`` check ("not a build PR") on its head, so ruleset 2, which requires
that check, holds only build PRs (decision 36, point 5). A build PR is one whose head is
``sdlc/<id>/build``; its check is the review pass's, posted by the deploy run on its final
head. The merge step below reads the review findings and gate (deploy)'s record, not the check, so a
check posted on a wrong head is caught there. ``pr/cli.py upsert`` posts the same check on
the pull requests the workflow token opens or updates, whose events start no run.

**merge** (``workflow_dispatch``, in the ``sdlc-merge`` environment only the default branch
can use): the deterministic step of decision 36, point 2. In this order, each refusal a
green "wait" line, since a merge that cannot happen leaves the PR open and shows in the
digest (decisions 11 and 20):

1. the pull request is open, not a draft, into the default branch, its head
   ``sdlc/<id>/build`` in this repository, labelled ``sdlc:deploy-ready`` (or the
   ``sdlc:e-ready`` an older plugin applied) and not
   ``sdlc:needs-human``;
2. at its head, ``changes/<id>-<slug>/status.yaml`` says phase deploy, gate (deploy) passed, no
   park, and names this pull request as ``build_pr``; ``evidence/gate-deploy.json`` (or the
   letter's ``gate-e.json``) says ``wait`` and
   carries no deferred commands check (issue #91);
3. ``evidence/review-findings.json`` at the head has no Important finding, and every commit
   after the one it reviewed touches only the change's ``evidence/``, its ``status.yaml``
   and ``changes/.review-seen.json`` (the evidence and the run record);
4. ``sdlc/review`` is green on the head;
5. the owner's latest review that approves or requests changes approves, and every commit
   after the one it was submitted on is evidence or the run record, as in 3;
6. the approved commit already carries ``evidence/gate-deploy.json`` reading ``wait``: an
   approval given before gate (deploy) offered the PR, before the owner could read its
   banner, is no gate (deploy) (choice 250; the R22 double check, F3);
7. it merges at exactly that head through the merge App's token (``SDLC_MERGE_TOKEN``),
   a bypass actor of ruleset 1; the workflow token never merges (decision 4).

Output: ``merge: <what>`` lines on stdout and in ``$GITHUB_STEP_SUMMARY``; until R11's
approvals list exists they are the record of the approval and the merge (who, when, the
findings tally). Exit 0 on a merge or a wait; 1, a red run for R18's "Failed runs", on an
API failure or a merge call GitHub refuses (a conflict, a rule, a moved head).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <framework root>/plugin
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from review import findings as fmod  # noqa: E402

from gate import artifacts as art  # noqa: E402
from gate import gate as gate_mod  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402
from state import yamlish  # noqa: E402
from state.unpark import is_owner_actor  # noqa: E402

EXIT_OK, EXIT_FAILED = 0, 1
MERGE_WORKFLOW = "sdlc-merge.yml"
MERGE_TOKEN_ENV = "SDLC_MERGE_TOKEN"
E_READY = c.ready_label(c.DEPLOY)
# R45: a build PR an older plugin labelled carries ``sdlc:e-ready``; both offer it
E_READY_LABELS = c.ready_labels(c.DEPLOY)
# R45: the build head is ``sdlc/<id>/build``, or ``sdlc/<id>/c`` for a change in flight
BUILD_HEAD_RE = re.compile(rf"^sdlc/(?P<id>\d{{4}})/(?:{c.BUILD}|{c.PHASE_LETTERS[c.BUILD]})$")
DECISIVE = ("APPROVED", "CHANGES_REQUESTED", "DISMISSED")
LINES = {"doorbell": "merge-doorbell", "not-build": "review-check", "merge": "merge"}


class StepError(RuntimeError):
    """An API call failed or an input is missing: the run is red (R18's "Failed runs")."""


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _github():
    from pr import github  # noqa: PLC0415

    return github


def _say(verb: str, what: str, env: Mapping[str, str], stream=None) -> None:
    line = f"{LINES[verb]}: {' '.join(str(what).split())}"
    print(line, file=stream or sys.stdout)
    target = env.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    try:
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(f"{line}\n")
    except OSError:
        pass  # the summary is a convenience; the log has the same line


def read_payload(env: Mapping[str, str]) -> dict[str, Any]:
    path = str(env.get("GITHUB_EVENT_PATH") or "")
    if not path:
        raise StepError("GITHUB_EVENT_PATH is not set: no event to read")
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StepError(f"the event payload could not be read ({type(exc).__name__})") from exc
    if not isinstance(data, dict):
        raise StepError("the event payload is not an object")
    return data


def _config(root: Path) -> dict[str, Any]:
    try:
        return load_sdlc_config(str(root)) or {}
    except ConfigError as exc:
        raise StepError(f"{exc}: nothing is merged until it is fixed") from exc


def build_change_id(head_ref: Any) -> str | None:
    """The change id of a build PR's head ``sdlc/<id>/build`` (or the letter branch
    ``sdlc/<id>/c`` an older plugin cut, R45), else None."""
    found = BUILD_HEAD_RE.match(str(head_ref or ""))
    return found.group("id") if found else None


def only_evidence_since(
    github: Any, repo: str, base: str, head: str, change_dir_rel: str
) -> str | None:
    """None when every commit from ``base`` to ``head`` touches only what
    ``review/findings.py allowed_after_review`` lets through, else why not. ``StepError`` on
    an API failure."""
    if base == head:
        return None
    found = github.compare_commits(repo, base, head)
    if not found.get("ok"):
        raise StepError(f"{base[:10]}...{head[:10]} could not be compared: {found.get('reason')}")
    if found.get("status") not in ("ahead", "identical"):
        return f"the head {head[:10]} does not follow {base[:10]} ({found.get('status')})"
    files = found.get("files") or []
    other = [f for f in files if not fmod.allowed_after_review(f, change_dir_rel)]
    if other:
        shown = ", ".join(other[:5]) + (" ..." if len(other) > 5 else "")
        return (
            f"the commits after {base[:10]} change more than evidence and the run record: {shown}"
        )
    return None


def owner_approval(
    reviews: list[dict[str, Any]], config: dict[str, Any], env: Mapping[str, str], repo: str
) -> dict[str, Any] | None:
    """The owner's latest review that approves, requests changes or was dismissed, when it
    approves: the review dict; else None. A comment-only review neither gives nor takes an
    approval (GitHub's own reading)."""
    latest = None
    for review in reviews:
        if str(review.get("state") or "").upper() not in DECISIVE:
            continue
        if not is_owner_actor(review.get("author"), config, env, repo):
            continue
        latest = review
    if latest is None or str(latest.get("state")).upper() != "APPROVED":
        return None
    return latest


# --- doorbell ---------------------------------------------------------------------------------
def doorbell(
    root: Path, repo: str, env: Mapping[str, str], github: Any = None, send: Any = None
) -> int:
    github = github if github is not None else _github()
    if send is None:
        from ci import run_phase  # noqa: PLC0415

        send = run_phase.dispatch
    try:
        payload = read_payload(env)
        if env.get("GITHUB_EVENT_NAME") != "pull_request_review":
            _say("doorbell", f"skipped: the event is {env.get('GITHUB_EVENT_NAME')}", env)
            return EXIT_OK
        review = _dict(payload.get("review"))
        if str(review.get("state") or "").lower() != "approved":
            _say("doorbell", "skipped: the review does not approve", env)
            return EXIT_OK
        config = _config(root)
        login = str(_dict(review.get("user")).get("login") or "")
        if not is_owner_actor(login, config, env, repo):
            _say(
                "doorbell", "skipped: the approval is not the owner's account's (decision 34)", env
            )
            return EXIT_OK
        pull = _dict(payload.get("pull_request"))
        head = _dict(pull.get("head"))
        change_id = build_change_id(head.get("ref"))
        if change_id is None:
            _say("doorbell", "skipped: not a build PR (its head is not sdlc/<id>/build)", env)
            return EXIT_OK
        head_repo = str(_dict(head.get("repo")).get("full_name") or "")
        if head_repo.lower() != repo.lower():
            _say("doorbell", f"skipped: the head is in {head_repo or 'an unknown repository'}", env)
            return EXIT_OK
        number = pull.get("number")
        if not isinstance(number, int) or isinstance(number, bool):
            raise StepError("the payload names no pull request number")
        ref = str(
            env.get("DEFAULT_BRANCH") or _dict(payload.get("repository")).get("default_branch")
        )
        if not ref or ref == "None":
            raise StepError(f"no default branch to dispatch {MERGE_WORKFLOW} on")
        sent = send(repo, MERGE_WORKFLOW, ref, change_id, head.get("ref"), {"pr": str(number)})
        if not sent.get("ok"):
            why = sent.get("reason") or sent.get("status") or "failed"
            raise StepError(f"{MERGE_WORKFLOW} could not be dispatched: {why}")
    except StepError as exc:
        _say("doorbell", f"failed: {exc}", env, stream=sys.stderr)
        return EXIT_FAILED
    _say("doorbell", f"dispatched {MERGE_WORKFLOW} for #{number} ({change_id})", env)
    return EXIT_OK


# --- not-build --------------------------------------------------------------------------------
def not_build(root: Path, repo: str, env: Mapping[str, str], github: Any = None) -> int:
    github = github if github is not None else _github()
    try:
        payload = read_payload(env)
        pull = _dict(payload.get("pull_request"))
        head = _dict(pull.get("head"))
        if build_change_id(head.get("ref")) is not None:
            _say("not-build", "skipped: a build PR; the deploy run posts its sdlc/review", env)
            return EXIT_OK
        head_repo = str(_dict(head.get("repo")).get("full_name") or "")
        if head_repo.lower() != repo.lower():
            # a fork's run holds a read-only token: the owner merges it through the bypass
            _say(
                "not-build", f"skipped: the head is in {head_repo or 'an unknown repository'}", env
            )
            return EXIT_OK
        sha = str(head.get("sha") or "")
        if not sha:
            raise StepError("the payload names no head commit")
        posted = github.post_not_build_check(repo, sha, cwd=root)
        if not posted.get("ok"):
            raise StepError(f"sdlc/review could not be posted: {posted.get('reason')}")
    except StepError as exc:
        _say("not-build", f"failed: {exc}", env, stream=sys.stderr)
        return EXIT_FAILED
    _say("not-build", f"posted sdlc/review ({github.NOT_BUILD_TITLE}) on {sha[:10]}", env)
    return EXIT_OK


# --- merge ------------------------------------------------------------------------------------
def _text_at(github: Any, repo: str, path: str, ref: str) -> str | None:
    got = github.file_at(repo, path, ref)
    if got.get("missing"):
        return None
    if not got.get("ok"):
        raise StepError(f"{path} at {ref[:10]} could not be read: {got.get('reason')}")
    return str(got.get("text"))


APPROVAL_PREDATES_GATE_E = "the owner's approval predates gate (deploy): approve again on the head"


def gate_e_paths(evidence: str) -> tuple[str, str]:
    """``evidence/gate-deploy.json``, then the ``evidence/gate-e.json`` an older plugin wrote
    (R45): a reader at a commit takes the first that is there."""
    return tuple(
        f"{evidence}/{art.GATE_RESULT.format(phase=p)}"
        for p in (c.DEPLOY, c.PHASE_LETTERS[c.DEPLOY])
    )


def _first_text_at(
    github: Any, repo: str, paths: str | tuple[str, ...] | list[str], ref: str
) -> tuple[str, str | None]:
    """``(path, text)`` of the first of ``paths`` present at ``ref``, or the first path and
    None when none is. ``StepError`` on a read error."""
    candidates = [paths] if isinstance(paths, str) else list(paths)
    for path in candidates:
        text = _text_at(github, repo, path, ref)
        if text is not None:
            return path, text
    return candidates[0], None


def gate_e_waits_at(
    github: Any, repo: str, gate_path: str | tuple[str, ...] | list[str], ref: str
) -> bool:
    """True when ``gate_path`` (the change's ``evidence/gate-deploy.json``; candidates from
    ``gate_e_paths`` are read in order) at ``ref`` reads ``result: wait``: gate (deploy) had
    run and offered the PR to the owner there (choice 250; an earlier deploy record that
    escalated or parked is no offer). ``StepError`` on a read error."""
    _path, text = _first_text_at(github, repo, gate_path, ref)
    try:
        record = json.loads(text) if text is not None else None
    except ValueError:
        return False
    return isinstance(record, dict) and record.get("result") == "wait"


def judge(
    pr: dict[str, Any],
    repo: str,
    default_branch: str,
    config: dict[str, Any],
    env: Mapping[str, str],
    github: Any,
) -> dict[str, Any]:
    """Points 1 to 5: ``{"wait": reason}`` or ``{"head", "change_id", "approval",
    "tally"}``. ``StepError`` when the API cannot be read. Pure but for ``github``."""
    number = pr.get("number")
    if pr.get("state") != "open":
        return {"wait": f"#{number} is not open ({pr.get('state') or 'unknown'})"}
    if pr.get("draft"):
        return {"wait": f"#{number} is a draft: the deploy run marks it ready"}
    change_id = build_change_id(pr.get("head_ref"))
    if change_id is None:
        return {"wait": f"#{number} is not a build PR (head {pr.get('head_ref') or '?'})"}
    if str(pr.get("head_repo") or "").lower() != repo.lower():
        return {"wait": f"#{number} has its head outside {repo}"}
    if pr.get("base_ref") != default_branch:
        return {"wait": f"#{number} is not into {default_branch} (base {pr.get('base_ref')})"}
    labels = pr.get("labels") or []
    if c.NEEDS_HUMAN_LABEL in labels:
        return {"wait": f"#{number} is parked ({c.NEEDS_HUMAN_LABEL})"}
    if not E_READY_LABELS & set(labels):
        return {"wait": f"#{number} does not carry {E_READY}: gate (deploy) has not offered it"}
    head = str(pr.get("head_sha") or "")
    if not head:
        raise StepError(f"#{number} names no head commit")
    listed = github.dir_at(repo, c.CHANGES_DIR, head)
    if not listed.get("ok"):
        raise StepError(f"{c.CHANGES_DIR}/ at {head[:10]} could not be listed: {listed['reason']}")
    dirs = [n for n in listed.get("names") or [] if n.startswith(f"{change_id}-")]
    if len(dirs) != 1:
        return {"wait": f"{c.CHANGES_DIR}/ at {head[:10]} has {len(dirs)} folders for {change_id}"}
    rel = f"{c.CHANGES_DIR}/{dirs[0]}"
    status_text = _text_at(github, repo, f"{rel}/{status_mod.STATUS_FILE}", head)
    if status_text is None:
        return {"wait": f"{rel}/status.yaml is not at the head"}
    try:
        data = yamlish.loads(status_text)
        st = status_mod.Status.from_dict(data if isinstance(data, dict) else {})
    except (ValueError, TypeError) as exc:
        return {"wait": f"{rel}/status.yaml at the head cannot be read: {exc}"}
    if st.phase != c.DEPLOY or st.gate.phase != c.DEPLOY or st.gate.result != "passed":
        gate = f"{st.gate.phase or '-'}/{st.gate.result or '-'}"
        return {
            "wait": f"change {change_id} is at phase {st.phase}, gate {gate}: not deploy passed"
        }
    if st.parked_reason:
        return {"wait": f"change {change_id} is parked: {st.parked_reason}"}
    if st.build_pr is None or int(st.build_pr) != int(number):
        return {"wait": f"status.yaml names build PR #{st.build_pr}, not #{number}"}
    evidence = f"{rel}/{art.EVIDENCE_DIR}"
    gate_paths = gate_e_paths(evidence)
    gate_path, gate_text = _first_text_at(github, repo, gate_paths, head)
    try:
        gate_record = json.loads(gate_text) if gate_text is not None else None
    except ValueError:
        gate_record = None
    if not isinstance(gate_record, dict):
        return {"wait": "evidence/gate-deploy.json is missing or unreadable at the head"}
    if gate_record.get("result") != "wait":
        return {"wait": f"gate (deploy) recorded {gate_record.get('result')!r}, not 'wait'"}
    if gate_mod.deferred_commands(gate_record):
        return {
            "wait": "gate (deploy)'s commands check is still deferred to the runner (issue #91)"
        }
    findings_text = _text_at(github, repo, f"{evidence}/{art.REVIEW_FINDINGS}", head)
    try:
        findings = json.loads(findings_text) if findings_text is not None else None
    except ValueError:
        findings = None
    if not isinstance(findings, dict):
        return {"wait": "evidence/review-findings.json is missing or unreadable at the head"}
    try:
        findings = fmod.normalise(findings)
    except (TypeError, ValueError, AttributeError) as exc:
        return {"wait": f"evidence/review-findings.json cannot be read: {exc}"}
    tally = findings["tally"]
    if tally.get("important"):
        return {"wait": f"the review found {tally['important']} Important finding(s)"}
    reviewed = str(findings.get("head") or "")
    if not reviewed:
        return {"wait": "review-findings.json names no reviewed commit"}
    later = only_evidence_since(github, repo, reviewed, head, rel)
    if later:
        return {"wait": later}
    checks = github.check_runs_on(repo, head, fmod.CHECK_RUN_NAME)
    if not checks.get("ok"):
        raise StepError(f"the check runs on {head[:10]} could not be read: {checks['reason']}")
    runs = checks.get("runs") or []
    if not runs:
        return {"wait": f"no {fmod.CHECK_RUN_NAME} check on the head {head[:10]} yet"}
    if any(r.get("conclusion") != "success" for r in runs):
        return {"wait": f"{fmod.CHECK_RUN_NAME} is not green on the head {head[:10]}"}
    got = github.pr_reviews(repo, int(number))
    if not got.get("ok"):
        raise StepError(f"the reviews of #{number} could not be read: {got.get('reason')}")
    approval = owner_approval(got.get("reviews") or [], config, env, repo)
    if approval is None:
        return {"wait": f"#{number} has no approving review by the owner's account"}
    approved_on = str(approval.get("commit") or "")
    if not approved_on:
        return {"wait": "the owner's approval names no commit"}
    after = only_evidence_since(github, repo, approved_on, head, rel)
    if after:
        return {"wait": f"after the owner's approval: {after}"}
    if not gate_e_waits_at(github, repo, gate_paths, approved_on):
        # choice 250: an approval given before gate (deploy) offered the PR is no gate
        # (deploy); the owner's banner and the review findings come with it, so the owner
        # approves again
        return {"wait": APPROVAL_PREDATES_GATE_E}
    return {"head": head, "change_id": change_id, "approval": approval, "tally": tally}


def merge(root: Path, repo: str, number: int, env: Mapping[str, str], github: Any = None) -> int:
    github = github if github is not None else _github()
    try:
        config = _config(root)
        default_branch = str(env.get("DEFAULT_BRANCH") or "")
        if not default_branch:
            raise StepError("DEFAULT_BRANCH is not set")
        pr = github.pr_by_number(repo, number)
        if not pr.get("ok"):
            raise StepError(f"#{number} could not be read: {pr.get('reason')}")
        found = judge(pr, repo, default_branch, config, env, github)
        if "wait" in found:
            _say("merge", f"wait: {found['wait']}", env)
            return EXIT_OK
        approval, tally = found["approval"], found["tally"]
        _say(
            "merge",
            f"approval: {approval.get('author')} approved #{number} at {approval.get('at')} "
            f"on {str(approval.get('commit'))[:10]} (gate (deploy), decision 36)",
            env,
        )
        tok = str(env.get(MERGE_TOKEN_ENV) or "").strip()
        if not tok:
            raise StepError(f"{MERGE_TOKEN_ENV} is empty: the merge App's token was not minted")
        done = github.merge_pr(repo, number, found["head"], tok)
        if not done.get("ok"):
            why = done.get("reason") or "refused"
            raise StepError(
                f"the merge of #{number} was refused (HTTP {done.get('status')}): {why}"
            )
    except StepError as exc:
        _say("merge", f"failed: {exc}", env, stream=sys.stderr)
        return EXIT_FAILED
    _say(
        "merge",
        f"merged #{number} ({found['change_id']}) at {found['head'][:10]} as "
        f"{str(done.get('sha'))[:10]} through the merge App; findings: "
        f"{tally.get('important', 0)} Important, {tally.get('nit', 0)} nits",
        env,
    )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sdlc-merge-step", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("doorbell", "not-build", "merge"):
        s = sub.add_parser(name)
        s.add_argument("--root", default=".", help="the default branch's checkout")
        s.add_argument("--repo", required=True, help="owner/name")
        if name == "merge":
            s.add_argument("--pr", required=True, type=int)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root, env = Path(args.root).resolve(), dict(os.environ)
    if args.cmd == "doorbell":
        return doorbell(root, args.repo, env)
    if args.cmd == "not-build":
        return not_build(root, args.repo, env)
    return merge(root, args.repo, args.pr, env)


if __name__ == "__main__":
    sys.exit(main())
