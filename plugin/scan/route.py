"""Routing the weekly security review's findings (build guide step 38; decisions 16, 18, 21,
25; article p.46-48).

The routing rule: every Important finding, bounded or wide, enters the framework as an
**incident intent change** (``entry_route: incident``, gate (f) = the owner's triage): no
route skips gates (a) and (b). The article's two routes (p.47 step 5 "a bounded finding" into
the PR review gate, step 6 "anything wider than one patch ... write it up as intent.md")
differ in the intent, not in the gates:

- **bounded** (one file, one patch): ``change_type: fix``; the Proposed outcome is the patch,
  stored beside the intent as ``evidence/suggested-patch.diff`` for the build run to apply;
- **wide**: ``change_type: feature``; the intent describes the class and its open questions.

At most ``max_findings`` intents per run (the rest stay in the run's JSON and return next
week). A dismissed finding (``changes/.dismissed.json``, kind ``scan``, no expiry) never
returns; a finding already filed as an open change is not filed twice. The vulnerability-class
eval of p.48 step 7 is ``/sdlc-deploy`` step 0b, as for every incident change.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from detect import dismissals  # noqa: E402
from review import findings as findings_mod  # noqa: E402

from gate import artifacts as art  # noqa: E402
from scan import prompt as prompt_mod  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops  # noqa: E402
from state import status as status_mod  # noqa: E402

STATE_CLI = PLUGIN_DIR / "state" / "cli.py"
PR_CLI = PLUGIN_DIR / "pr" / "cli.py"
GATE_CLI = PLUGIN_DIR / "gate" / "cli.py"
SCHEMA_VERSION = 1
KIND = "scan"
FINDING_FILE = "scan-finding.json"
PATCH_FILE = "suggested-patch.diff"
PROPOSAL_FILE = "proposal.json"
DEFAULT_CLASS = "unclassified"
TITLE_SUMMARY_CHARS = 60
AUTHOR = "security review (phase f)"
PROPOSAL = {
    "schema_version": 1,
    "tier": 3,
    "route": "pull_request",
    "args": {},
    "rationale": "the weekly security review; the intent PR is the route",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- the findings file ------------------------------------------------------------------------
def _patch_of(finding: dict[str, Any]) -> str | None:
    """The finding's patch when it reads as a unified diff, else None."""
    patch = finding.get("patch")
    if not isinstance(patch, str) or not patch.strip():
        return None
    text = patch.replace("\r\n", "\n")
    if "@@" not in text or "+++ " not in text or "--- " not in text:
        return None
    return text if text.endswith("\n") else text + "\n"


