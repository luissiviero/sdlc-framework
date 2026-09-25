"""Layer-1 tests for plugin/detect/cli.py: the deterministic half of phase (f) (build guide
steps 37 and 39; decisions 14, 15, 25, 26; article p.42-45).

Every test runs against a copy of the fixture project initialised with ``/sdlc-init``
(``bands.yaml`` and ``sdlc.yaml`` from the template), committed on ``main`` and pushed to a
bare ``origin``, so ``commit-phase --start-point origin/main --push`` works for real. Nothing
leaves the machine: ``detect.source.fetch`` returns synthetic daily observations, the
``pr.github`` functions the CLI calls are fakes that record their calls, and
``detect.runbooks.run`` is replaced where a runbook would act."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from detect import bands as bands_mod
from detect import cli as detect_cli
from detect import dismissals, finding, runbooks, source

from state import gitops
from state import status as status_mod

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
DETECT_CLI = ROOT / "plugin" / "detect" / "cli.py"
METRIC = "ci_test_failure_rate"  # the template's metric (decision 15)
FAILED_URL = "https://github.com/o/r/actions/runs/42"
REPO = "o/r"
ROLLBACK_ENTRY = (
    "  runbooks:\n"
    "    - name: rollback-deploy\n"
    '      command: "python scripts/rollback.py"\n'
    "      authorization: go\n"
)
# cli.open_incidents builds the change folder path from `git show <ref>:changes`, whose
# listing names a directory with a trailing "/" ("0001-slug/"): the detection record is then
# looked up at "changes/0001-slug//evidence/detection.json", which git refuses, so no filed
# incident is ever found and a second breach of the same metric files a second change.
OPEN_INCIDENTS_BUG = (
    "cli.open_incidents keeps the trailing '/' of the `git show <ref>:changes` listing, so "
    "the detection record path has '//' and is never read: open incidents are never found"
)


# --- helpers ----------------------------------------------------------------------------------
def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


def bare(root: Path) -> Path:
    return root.parent / "origin.git"


def remote_has(root: Path, branch: str) -> bool:
    return bool(git(bare(root), "branch", "--list", branch).strip())


def project(tmp_path: Path) -> Path:
    """The fixture initialised (standard profile) and committed on main, pushed to a bare
    origin whose HEAD is main."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    proc = subprocess.run(
        [sys.executable, str(INIT), "--root", str(root), "--profile", "standard"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "sdlc-init (as if the 0000 PR merged)")
    origin = bare(root)
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(root, "remote", "add", "origin", str(origin))
    git(root, "push", "-q", "-u", "origin", "main")
    git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return root


def observations(values: list[float], failed_last: str | None = None) -> list[dict[str, Any]]:
    """One observation per day of September 2026, in order."""
    assert len(values) <= 30
    out = []
    for i, value in enumerate(values, 1):
        failed = int(round(value * 5))
        urls = [failed_last] if failed_last and i == len(values) else []
        out.append(
            {
                "at": f"2026-09-{i:02d}",
                "value": value,
                "meta": {"runs": 5, "failed": failed, "failed_run_urls": urls},
            }
        )
    return out


def series(n_days: int, spike: bool = False) -> list[dict[str, Any]]:
    """``n_days`` flat days (value 0.0), the last one a spike (1.0, one failed run) when
    asked. The baseline is the window minus the last 8 points and needs 8: n >= 16."""
    values = [0.0] * n_days
    if spike:
        values[-1] = 1.0
    return observations(values, FAILED_URL if spike else None)


def tier1_series() -> list[dict[str, Any]]:
    """A baseline alternating 0.0/0.2 (mean 0.1, sample sigma ~0.103) and a tail whose last
    five points sit between 1 and 2 sigma above it: rule we3 alone, tier 1."""
    return observations([0.0, 0.2] * 5 + [0.0, 0.0, 0.0] + [0.25] * 5)


def change_dirs(root: Path) -> list[Path]:
    return sorted(p for p in (root / "changes").iterdir() if p.is_dir())


def incident_dir(root: Path, change_id: str = "0001") -> Path:
    [found] = [p for p in change_dirs(root) if p.name.startswith(change_id + "-")]
    return found


def cli(capsys, *argv: str) -> tuple[int, dict[str, Any] | None]:
    code = detect_cli.main(list(argv))
    out = capsys.readouterr().out
    return code, (json.loads(out) if out.strip() else None)


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def write_proposal(change_dir: Path, route: str, tier: int = 3, args=None) -> None:
    path = change_dir / "evidence" / finding.PROPOSAL_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "tier": tier,
        "route": route,
        "args": dict(args or {}),
        "rationale": "the failures began with one commit; reverting it is the smallest move",
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def add_rollback_runbook(root: Path) -> None:
    """Give the template's rollback-deploy route a command (sdlc.yaml: maintain.runbooks):
    without one the route is unsupported and never taken."""
    path = root / "sdlc.yaml"
    text = path.read_text(encoding="utf-8")
    assert "  runbooks: []\n" in text
    path.write_text(text.replace("  runbooks: []\n", ROLLBACK_ENTRY), encoding="utf-8")
    git(root, "add", "sdlc.yaml")
    git(root, "commit", "-q", "-m", "a rollback runbook")
    git(root, "push", "-q", "origin", "main")


def runbook_records(change_dir: Path) -> list[str]:
    return sorted(p.name for p in (change_dir / "evidence").glob("runbook-*.json"))


class FakeGitHub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.actor: dict[str, Any] = {"ok": True, "actor": None, "reason": ""}
        self.comments: dict[str, Any] = {"ok": True, "comments": [], "reason": ""}

    def find_open_pr(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("find_open_pr", args, kwargs))
        return {"ok": True, "route": "fake", "number": 12, "url": "https://x/pr/12"}

    def label_actor(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("label_actor", args, kwargs))
        return dict(self.actor)

    def issue_comments(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("issue_comments", args, kwargs))
        return dict(self.comments)

    def set_labels(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("set_labels", args, kwargs))
        return {"ok": True, "route": "fake", "added": list(args[2]), "removed": list(args[3])}

    def create_pr(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("create_pr", args, kwargs))
        return {"ok": True, "route": "fake", "url": "https://x/pr/13", "number": 13}

    def ensure_label(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("ensure_label", args, kwargs))
        return {"ok": True, "route": "fake", "label": args[1], "created": False}

    def named(self, name: str) -> list[tuple[tuple[Any, ...], dict[str, Any]]]:
        return [(a, k) for n, a, k in self.calls if n == name]