def load_findings(path: Path, head: str | None) -> tuple[dict[str, Any] | None, list[str]]:
    """The review's findings file, validated (``review.findings.validate``) and normalised,
    with the scan's extra keys: ``bounded`` (bool, default False), ``class`` (str, default
    ``unclassified``) and ``patch`` (kept only when it is a unified diff of at most
    ``MAX_PATCH_LINES`` lines; a longer one is not "one patch", so the finding is routed as
    wide). Every finding gets its ``signature``. (None, problems) when the file cannot be
    used."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return None, [f"no findings file at {path.as_posix()}: the review did not write it"]
    except ValueError as exc:
        return None, [f"the findings file is not JSON: {exc}"]
    problems = findings_mod.validate(raw, head)
    if problems:
        return None, problems
    for i, finding in enumerate(raw["findings"]):
        if str(finding.get("pass", "")).strip().lower() != "security":
            problems.append(f"findings[{i}].pass must be 'security' in a scan")
        bounded = finding.get("bounded", False)
        if not isinstance(bounded, bool):
            problems.append(f"findings[{i}].bounded must be true or false")
        klass = finding.get("class", DEFAULT_CLASS)
        if klass is not None and not isinstance(klass, str):
            problems.append(f"findings[{i}].class must be a string")
    if problems:
        return None, problems
    data = findings_mod.normalise(raw)
    for finding in data["findings"]:
        finding["bounded"] = bool(finding.get("bounded", False))
        finding["class"] = " ".join(str(finding.get("class") or "").split()) or DEFAULT_CLASS
        patch = _patch_of(finding)
        if patch is not None and len(patch.splitlines()) > prompt_mod.MAX_PATCH_LINES:
            finding["patch_dropped"] = (
                f"patch of {len(patch.splitlines())} lines is over {prompt_mod.MAX_PATCH_LINES}"
            )
            finding["bounded"] = False
            patch = None
        if patch is None:
            finding.pop("patch", None)
        else:
            finding["patch"] = patch
        finding["signature"] = findings_mod.signature(finding)
    return data, []


# --- selection ----------------------------------------------------------------------------------
def _is_important(finding: dict[str, Any]) -> bool:
    return str(finding.get("severity", "")).strip().lower() == "important"


def select(
    findings: list[dict[str, Any]],
    dismissed_record: dict[str, Any],
    max_findings: int,
    *,
    already_filed: dict[str, str] | None = None,
    today: date | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(to file, skipped). Important findings only, not dismissed (``dismissals.lookup``), not
    already filed as an open change, ranked bounded first and then in file order (file,
    line), capped at ``max_findings``. Every finding left out is in ``skipped`` with its
    ``skip_reason`` (``nit``, ``dismissed``, ``already filed as change <id>``, ``over the
    cap``)."""
    filed = already_filed or {}
    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for finding in findings:
        sig = finding.get("signature") or findings_mod.signature(finding)
        item = {**finding, "signature": sig}
        if not _is_important(item):
            skipped.append({**item, "skip_reason": "nit"})
            continue
        entry = dismissals.lookup(dismissed_record, sig, today)
        if entry is not None:
            skipped.append(
                {**item, "skip_reason": "dismissed", "dismissal": entry.get("reason", "")}
            )
            continue
        if sig in filed:
            skipped.append({**item, "skip_reason": f"already filed as change {filed[sig]}"})
            continue
        candidates.append(item)
    candidates.sort(
        key=lambda f: (
            0 if f.get("bounded") else 1,
            findings_mod.normalise_file(f.get("file", "")),
            f.get("line") if isinstance(f.get("line"), int) else 0,
            str(f.get("summary", "")),
        )
    )
    cap = max(int(max_findings), 0)
    for item in candidates[cap:]:
        skipped.append({**item, "skip_reason": "over the cap: returns next week"})
    return candidates[:cap], skipped


# --- the intent ---------------------------------------------------------------------------------
def title_for(finding: dict[str, Any]) -> str:
    # cut at a word boundary: the live run of 2026-09-25 titled an intent "... in git (pre"
    short = c.truncate_words(finding.get("summary", ""), TITLE_SUMMARY_CHARS).rstrip(" .,;:")
    return f"security: {finding.get('class') or DEFAULT_CLASS}: {short}"


def _where(finding: dict[str, Any]) -> str:
    file = findings_mod.strip_dot_slash(str(finding.get("file", "")).replace("\\", "/"))
    line = finding.get("line")
    return f"{file}:{line}" if isinstance(line, int) and line > 0 else file


def _link(finding: dict[str, Any], head: str, repo: str | None) -> str | None:
    if not repo or not head:
        return None
    file = findings_mod.strip_dot_slash(str(finding.get("file", "")).replace("\\", "/"))
    line = finding.get("line")
    anchor = f"#L{line}" if isinstance(line, int) and line > 0 else ""
    return f"https://github.com/{repo}/blob/{head}/{file}{anchor}"


def intent_text(finding: dict[str, Any], change_id: str, head: str, repo: str | None) -> str:
    """intent.md in the ``intent-template`` skill's shape: the header line, the five sections
    and ``## Evidence`` (an incident). A bounded finding's Proposed outcome is its patch; a
    wide finding's is the outcome for its class, with the class's open questions."""
    klass = finding.get("class") or DEFAULT_CLASS
    summary = " ".join(str(finding.get("summary", "")).split())
    where = _where(finding)
    sig = finding.get("signature") or findings_mod.signature(finding)
    rule = " ".join(str(finding.get("rule") or "").split())
    bounded = bool(finding.get("bounded"))
    patch = finding.get("patch") if bounded else None
    link = _link(finding, head, repo)
    short_head = head[:12] if head else "unknown"
    lines = [
        f"# Intent: {title_for(finding)}",
        f"Author: {AUTHOR}. Status: proposed. Change id: {change_id}. "
        f"Entry route: incident scan:{sig}.",
        "",
        art.INTENT_SECTIONS[0],  # Problem
        f"The weekly security review of the codebase at commit `{short_head}` found an "
        f"Important {klass} finding in `{where}`: {summary}",
        "",
        "Until it is fixed the weakness stays in the code the project ships. The review is "
        "read-only; nothing has been changed.",
        "",
        art.INTENT_SECTIONS[1],  # Proposed outcome
    ]
    if bounded and patch:
        lines += [
            f"The finding is bounded (one file, one patch): `{where}` no longer has the "
            f"{klass} weakness, proven by a new test that reproduces it before the fix and "
            "passes after it. The review suggests this patch, stored as "
            f"`evidence/{PATCH_FILE}` for the build run to apply and check:",
            "",
            "```diff",
            patch.rstrip("\n"),
            "```",
        ]
    elif bounded:
        lines.append(
            f"The finding is bounded (one file, one patch): `{where}` no longer has the "
            f"{klass} weakness, proven by a new test that reproduces it before the fix and "
            "passes after it. The review gave no patch; the design pass writes it."
        )
    else:
        lines.append(
            f"No instance of this {klass} weakness remains in the codebase: the case at "
            f"`{where}` and every other place with the same pattern are fixed, each proven by "
            "a test, and an eval case for the class keeps it from returning (article p.48 "
            "step 7)."
        )
    lines += [
        "",
        art.INTENT_SECTIONS[2],  # Affected users and systems
        f"- `{findings_mod.strip_dot_slash(str(finding.get('file', '')))}` and whatever "
        "calls it" + ("" if bounded else "; the design pass finds the other places"),
        f"- Users of {repo}" if repo else "- The project's users",
        "",
        art.INTENT_SECTIONS[3],  # Constraints
        "- The security-baseline skill applies to the fix; no new dependency without a Risks "
        "line in plan.md.",
        "- A test that reproduces the vulnerability is written first; no pre-existing test is "
        "edited to make the fix pass.",
        "- Never quote a credential in the change, its tests or its evidence.",
        "",
        art.INTENT_SECTIONS[4],  # Open questions
    ]
    if bounded:
        lines.append("none")
    else:
        lines += [
            f"- Where else does the {klass} pattern occur, and does one fix cover every place?",
            "- Is a shared guard (a helper, a middleware, a schema) better than local fixes?",
            "- Which eval case captures the class so it does not return?",
        ]
    lines += [
        "",
        art.INTENT_EVIDENCE_SECTION,
        f"- Where: `{where}`" + (f" ({link})" if link else ""),
        f"- Class: {klass}; severity: Important; bounded: {'yes' if bounded else 'no'}",
        f"- Commit reviewed: `{head}`",
        f'- The review\'s words: "{summary}"' + (f" (rule: {rule})" if rule else ""),
        f"- Finding signature: `{sig}` (`evidence/{FINDING_FILE}`); closing this pull request "
        "with a comment dismisses it, and it does not return (article p.47 step 4).",
    ]
    if finding.get("patch_dropped"):
        lines.append(f"- The review's patch was not kept: {finding['patch_dropped']}.")
    return "\n".join(lines) + "\n"


def finding_record(finding: dict[str, Any], head: str, at: str | None = None) -> dict[str, Any]:
    """``evidence/scan-finding.json``: what ``detect/cli.py dismiss`` and gate (f) read."""
    line = finding.get("line")
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "signature": finding.get("signature") or findings_mod.signature(finding),
        "summary": " ".join(str(finding.get("summary", "")).split()),
        "file": findings_mod.strip_dot_slash(str(finding.get("file", "")).replace("\\", "/")),
        "line": line if isinstance(line, int) and not isinstance(line, bool) else 0,
        "class": finding.get("class") or DEFAULT_CLASS,
        "bounded": bool(finding.get("bounded")),
        "head": head,
        "severity": str(finding.get("severity", "")).strip().lower(),
        "at": at or _now(),
    }


# --- what is already filed ----------------------------------------------------------------------
def _show(root: Path, ref: str, path: str) -> str | None:
    try:
        return gitops.run(root, "show", f"{ref}:{path}")
    except (gitops.GitError, FileNotFoundError):
        return None


def _status_from(text: str | None) -> status_mod.Status | None:
    if not text:
        return None
    try:
        return status_mod.Status.from_dict(status_mod.yamlish.loads(text))
    except Exception:  # noqa: BLE001 - an unreadable status never hides a finding
        return None


def _signature_in(text: str | None) -> str | None:
    try:
        data = json.loads(text or "")
    except ValueError:
        return None
    sig = data.get("signature") if isinstance(data, dict) else None
    return sig if isinstance(sig, str) and sig else None