class FakeSource:
    def __init__(self) -> None:
        self.observations: list[dict[str, Any]] = series(16)
        self.error: str | None = None
        self.calls: list[dict[str, Any]] = []

    def fetch(self, repo, *, since, cache=None, workflow=None, **_kw) -> source.FetchResult:
        self.calls.append({"repo": repo, "since": since, "cache": cache, "workflow": workflow})
        if self.error:
            raise source.SourceError(self.error)
        return source.FetchResult(
            observations=list(self.observations),
            runs_total=sum(o["meta"]["runs"] for o in self.observations),
            fetched=len(self.observations),
            since=since,
        )


class RunbookSpy:
    def __init__(self, status: str = "ran") -> None:
        self.status = status
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def __call__(self, name, *args: Any, **kwargs: Any) -> runbooks.Outcome:
        self.calls.append(((name, *args), kwargs))
        return runbooks.Outcome(
            runbook=name, status=self.status, pr_url="https://x/pr/9", args=dict(args[2])
        )


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """No token reaches a subprocess (the gate and PR CLIs report ``route: none``), and no
    ``$GITHUB_OUTPUT`` or ``$SDLC_DEFAULT_BRANCH`` leaks in from the runner."""
    for name in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_OUTPUT", "SDLC_DEFAULT_BRANCH"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def gh(monkeypatch) -> FakeGitHub:
    fake = FakeGitHub()
    module = detect_cli._github()
    for name in (
        "find_open_pr",
        "label_actor",
        "issue_comments",
        "set_labels",
        "create_pr",
        "ensure_label",
    ):
        monkeypatch.setattr(module, name, getattr(fake, name))
    return fake


@pytest.fixture
def src(monkeypatch) -> FakeSource:
    fake = FakeSource()
    monkeypatch.setattr(detect_cli.source, "fetch", fake.fetch)
    return fake


@pytest.fixture
def spy(monkeypatch) -> RunbookSpy:
    fake = RunbookSpy()
    monkeypatch.setattr(runbooks, "run", fake)
    return fake


def file_incident(root: Path, src: FakeSource, capsys, *extra: str, force: str | None = None):
    """Run the detection with --file (a spike, or a flat series forced to a tier)."""
    src.observations = series(16) if force else series(16, spike=True)
    argv = ["run", "--root", str(root), "--repo", REPO, "--file", *extra]
    if force:
        argv += ["--force-tier", force]
    code, out = cli(capsys, *argv)
    assert code == 0, out
    assert out["filed"]["filed"] is True, out
    return out


@pytest.fixture
def incident(tmp_path, src, gh, capsys) -> tuple[Path, Path]:
    """A project with a tier-3 incident (change 0001) filed, pushed and checked out."""
    root = project(tmp_path)
    file_incident(root, src, capsys)
    return root, incident_dir(root)


@pytest.fixture
def rollback_incident(tmp_path, src, gh, capsys) -> tuple[Path, Path]:
    """As ``incident``, with sdlc.yaml giving the rollback-deploy route a command."""
    root = project(tmp_path)
    add_rollback_runbook(root)
    file_incident(root, src, capsys)
    return root, incident_dir(root)


# --- run: log only below tier 2 ---------------------------------------------------------------
@pytest.mark.parametrize(
    ("make", "tier", "action"), [(lambda: series(16), 0, None), (tier1_series, 1, "log")]
)
def test_run_below_tier_2_only_logs(tmp_path, src, gh, capsys, monkeypatch, make, tier, action):
    root = project(tmp_path)
    src.observations = make()
    outfile = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(outfile))
    log = tmp_path / "logs" / "detect-log.jsonl"
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--log", str(log), "--file")
    assert code == 0
    assert (out["tier"], out["action"], out["outcome"], out["filed"]) == (
        tier,
        action,
        "logged",
        {},
    )
    assert src.calls and src.calls[0]["repo"] == REPO
    [line] = log.read_text(encoding="utf-8").splitlines()
    entry = json.loads(line)
    assert {"tier", "rule", "at", "outcome"} <= set(entry)
    assert (entry["tier"], entry["outcome"], entry["change_id"]) == (tier, "logged", None)
    lines = outfile.read_text(encoding="utf-8").splitlines()
    assert f"tier={tier}" in lines
    assert "change_id=" in lines and "head_ref=" in lines
    # nothing filed: no new change folder, no incident branch anywhere
    assert [p.name for p in change_dirs(root)] == ["0000-sdlc-init"]
    assert gitops.current_branch(root) == "main"
    assert not remote_has(root, "sdlc/0001/a")
    assert not git(root, "branch", "--list", "sdlc/*").strip()


def test_run_twice_appends_one_line_per_run(tmp_path, src, gh, capsys):
    root = project(tmp_path)
    log = tmp_path / "detect-log.jsonl"
    for _ in range(2):
        code, _out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--log", str(log))
        assert code == 0
    assert len(log.read_text(encoding="utf-8").splitlines()) == 2


# --- run: filing the incident ---------------------------------------------------------------
def test_run_spike_with_file_opens_the_incident_change(tmp_path, src, gh, capsys, monkeypatch):
    root = project(tmp_path)
    src.observations = series(16, spike=True)
    outfile = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(outfile))
    log = tmp_path / "detect-log.jsonl"
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--log", str(log), "--file")
    assert code == 0, out
    assert (out["tier"], out["rule"], out["action"]) == (3, "we1", "propose")
    assert out["filed"]["filed"] is True
    change_id = out["filed"]["change_id"]
    assert change_id == "0001"
    assert out["outcome"] == f"filed change {change_id}"
    change = incident_dir(root, change_id)
    st = status_mod.read_status(change)
    assert (st.entry_route, st.change_type, st.phase) == ("incident", "fix", "f")

    record = json.loads((change / "evidence" / "detection.json").read_text(encoding="utf-8"))
    assert finding.validate(record) == []
    assert record["signature"] == finding.signature(METRIC, "we1")
    assert (record["tier"], record["rule"], record["forced"]) == (3, "we1", False)
    assert record["failed_run_urls"] == [FAILED_URL]
    assert 0 < len(record["observations"]) <= finding.RECENT_POINTS
    assert record["observations"][-1]["at"] == "2026-09-16"

    # the commit is on sdlc/<id>/a and was pushed; main (local and remote) is untouched
    branch = f"sdlc/{change_id}/a"
    assert out["filed"]["branch"] == branch
    assert remote_has(root, branch)
    subject = git(bare(root), "log", "-1", "--format=%s", branch).strip()
    assert subject.startswith(f"maintain({change_id}): detection {METRIC} tier 3")
    rel = f"changes/{change.name}/evidence/detection.json"
    assert json.loads(git(bare(root), "show", f"{branch}:{rel}")) == record
    assert change.name not in git(bare(root), "ls-tree", "--name-only", "main", "changes/")
    # commit-phase leaves the checkout on the work branch; the CLI does not switch back
    assert gitops.current_branch(root) == branch

    lines = outfile.read_text(encoding="utf-8").splitlines()
    assert f"change_id={change_id}" in lines
    assert f"head_ref={branch}" in lines
    assert "tier=3" in lines
    [entry] = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert (entry["tier"], entry["rule"], entry["change_id"]) == (3, "we1", change_id)


def test_run_force_tier_2_on_a_flat_series_files_a_forced_finding(tmp_path, src, gh, capsys):
    root = project(tmp_path)
    out = file_incident(root, src, capsys, force="2")
    assert (out["tier"], out["rule"], out["forced"], out["action"]) == (
        2,
        "forced",
        True,
        "diagnose",
    )
    change = incident_dir(root, out["filed"]["change_id"])
    record = json.loads((change / "evidence" / "detection.json").read_text(encoding="utf-8"))
    assert finding.validate(record) == []
    assert (record["tier"], record["rule"], record["forced"]) == (2, "forced", True)
    assert record["signature"] == finding.signature(METRIC, "forced")
    assert record["breach_start"] == "2026-09-16"  # the latest point, when nothing tripped


def test_run_force_tier_with_no_observation_still_files_the_rehearsal(
    tmp_path, src, gh, capsys, monkeypatch
):
    """The workflow's force_tier input files an incident "whatever the metric says": on a
    repository whose every run is an excluded `SDLC ...` workflow the series is empty (live
    run of 2026-09-25), and the rehearsal is still filed, with no latest observation."""
    root = project(tmp_path)
    src.observations = []
    outfile = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(outfile))
    log = tmp_path / "detect-log.jsonl"
    argv = ["run", "--root", str(root), "--repo", REPO, "--log", str(log)]
    code, out = cli(capsys, *argv, "--force-tier", "2", "--file")
    assert code == 0, out
    assert out["forced"] is True
    assert out["tier"] == 2
    assert out["latest"] is None and out["breach_start"] is None
    assert "no complete-day observation" in out["reason"]
    assert out["filed"]["filed"] is True
    change_id = out["filed"]["change_id"]
    change = incident_dir(root, change_id)
    record = json.loads((change / "evidence" / "detection.json").read_text(encoding="utf-8"))
    assert finding.validate(record) == []
    assert record["latest"] is None
    assert record["forced"] is True
    assert record["observations"] == []
    assert record["failed_run_urls"] == [] and record["commits"] == []
    assert "no complete-day observation" in record["reason"]
    branch = f"sdlc/{change_id}/a"
    rel = f"changes/{change.name}/evidence/detection.json"
    assert json.loads(git(bare(root), "show", f"{branch}:{rel}")) == record
    [entry] = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert entry["change_id"] == change_id and entry["forced"] is True
    lines = outfile.read_text(encoding="utf-8").splitlines()
    assert f"change_id={change_id}" in lines and f"head_ref={branch}" in lines


def test_run_without_force_on_an_empty_series_logs_tier_0_and_files_nothing(
    tmp_path, src, gh, capsys
):
    root = project(tmp_path)
    src.observations = []
    log = tmp_path / "detect-log.jsonl"
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--log", str(log), "--file")
    assert code == 0
    assert (out["tier"], out["forced"], out["outcome"], out["filed"]) == (0, False, "logged", {})
    assert [p.name for p in change_dirs(root)] == ["0000-sdlc-init"]
    assert len(log.read_text(encoding="utf-8").splitlines()) == 1


def test_run_tier_3_without_file_names_the_flag_and_files_nothing(tmp_path, src, gh, capsys):
    root = project(tmp_path)
    src.observations = series(16, spike=True)
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO)
    assert code == 0
    assert out["tier"] == 3
    assert "run with --file" in out["outcome"]
    assert out["filed"] == {}
    assert [p.name for p in change_dirs(root)] == ["0000-sdlc-init"]
    assert gitops.current_branch(root) == "main"


def test_run_dry_run_files_nothing(tmp_path, src, gh, capsys):
    root = project(tmp_path)
    src.observations = series(16, spike=True)
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--file", "--dry-run")
    assert code == 0
    assert out["filed"]["dry_run"] is True and out["filed"]["filed"] is False
    assert out["outcome"] == "not filed: dry run"
    assert [p.name for p in change_dirs(root)] == ["0000-sdlc-init"]


def test_run_skips_a_dismissed_signature(tmp_path, src, gh, capsys):
    root = project(tmp_path)
    until = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
    path = dismissals.path_for(root)
    store = dismissals.add(
        dismissals.empty(),
        finding.signature(METRIC, "we1"),
        kind="detect",
        reason="a runner outage, not the code",
        by="owner",
        change_id="0009",
        until=until,
    )
    dismissals.save(path, store)
    git(root, "add", "changes/.dismissed.json")
    git(root, "commit", "-q", "-m", "dismiss(0009): a runner outage")
    src.observations = series(16, spike=True)
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--file")
    assert code == 0
    assert out["outcome"].startswith("dismissed")
    assert until in out["outcome"] and "a runner outage" in out["outcome"]
    assert out["dismissal"]["change_id"] == "0009"
    assert out["filed"] == {}
    assert [p.name for p in change_dirs(root)] == ["0000-sdlc-init"]
    assert not remote_has(root, "sdlc/0001/a")