def _in_flight(st: status_mod.Status | None) -> bool:
    return st is not None and not st.abandoned and st.phase != "e"


def filed_signatures(root: Path) -> dict[str, str]:
    """signature -> change id of every scan change still in flight: in the checkout (the
    default branch, once its intent merged) or on a remote ``sdlc/<id>/a`` branch, not
    abandoned and not shipped. A finding the owner has not triaged yet is not filed twice."""
    root = Path(root)
    found: dict[str, str] = {}
    for change_dir in c.list_change_dirs(root):
        sig = _signature_in(art.read_text(change_dir / art.EVIDENCE_DIR / FINDING_FILE))
        if not sig:
            continue
        try:
            st = status_mod.read_status(change_dir)
        except Exception:  # noqa: BLE001
            st = None
        if _in_flight(st):
            found.setdefault(sig, change_dir.name[:4])
    if not gitops.is_repo(root):
        return found
    try:
        refs = gitops.run(
            root, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/sdlc/"
        ).split()
    except (gitops.GitError, FileNotFoundError):
        return found
    for ref in refs:
        parsed = c.parse_branch(ref.removeprefix("origin/"))
        if not parsed or parsed[1] != "a":
            continue
        change_id = parsed[0]
        listing = _show(root, ref, c.CHANGES_DIR) or ""
        names = [
            n.rstrip("/") for n in listing.split() if n.startswith(change_id + "-")
        ]  # `git show <tree>` lists a directory with a trailing "/"
        if not names:
            continue
        rel = f"{c.CHANGES_DIR}/{names[0]}"
        sig = _signature_in(_show(root, ref, f"{rel}/{art.EVIDENCE_DIR}/{FINDING_FILE}"))
        if not sig or sig in found:
            continue
        if not _in_flight(_status_from(_show(root, ref, f"{rel}/{status_mod.STATUS_FILE}"))):
            continue
        found[sig] = change_id
    return found