def test_run_skips_while_an_incident_of_the_metric_is_open(tmp_path, src, gh, capsys):
    root = project(tmp_path)
    first = file_incident(root, src, capsys)
    assert first["filed"]["change_id"] == "0001"
    src.observations = series(20, spike=True)  # a fresh spike, days later
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--file")
    assert code == 0
    assert out["outcome"] == f"open incident 0001 already carries {METRIC}"
    assert [i["change_id"] for i in out["open_incidents"]] == ["0001"]
    assert out["filed"] == {}
    assert not [p for p in change_dirs(root) if p.name.startswith("0002-")]
    assert not remote_has(root, "sdlc/0002/a")


def test_run_source_error_exits_1_and_logs_the_error(tmp_path, src, gh, capsys):
    root = project(tmp_path)
    src.error = "GitHub API 503: unavailable"
    log = tmp_path / "detect-log.jsonl"
    code = detect_cli.main(["run", "--root", str(root), "--repo", REPO, "--log", str(log)])
    captured = capsys.readouterr()
    assert code == 1
    assert "503" in captured.err
    [entry] = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert "503" in entry["error"]
    assert entry["metric"] == METRIC


def test_run_with_a_bad_bands_file_is_a_usage_error(tmp_path):
    """Run as a subprocess: the invalid bands.yaml stops the run before any fetch."""
    root = project(tmp_path)
    bands = root / "bands.yaml"
    text = bands.read_text(encoding="utf-8")
    assert f"metric: {METRIC}\n" in text
    bands.write_text(text.replace(f"metric: {METRIC}\n", ""), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(DETECT_CLI), "run", "--root", str(root), "--repo", REPO],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 2, proc.stderr
    assert "missing metric" in proc.stderr
    assert proc.stdout.strip() == ""


def test_run_without_a_repo_is_a_usage_error(tmp_path, src, gh, capsys):
    root = project(tmp_path)  # origin is a local path: no owner/name to derive
    code, out = cli(capsys, "run", "--root", str(root))
    assert (code, out) == (2, None)
    assert src.calls == []


# --- routes -----------------------------------------------------------------------------------
def test_routes_at_tier_3_lists_the_template_routes(incident, capsys):
    root, _change = incident
    code, out = cli(capsys, "routes", "--root", str(root), "--id", "0001")
    assert code == 0
    tools = out["tools"].split(",")
    for tool in ("Read", "Grep", "Write", "Bash(python *)"):
        assert tool in tools
    assert len(tools) == len(set(tools))
    by_name = {r["route"]: r for r in out["routes"]}
    assert list(by_name) == [
        "pull_request",
        "runbook:quarantine-flaky-test",
        "runbook:revert-pr",
        "runbook:rollback-deploy",
    ]
    assert all(r["authorization"] in ("preapproved", "go") for r in out["routes"])
    assert by_name["runbook:rollback-deploy"]["authorization"] == "go"
    for builtin in ("runbook:quarantine-flaky-test", "runbook:revert-pr"):
        assert by_name[builtin]["builtin"] is True
        assert by_name[builtin]["args"]
    assert "sha" in by_name["runbook:revert-pr"]["args"]
    assert by_name["runbook:revert-pr"]["supported"] is True
    assert out["language"] == "python"
    assert by_name["runbook:quarantine-flaky-test"]["supported"] is True
    assert (out["tier"], out["proposal_shape"]["tier"]) == (3, 3)


def test_routes_at_tier_2_offers_only_the_pull_request(tmp_path, src, gh, capsys):
    root = project(tmp_path)
    out = file_incident(root, src, capsys, force="2")
    code, routes_out = cli(capsys, "routes", "--root", str(root), "--id", out["filed"]["change_id"])
    assert code == 0
    assert [r["route"] for r in routes_out["routes"]] == ["pull_request"]


def test_routes_of_an_unknown_change_is_a_usage_error(incident, capsys):
    root, _change = incident
    code, out = cli(capsys, "routes", "--root", str(root), "--id", "0042")
    assert (code, out) == (2, None)


# --- dispatch ---------------------------------------------------------------------------------
def test_dispatch_pull_request_needs_no_runbook(incident, spy, capsys):
    root, change = incident
    write_proposal(change, "pull_request")
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001")
    assert code == 0
    assert out["acted"] is True
    assert out["resolved"]["route"] == "pull_request"
    assert spy.calls == []
    assert runbook_records(change) == []


def test_dispatch_preapproved_revert_runs_records_and_commits(incident, spy, capsys):
    root, change = incident
    sha = "a" * 40
    write_proposal(change, "runbook:revert-pr", args={"sha": sha})
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001", "--commit")
    assert code == 0, out
    assert out["acted"] is True
    [(call_args, call_kwargs)] = spy.calls
    assert call_args[0] == "revert-pr" and call_args[2] == "0001"
    assert call_args[3] == {"sha": sha}
    assert call_kwargs["dry_run"] is False
    record = json.loads((change / "evidence" / "runbook-revert-pr.json").read_text("utf-8"))
    assert record["status"] == "ran"
    assert record["pr_url"] == "https://x/pr/9"
    assert record["authorization"]["authorization"] == "preapproved"
    assert out["commit"]["ok"] is True
    branch = "sdlc/0001/a"
    assert gitops.current_branch(root) == branch
    rel = f"changes/{change.name}/evidence/runbook-revert-pr.json"
    assert json.loads(git(root, "show", f"{branch}:{rel}"))["status"] == "ran"
    assert json.loads(git(bare(root), "show", f"{branch}:{rel}"))["status"] == "ran"  # pushed
    subject = git(root, "log", "-1", "--format=%s", branch).strip()
    assert subject == "maintain(0001): route runbook:revert-pr"


def test_dispatch_go_route_records_go_requested_and_runs_nothing(rollback_incident, spy, capsys):
    root, change = rollback_incident
    write_proposal(change, "runbook:rollback-deploy")
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001")
    assert code == 0, out
    assert out["acted"] is False
    assert out["outcome"]["status"] == "go-requested"
    assert spy.calls == []
    record = json.loads((change / "evidence" / "runbook-rollback-deploy.json").read_text("utf-8"))
    assert record["status"] == "go-requested"
    assert record["authorization"]["authorization"] == "go"


def test_dispatch_rollback_without_a_command_is_not_taken(incident, spy, capsys):
    """The template lists rollback-deploy but sdlc.yaml gives it no command: unsupported."""
    root, change = incident
    write_proposal(change, "runbook:rollback-deploy")
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001")
    assert code == 0
    assert out["acted"] is False
    assert "rollback-deploy" in out["reason"]
    assert spy.calls == [] and runbook_records(change) == []


def test_dispatch_refuses_an_unlisted_route(incident, spy, capsys):
    root, change = incident
    write_proposal(change, "runbook:restart-database")
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001")
    assert code == 0
    assert out["acted"] is False
    assert "not a route" in out["reason"]
    assert spy.calls == [] and runbook_records(change) == []


def test_dispatch_refuses_a_tier_mismatch(incident, spy, capsys):
    root, change = incident
    write_proposal(change, "pull_request", tier=2)
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001")
    assert code == 0
    assert out["acted"] is False
    assert "tier 2" in out["reason"] and "3" in out["reason"]
    assert spy.calls == [] and runbook_records(change) == []


def test_dispatch_without_a_proposal_says_so(incident, spy, capsys):
    root, _change = incident
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001")
    assert code == 0
    assert out["acted"] is False
    assert "proposal.json is missing" in out["reason"]


# --- go -------------------------------------------------------------------------------------
def test_go_by_a_person_runs_the_runbook_and_reruns_the_gate(rollback_incident, gh, spy, capsys):
    root, change = rollback_incident
    write_proposal(change, "runbook:rollback-deploy")
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001", "--repo", REPO)
    assert code == 0 and out["outcome"]["status"] == "go-requested"
    gh.actor = {"ok": True, "actor": "the-owner", "reason": ""}
    code, out = cli(
        capsys, "go", "--root", str(root), "--id", "0001", "--repo", REPO, "--pr-number", "12"
    )
    assert code == 0, out
    assert (out["performed"], out["actor"], out["route"]) == (
        True,
        "the-owner",
        "runbook:rollback-deploy",
    )
    assert len(spy.calls) == 1
    assert spy.calls[0][0][0] == "rollback-deploy"
    record = json.loads((change / "evidence" / "runbook-rollback-deploy.json").read_text("utf-8"))
    assert record["status"] == "ran"
    assert record["authorized_by"] == "the-owner"
    assert status_mod.read_status(change).runbook_authorized_by == "the-owner"
    [(args, _kw)] = gh.named("set_labels")
    assert args == (REPO, 12, [], ["sdlc:go"])
    [(args, _kw)] = gh.named("label_actor")
    assert args == (REPO, 12, "sdlc:go")
    assert (change / "evidence" / "gate-f.json").is_file()
    assert isinstance(out["gate"], dict)
    assert isinstance(out["pr"], dict)
    assert out["commit"]["ok"] is True
    rel = f"changes/{change.name}/status.yaml"
    assert "runbook_authorized_by: the-owner" in git(bare(root), "show", f"sdlc/0001/a:{rel}")


@pytest.mark.parametrize(
    ("actor", "why"),
    [("github-actions[bot]", "not by a person"), (None, "no `labeled` event")],
)
def test_go_not_by_a_person_performs_nothing(rollback_incident, gh, spy, capsys, actor, why):
    root, change = rollback_incident
    write_proposal(change, "runbook:rollback-deploy")
    gh.actor = {"ok": True, "actor": actor, "reason": ""}
    code, out = cli(
        capsys, "go", "--root", str(root), "--id", "0001", "--repo", REPO, "--pr-number", "12"
    )
    assert code == 0
    assert out["performed"] is False
    assert why in out["reason"]
    assert spy.calls == []
    assert gh.named("set_labels") == []  # the label is left where it is
    assert runbook_records(change) == []
    assert status_mod.read_status(change).runbook_authorized_by is None


def test_go_needs_repo_and_pr_number(incident, capsys):
    root, _change = incident
    code, out = cli(capsys, "go", "--root", str(root), "--id", "0001", "--repo", REPO)
    assert (code, out) == (2, None)


# --- dismiss ----------------------------------------------------------------------------------
def test_dismiss_with_a_reason_opens_the_dismissal_pr(incident, gh, capsys):
    root, _change = incident
    original = gitops.current_branch(root)
    main_sha = git(root, "rev-parse", "origin/main").strip()
    reason = "a runner outage on the 16th, not the code"
    code, out = cli(
        capsys, "dismiss", "--root", str(root), "--id", "0001", "--repo", REPO,
        "--pr-number", "12", "--reason", reason, "--by", "the-owner", "--open-pr",
    )  # fmt: skip
    assert code == 0, out
    assert out["dismissed"] is True
    signature = finding.signature(METRIC, "we1")
    until = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
    branch = "sdlc/0001/dismiss"
    stored = json.loads(git(bare(root), "show", f"{branch}:changes/.dismissed.json"))
    entry = stored["entries"][signature]
    assert (entry["kind"], entry["until"], entry["change_id"]) == ("detect", until, "0001")
    assert (entry["reason"], entry["by"]) == (reason, "the-owner")
    subject = git(bare(root), "log", "-1", "--format=%s", branch).strip()
    assert subject.startswith("dismiss(0001)")
    assert git(bare(root), "rev-parse", f"{branch}~1").strip() == main_sha  # from origin/main
    assert gitops.current_branch(root) == original
    [(args, kwargs)] = gh.named("create_pr")
    repo, base, head, title, body = args
    assert (repo, base, head) == (REPO, "main", branch)
    assert title == subject
    assert reason in body and signature in body
    assert kwargs["draft"] is False
    assert out["pr"]["url"] == "https://x/pr/13"


def test_dismiss_reads_the_reason_from_the_last_comment_by_a_person(incident, gh, capsys):
    root, _change = incident
    original = gitops.current_branch(root)
    gh.comments = {
        "ok": True,
        "reason": "",
        "comments": [
            {"author": "the-owner", "type": "User", "body": "flaky runner,\n  not the code"},
            {"author": "github-actions[bot]", "type": "Bot", "body": "parked: what I need"},
        ],
    }
    code, out = cli(
        capsys, "dismiss", "--root", str(root), "--id", "0001", "--repo", REPO, "--pr-number", "12"
    )
    assert code == 0, out
    assert out["dismissed"] is True
    assert (out["reason"], out["by"]) == ("flaky runner, not the code", "the-owner")
    stored = json.loads(git(root, "show", "sdlc/0001/dismiss:changes/.dismissed.json"))
    entry = stored["entries"][finding.signature(METRIC, "we1")]
    assert (entry["reason"], entry["by"]) == ("flaky runner, not the code", "the-owner")
    assert gitops.current_branch(root) == original
    assert gh.named("create_pr") == []  # no --open-pr