# --- filing ---------------------------------------------------------------------------------------
def _cli(script: Path, argv: list[str], root: Path) -> tuple[dict[str, Any] | None, int, str]:
    """Run one plugin CLI as a subprocess; (its JSON or None, exit code, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(script), *argv],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    data = None
    try:
        data = json.loads(proc.stdout) if proc.stdout.strip() else None
    except ValueError:
        data = None
    return data, proc.returncode, proc.stderr.strip()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def _default_branch(root: Path) -> str:
    """``gitops.default_branch`` (``SDLC_DEFAULT_BRANCH`` first: the scan workflow sets it
    from ``github.event.repository.default_branch``), "main" outside a git checkout."""
    try:
        return gitops.default_branch(root)
    except (gitops.GitError, FileNotFoundError):
        return "main"


def _local_ids(root: Path) -> list[str]:
    """Change ids of local ``sdlc/<id>/*`` branches (an unpushed filing of this run)."""
    try:
        out = gitops.run(root, "for-each-ref", "--format=%(refname:short)", "refs/heads/sdlc/")
    except (gitops.GitError, FileNotFoundError):
        return []
    ids = []
    for ref in out.split():
        parsed = c.parse_branch(ref)
        if parsed:
            ids.append(parsed[0])
    return ids


def _next_id(root: Path, allocated: list[str]) -> str:
    seen = [*allocated, *_local_ids(root)]
    if gitops.has_remote(root):
        seen += gitops.remote_change_ids(root)
    return c.next_change_id(root, seen)


def _original_ref(root: Path) -> str | None:
    if not gitops.is_repo(root):
        return None
    try:
        branch = gitops.current_branch(root)
        return gitops.run(root, "rev-parse", "HEAD").strip() if branch == "HEAD" else branch
    except gitops.GitError:
        return None


def _restore(root: Path, ref: str | None) -> None:
    if not ref:
        return
    try:
        gitops.run(root, "checkout", "-q", ref)
    except gitops.GitError:
        pass


def file_one(
    root: Path,
    finding: dict[str, Any],
    *,
    change_id: str,
    head: str,
    repo: str | None,
    push: bool,
) -> dict[str, Any]:
    """Allocate one incident change for the finding, write its intent and evidence, commit
    them on ``sdlc/<id>/a`` from the default branch and open the intent PR."""
    sig = finding["signature"]
    bounded = bool(finding.get("bounded"))
    change_type = "fix" if bounded else "feature"
    data, code, err = _cli(
        STATE_CLI,
        ["new-change", "--root", str(root), "--title", title_for(finding), "--route", "incident",
         "--type", change_type, "--id", change_id],
        root,
    )  # fmt: skip
    if code != 0 or not data:
        return {"signature": sig, "error": f"new-change failed: {err or code}"}
    change_id = data["id"]
    change_dir = root / data["dir"]
    (change_dir / "intent.md").write_text(
        intent_text(finding, change_id, head, repo), encoding="utf-8", newline="\n"
    )
    evidence = change_dir / art.EVIDENCE_DIR
    _write_json(evidence / FINDING_FILE, finding_record(finding, head))
    patch = finding.get("patch") if bounded else None
    if patch:
        (evidence / PATCH_FILE).parent.mkdir(parents=True, exist_ok=True)
        (evidence / PATCH_FILE).write_text(patch, encoding="utf-8", newline="\n")
    _write_json(evidence / PROPOSAL_FILE, dict(PROPOSAL))
    default = _default_branch(root)
    start = f"origin/{default}" if gitops.has_remote(root) else default
    argv = ["commit-phase", "--root", str(root), "--id", change_id, "--phase", "f",
            "--message", f"maintain({change_id}): security review finding {sig}",
            "--start-point", start]  # fmt: skip
    if push:
        argv.append("--push")
    committed, code, err = _cli(STATE_CLI, argv, root)
    if code != 0:
        return {
            "signature": sig,
            "change_id": change_id,
            "error": f"commit-phase failed: {err or code}",
        }
    # gate (f) on the filed change (no diagnosis run: the review already wrote the intent
    # and the proposal), so the intent PR carries the gate's label (sdlc:f-ready, or
    # sdlc:needs-human with the reason) beside `incident`; the evidence rides in its own
    # commit, as every phase does (OPERATING_MODEL section 4.1)
    _cli(GATE_CLI, ["start-run", "--root", str(root), "--id", change_id, "--phase", "f"], root)
    gate, _code, _err = _cli(
        GATE_CLI, ["check", "--root", str(root), "--id", change_id, "--phase", "f"], root
    )
    evidence_argv = ["commit-phase", "--root", str(root), "--id", change_id, "--phase", "f",
                     "--message", f"maintain({change_id}): gate (f) evidence"]  # fmt: skip
    if push:
        evidence_argv.append("--push")
    _cli(STATE_CLI, evidence_argv, root)
    upsert, code, err = _cli(
        PR_CLI, ["upsert", "--root", str(root), "--id", change_id, "--phase", "f"], root
    )
    out: dict[str, Any] = {
        "signature": sig,
        "change_id": change_id,
        "dir": data["dir"],
        "type": change_type,
        "branch": (committed or {}).get("branch"),
        "commit": (committed or {}).get("commit"),
        "pushed": bool((committed or {}).get("pushed")),
        "gate": (gate or {}).get("result"),
        "label": (upsert or {}).get("label"),
        "pr": (upsert or {}).get("url"),
        "pr_route": (upsert or {}).get("route"),
    }
    if code != 0 or upsert is None:
        out["error"] = f"pr upsert failed: {err or code}"
    return out


def file_findings(
    root: Path,
    findings: list[dict[str, Any]],
    *,
    head: str,
    repo: str | None,
    push: bool,
    dry_run: bool,
) -> list[dict[str, Any]]:
    """File each finding as an incident intent change (``file_one``); one dict per finding:
    ``{signature, change_id, dir, pr, commit, pushed, ...}`` or ``{signature, error}``. The
    checkout is back on the branch it started on afterwards, whatever happened."""
    root = Path(root)
    results: list[dict[str, Any]] = []
    if dry_run:
        for finding in findings:
            results.append(
                {
                    "signature": finding["signature"],
                    "dry_run": True,
                    "title": title_for(finding),
                    "type": "fix" if finding.get("bounded") else "feature",
                }
            )
        return results
    original = _original_ref(root)
    allocated: list[str] = []
    try:
        for finding in findings:
            try:
                change_id = _next_id(root, allocated)
                allocated.append(change_id)
                results.append(
                    file_one(root, finding, change_id=change_id, head=head, repo=repo, push=push)
                )
            except (gitops.GitError, OSError, ValueError, KeyError) as exc:
                results.append({"signature": finding.get("signature"), "error": str(exc)})
            finally:
                _restore(root, original)
    finally:
        _restore(root, original)
    return results