def test_dismiss_with_only_bot_comments_dismisses_nothing(incident, gh, capsys):
    root, _change = incident
    gh.comments = {
        "ok": True,
        "reason": "",
        "comments": [
            {"author": "renovate", "type": "Bot", "body": "an update"},
            {"author": "sdlc-helper[bot]", "type": "User", "body": "parked"},
        ],
    }
    code, out = cli(
        capsys, "dismiss", "--root", str(root), "--id", "0001", "--repo", REPO, "--pr-number", "12"
    )
    assert code == 0
    assert out["dismissed"] is False
    assert "no comment by a person" in out["reason"]
    assert not git(root, "branch", "--list", "sdlc/0001/dismiss").strip()


def test_dismiss_dry_run_writes_nothing(incident, gh, capsys):
    root, _change = incident
    head = git(root, "rev-parse", "HEAD").strip()
    code, out = cli(
        capsys, "dismiss", "--root", str(root), "--id", "0001", "--reason", "noise",
        "--by", "the-owner", "--dry-run",
    )  # fmt: skip
    assert code == 0
    assert (out["dismissed"], out["dry_run"], out["reason"]) == (False, True, "noise")
    assert out["until"] == (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
    assert not dismissals.path_for(root).exists()
    assert not git(root, "branch", "--list", "sdlc/0001/dismiss").strip()
    assert git(root, "rev-parse", "HEAD").strip() == head
    assert gh.calls == []


# --- maintain_tools ---------------------------------------------------------------------------
def test_maintain_tools_default_and_bands_tools_get_the_extras_once():
    default = detect_cli.maintain_tools(None).split(",")
    assert default[:3] == ["Read", "Grep", "Bash(gh run view *)"]
    assert default[3:] == list(detect_cli.MAINTAIN_EXTRA_TOOLS)
    only_read = bands_mod.Bands(
        metric=METRIC, source="", tiers={2: {"action": "diagnose", "tools": "Read"}}
    )
    assert detect_cli.maintain_tools(only_read).split(",") == [
        "Read",
        *detect_cli.MAINTAIN_EXTRA_TOOLS,
    ]
    overlapping = bands_mod.Bands(
        metric=METRIC, source="", tiers={2: {"action": "diagnose", "tools": "Read, Write,Glob"}}
    )
    tools = detect_cli.maintain_tools(overlapping).split(",")
    assert len(tools) == len(set(tools))
    assert tools[:3] == ["Read", "Write", "Glob"]
    assert set(detect_cli.MAINTAIN_EXTRA_TOOLS) <= set(tools)


# --- open_incidents ---------------------------------------------------------------------------
def test_open_incidents_is_empty_without_a_remote_incident(tmp_path):
    root = project(tmp_path)
    assert detect_cli.open_incidents(root, METRIC) == []


def test_open_incidents_finds_the_filed_one_for_its_metric_only(incident):
    root, _change = incident
    [found] = detect_cli.open_incidents(root, METRIC)
    assert (found["change_id"], found["ref"]) == ("0001", "origin/sdlc/0001/a")
    assert found["signature"] == finding.signature(METRIC, "we1")
    assert detect_cli.open_incidents(root, "p95_latency") == []


def test_open_incidents_ignores_an_abandoned_incident(incident):
    root, change = incident
    assert len(detect_cli.open_incidents(root, METRIC)) == 1  # found before the close
    st = status_mod.read_status(change)
    st.abandon("closed: a runner outage")
    status_mod.write_status(change, st)
    git(root, "add", "--", str(change / "status.yaml"))
    git(root, "commit", "-q", "-m", "abandon(0001)")
    git(root, "push", "-q", "origin", "sdlc/0001/a")
    assert detect_cli.open_incidents(root, METRIC) == []


def test_open_incidents_ignores_a_shipped_incident(incident):
    root, change = incident
    assert len(detect_cli.open_incidents(root, METRIC)) == 1  # found before the ship
    rel = f"changes/{change.name}"
    git(root, "checkout", "-q", "main")
    git(root, "checkout", "sdlc/0001/a", "--", rel)
    st = status_mod.read_status(root / rel)
    st.phase = "e"
    status_mod.write_status(root / rel, st)
    git(root, "add", "--", rel)
    git(root, "commit", "-q", "-m", "ship 0001 (as if the fix merged and deployed)")
    git(root, "push", "-q", "origin", "main")
    assert detect_cli.open_incidents(root, METRIC) == []


def test_open_incidents_ignores_a_merged_incident_abandoned_on_a_later_branch(incident):
    """The live sequence of 2026-09-25: the owner merges the incident PR (the folder lands on
    main at phase f; GitHub deletes sdlc/0001/a), then closes the design PR on sdlc/0001/b;
    abandon writes ``phase: abandoned`` on the change's branches only, never on main."""
    root, change = incident
    rel = f"changes/{change.name}"
    git(root, "checkout", "-q", "main")
    git(root, "merge", "-q", "--no-ff", "-m", "merge the incident PR", "sdlc/0001/a")
    git(root, "push", "-q", "origin", "main")
    git(root, "push", "-q", "origin", "--delete", "sdlc/0001/a")
    git(root, "fetch", "-q", "--prune", "origin")
    # control: merged and not abandoned, the incident is in flight until it ships
    [found] = detect_cli.open_incidents(root, METRIC)
    assert (found["change_id"], found["ref"]) == ("0001", "the checkout")
    git(root, "checkout", "-q", "-b", "sdlc/0001/b", "main")
    st = status_mod.read_status(root / rel)
    st.abandon("closed: the design PR")
    status_mod.write_status(root / rel, st)
    git(root, "add", "--", rel)
    git(root, "commit", "-q", "-m", "abandon(0001)")
    git(root, "push", "-q", "origin", "sdlc/0001/b")
    git(root, "checkout", "-q", "main")
    git(root, "fetch", "-q", "origin")
    assert not status_mod.read_status(root / rel).abandoned  # main still says phase f
    assert detect_cli.open_incidents(root, METRIC) == []
    assert detect_cli._remote_abandoned_ids(root) == {"0001"}


def test_dismiss_title_cuts_a_long_reason_at_a_word_boundary(incident, gh, capsys):
    root, _change = incident
    reason = (
        "Dismissed: the `.env` file is the framework's secrets-check fixture, committed on purpose"
    )
    code, out = cli(
        capsys, "dismiss", "--root", str(root), "--id", "0001", "--reason", reason,
        "--by", "the-owner",
    )  # fmt: skip
    assert code == 0, out
    subject = git(root, "log", "-1", "--format=%s", "sdlc/0001/dismiss").strip()
    assert subject == "dismiss(0001): Dismissed: the `.env` file is the framework's secrets-check"
    assert len(subject) <= len("dismiss(0001): ") + 60


# --- the session-5 review's fixes -------------------------------------------------------------
def test_run_accepts_the_workflow_s_empty_force_tier(tmp_path, src, gh, capsys):
    """The scheduled workflow passes --force-tier "" (its dispatch input's default): it means
    "force nothing", never a usage error (the first review found argparse refusing it)."""
    root = project(tmp_path)
    src.observations = series(16)
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--force-tier", "")
    assert code == 0 and out["forced"] is False and out["outcome"] == "logged"


def test_run_judges_complete_days_only(tmp_path, src, gh, capsys):
    """Today's first hours are not a day: the latest point judged is yesterday's."""
    from datetime import datetime, timezone

    root = project(tmp_path)
    src.observations = series(16, spike=True)
    today = datetime.now(timezone.utc).date().isoformat()
    src.observations.append({"at": today, "value": 0.0, "meta": {"runs": 1, "failed": 0}})
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO)
    assert code == 0 and out["tier"] == 3 and out["latest"]["at"] != today


def test_go_runs_only_a_route_that_asked_for_it(rollback_incident, gh, spy, capsys):
    root, change = rollback_incident
    write_proposal(change, "runbook:rollback-deploy")
    gh.actor = {"ok": True, "actor": "the-owner", "reason": ""}
    code, out = cli(
        capsys, "go", "--root", str(root), "--id", "0001", "--repo", REPO, "--pr-number", "12"
    )
    assert code == 0 and out["performed"] is False and "did not ask for Go" in out["reason"]
    assert spy.calls == [] and gh.named("set_labels") == []
    record = change / "evidence" / "runbook-rollback-deploy.json"
    record.write_text(json.dumps({"runbook": "rollback-deploy", "status": "ran"}), "utf-8")
    code, out = cli(
        capsys, "go", "--root", str(root), "--id", "0001", "--repo", REPO, "--pr-number", "12"
    )
    assert out["performed"] is False and "record: ran" in out["reason"] and spy.calls == []


def test_finish_dispatches_runs_the_gate_and_opens_the_pr(incident, gh, capsys):
    """The CI tail after the model's diagnosis-only session: dispatch, gate (f), the evidence
    commit and the intent PR, in one deterministic step that holds the runbook secrets."""
    root, change = incident
    # the model's diagnosis-only session wrote the intent and the proposal and committed them
    (change / "intent.md").write_text(
        "# Intent: CI failure rate breach\n"
        "Author: maintain run (phase f). Status: proposed. Change id: 0001. "
        "Entry route: incident abc.\n\n"
        "## Problem\nThe failure rate spiked.\n\n## Proposed outcome\nThe flaky test is "
        "quarantined.\n\n## Affected users and systems\nCI.\n\n## Constraints\nNone.\n\n"
        "## Open questions\nnone\n\n## Evidence\nwe1 at 3sigma; run https://x/runs/1.\n",
        encoding="utf-8",
    )
    write_proposal(change, "pull_request")
    git(root, "add", "changes")
    git(root, "commit", "-q", "-m", "maintain(0001): diagnosis")
    code, out = cli(capsys, "finish", "--root", str(root), "--id", "0001", "--repo", REPO)
    assert out["dispatch"]["acted"] is True
    failed = [ch for ch in out["gate"]["checks"] if not ch["ok"]]
    assert out["gate"]["result"] == "wait" and out["gate"]["label"] == "sdlc:f-ready", failed
    assert (change / "evidence" / "gate-f.json").is_file()
    assert out["evidence_commit"]["ok"] is True
    assert out["pr"]["route"] == "none" and code == 1  # no GitHub route in the test: red
    rel = f"changes/{change.name}/evidence/gate-f.json"
    assert git(bare(root), "show", f"sdlc/0001/a:{rel}")


def test_finish_judges_by_the_default_branch_s_bands_not_the_checkout_s(
    rollback_incident, gh, spy, capsys
):
    """Decision 14 "enforced, not remembered": an uncommitted edit of bands.yaml in the
    session (a prompt injection in a failed-run log could ask for one) changes no route's
    authorization - the dispatcher reads the default branch's copies."""
    root, change = rollback_incident
    write_proposal(change, "runbook:rollback-deploy")
    bands = root / "bands.yaml"
    bands.write_text(
        bands.read_text(encoding="utf-8").replace(
            "- name: runbook:rollback-deploy\n        authorization: go",
            "- name: runbook:rollback-deploy\n        authorization: preapproved",
        ),
        encoding="utf-8",
    )
    assert "authorization: preapproved" in bands.read_text(encoding="utf-8")
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001", "--repo", REPO)
    assert code == 0 and out["outcome"]["status"] == "go-requested", out
    assert spy.calls == []


def test_a_forced_finding_never_pre_approves_a_runbook(tmp_path, src, gh, spy, capsys):
    root = project(tmp_path)
    file_incident(root, src, capsys, force="3")
    change = incident_dir(root)
    write_proposal(change, "runbook:revert-pr", args={"sha": "0" * 40})
    code, out = cli(capsys, "dispatch", "--root", str(root), "--id", "0001", "--repo", REPO)
    assert code == 0 and out["outcome"]["status"] == "go-requested"
    assert "rehearsal" in out["resolved"]["source"] and spy.calls == []


def test_open_incidents_sees_a_merged_incident_on_the_default_branch(incident, src, gh, capsys):
    """GitHub may delete a merged head: an incident the owner merged (fix now) is a folder on
    the default branch until its fix ships, and still suppresses a second filing."""
    root, change = incident
    git(root, "checkout", "-q", "main")
    git(root, "merge", "-q", "--no-ff", "-m", "merge the incident (gate a)", "sdlc/0001/a")
    git(root, "push", "-q", "origin", "main")
    git(root, "push", "-q", "origin", "--delete", "sdlc/0001/a")
    git(root, "fetch", "-q", "--prune", "origin")
    found = detect_cli.open_incidents(root, METRIC)
    assert [i["change_id"] for i in found] == ["0001"] and found[0]["ref"] == "the checkout"
    src.observations = series(20, spike=True)
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--file")
    assert out["outcome"] == f"open incident 0001 already carries {METRIC}"


def test_a_pending_dismissal_branch_already_suppresses_the_finding(incident, src, gh, capsys):
    """The owner closed the incident with a comment; until the dismissal PR is merged the
    default branch's store is empty, and the pending branch must still mute the finding."""
    root, change = incident
    code, out = cli(
        capsys, "dismiss", "--root", str(root), "--id", "0001", "--reason", "runner outage",
        "--by", "owner", "--repo", REPO, "--pr-number", "5",
    )  # fmt: skip
    assert out["dismissed"] is True
    git(root, "push", "-q", "origin", "sdlc/0001/dismiss")
    git(root, "fetch", "-q", "origin")
    # the incident itself is abandoned (the abandon workflow ran)
    st = status_mod.read_status(change)
    st.abandon("pull request 5 closed without a merge")
    status_mod.write_status(change, st)
    git(root, "add", "changes")
    git(root, "commit", "-q", "-m", "abandon")
    git(root, "push", "-q", "origin", "sdlc/0001/a")
    src.observations = series(20, spike=True)
    code, out = cli(capsys, "run", "--root", str(root), "--repo", REPO, "--file")
    assert out["outcome"].startswith("dismissed until") and out["filed"] == {}
    assert out["dismissal"]["pending"] == "origin/sdlc/0001/dismiss"


# --- $GITHUB_OUTPUT and a failing commit (live run of 2026-09-25) -----------------------------
def test_github_output_writes_multi_line_values_in_the_heredoc_form(tmp_path):
    """``key=value`` is one line per value: a multi-line value (a traceback) made the runner
    reject the file ("Invalid format"); it goes in GitHub's ``key<<DELIM`` form instead."""
    outfile = tmp_path / "github_output"
    value = 'Traceback (most recent call last):\n  File "x.py", line 1\nfatal: boom'
    detect_cli._github_output(
        {"tier": 2, "outcome": value, "change_id": None}, env={"GITHUB_OUTPUT": str(outfile)}
    )
    lines = outfile.read_text(encoding="utf-8").split("\n")
    assert lines[0] == "tier=2"
    key, _, delim = lines[1].partition("<<")
    assert key == "outcome" and delim.startswith("ghadelimiter_")
    end = lines.index(delim, 2)
    assert "\n".join(lines[2:end]) == value
    assert all(delim not in line for line in lines[2:end])
    assert lines[end + 1 :] == ["change_id=", ""]
    # two multi-line values never share a delimiter
    detect_cli._github_output({"a": "1\n2", "b": "3\n4"}, env={"GITHUB_OUTPUT": str(outfile)})
    heads = [x for x in outfile.read_text(encoding="utf-8").splitlines() if "<<" in x]
    assert len({h.partition("<<")[2] for h in heads}) == 3


def test_a_failing_commit_phase_keeps_the_reason_to_one_line(
    tmp_path, src, gh, capsys, monkeypatch
):
    """A git failure in ``commit-phase`` ("empty ident name" on a runner) is reported as its
    last stderr line; the whole stderr stays in the printed JSON only."""
    root = project(tmp_path)
    src.observations = series(16)
    stderr = "line1\nline2\nfatal: empty ident name"
    real_cli = detect_cli._cli

    def fake_cli(script, argv, cwd):
        if argv and argv[0] == "commit-phase":
            return None, 1, stderr
        return real_cli(script, argv, cwd)

    monkeypatch.setattr(detect_cli, "_cli", fake_cli)
    outfile = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(outfile))
    log = tmp_path / "detect-log.jsonl"
    argv = ["run", "--root", str(root), "--repo", REPO, "--log", str(log)]
    code, out = cli(capsys, *argv, "--force-tier", "2", "--file")
    assert code == 1, out
    filed = out["filed"]
    assert filed["filed"] is False
    assert filed["reason"] == "commit-phase failed: fatal: empty ident name"
    assert filed["stderr"] == stderr
    [entry] = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert "\n" not in entry["outcome"]
    assert entry["outcome"] == "not filed: commit-phase failed: fatal: empty ident name"
    lines = outfile.read_text(encoding="utf-8").splitlines()
    assert "outcome=not filed: commit-phase failed: fatal: empty ident name" in lines


def test_default_branch_prefers_the_explicit_environment_value(tmp_path, monkeypatch):
    """The workflows set ``SDLC_DEFAULT_BRANCH`` from the repository's default branch: it
    wins over the git guess, which on a checkout of a PR head could name that head (live run
    of 2026-09-25). An empty value falls back to the guess."""
    root = project(tmp_path)
    git(root, "checkout", "-q", "-b", "shakedown/detect")
    monkeypatch.setenv("SDLC_DEFAULT_BRANCH", "trunk")
    assert detect_cli._default_branch(root) == "trunk"
    monkeypatch.setenv("SDLC_DEFAULT_BRANCH", "")
    assert detect_cli._default_branch(root) == "main"


def test_run_default_branch_argument_sets_the_filing_s_start_point(
    tmp_path, src, gh, capsys, monkeypatch
):
    """``--default-branch trunk`` wins over the guess (origin/HEAD is main here): the
    incident branch starts from origin/trunk, not from the checkout's own branch."""
    root = project(tmp_path)
    git(root, "checkout", "-q", "-b", "shakedown/detect")
    monkeypatch.setenv("SDLC_DEFAULT_BRANCH", "")  # restored after main() sets it
    src.observations = series(16)
    seen: list[list[str]] = []
    real_cli = detect_cli._cli

    def spy_cli(script, argv, cwd):
        if argv and argv[0] == "commit-phase":
            seen.append(list(argv))
            return None, 1, "fatal: stop here"
        return real_cli(script, argv, cwd)

    monkeypatch.setattr(detect_cli, "_cli", spy_cli)
    argv = ["run", "--root", str(root), "--repo", REPO, "--default-branch", "trunk"]
    code, out = cli(capsys, *argv, "--force-tier", "2", "--file")
    assert code == 1, out
    [commit_phase] = seen
    assert commit_phase[commit_phase.index("--start-point") + 1] == "origin/trunk"
