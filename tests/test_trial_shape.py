"""R61 (the trial project's shape) and R33 (the formatter follows the project's languages),
plugin 1.0.29: detection on a mixed repository, the registry hosts, the formatter commands,
the secret-shaped paths, the maintain metric's workflow, the targets' duration and
environment, the CI session's settings and the formatter hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin"))
sys.path.insert(0, str(ROOT / "plugin" / "hooks"))

import format_on_edit  # noqa: E402
from ci import run_phase  # noqa: E402

from init import detect, sdlc_init  # noqa: E402
from init.render import render_file  # noqa: E402
from state import yamlish  # noqa: E402

INIT = ROOT / "plugin" / "init" / "sdlc_init.py"


def _write(root: Path, rel: str, text: str = "") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _run_init(root: Path, *extra: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(INIT), "--root", str(root), *extra],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


# --- part 2: which language ----------------------------------------------------------------- ----
def test_a_helper_python_file_no_longer_makes_a_node_project_python(tmp_path):
    _write(tmp_path, "package.json", json.dumps({"scripts": {"test": "jest"}}))
    for n in range(5):
        _write(tmp_path, f"src/m{n}.ts", "export {};\n")
    _write(tmp_path, "scripts/release.py", "print(1)\n")
    det = detect.detect(tmp_path)
    assert det.language == "node" and det.test.command == "npm test"
    assert det.signals["python"] == {"files": 1, "manifests": []}
    assert det.signals["node"] == {"files": 5, "manifests": ["package.json"]}


def test_a_go_project_with_one_python_file_asks_for_the_commands(tmp_path):
    _write(tmp_path, "go.mod", "module x\n")
    for n in range(4):
        _write(tmp_path, f"pkg/f{n}.go", "package pkg\n")
    _write(tmp_path, "tools/gen.py", "print(1)\n")
    det = detect.detect(tmp_path)
    assert det.language == "go"
    assert (det.build.command, det.test.command, det.lint.command, det.setup.command) == (
        None,
        None,
        None,
        None,
    )
    assert "ask the owner" in det.notes[0] and "go 4 file(s) (go.mod)" in det.notes[0]
    assert det.as_dict()["signals"]["go"]["files"] == 4


def test_a_mixed_repository_is_not_given_python_targets(tmp_path):
    _write(tmp_path, "pyproject.toml", "[project]\nname = 'x'\n")
    _write(tmp_path, "package.json", "{}")
    for n in range(3):
        _write(tmp_path, f"api/m{n}.py", "x = 1\n")
        _write(tmp_path, f"web/c{n}.tsx", "export {};\n")
    det = detect.detect(tmp_path)
    assert det.language == "python" and det.test.command is None
    assert det.notes[0].startswith("mixed repository (")


def test_a_node_frontend_in_a_subfolder_takes_part(tmp_path):
    """The review of 1.0.29: a manifest counts in any folder, so `web/package.json` with more
    TypeScript than the root's Python makes the repository mixed, not Python."""
    _write(tmp_path, "pyproject.toml", "[tool.pytest.ini_options]\n")
    for n in range(3):
        _write(tmp_path, f"m{n}.py", "x = 1\n")
    _write(tmp_path, "web/package.json", "{}")
    for n in range(8):
        _write(tmp_path, f"web/src/c{n}.tsx", "export {};\n")
    det = detect.detect(tmp_path)
    assert det.language == "node" and det.test.command is None
    assert "no package.json at the root" in det.notes[0]


def test_a_virtualenv_of_any_name_and_ignored_files_are_not_counted(tmp_path):
    _write(tmp_path, "package.json", json.dumps({"scripts": {"test": "jest"}}))
    for n in range(5):
        _write(tmp_path, f"src/m{n}.ts", "export {};\n")
    _write(tmp_path, ".venv-docs/pyvenv.cfg", "home = /usr\n")
    for n in range(20):
        _write(tmp_path, f".venv-docs/lib/m{n}.py", "x = 1\n")
    assert detect.detect(tmp_path).language == "node"  # no git: the walk prunes the venv
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    _write(tmp_path, ".gitignore", "build-out/\n")
    for n in range(20):
        _write(tmp_path, f"build-out/m{n}.py", "x = 1\n")
    assert "build-out/m0.py" not in detect.project_files(tmp_path)
    assert detect.detect(tmp_path).language == "node"


def test_on_a_runner_a_planted_git_program_is_refused_and_the_walk_used(tmp_path, monkeypatch):
    """The gate, the detection, the runbooks and the scan call detect() on the runner, on a
    checkout the session wrote: the file list goes through gitops (R44, I4), which refuses a
    config key that runs a program, and the walk stands in."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    marker = tmp_path.parent / f"{tmp_path.name}-ran"
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "alias.ls-files", f"!touch {marker}"], check=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "core.fsmonitor", f"touch {marker}"], check=True
    )
    _write(tmp_path, ".gitignore", "out/\n")
    _write(tmp_path, "out/gen.py", "x = 1\n")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    files = detect.project_files(tmp_path)
    assert "out/gen.py" in files  # the walk, which reads ignored files too
    assert not marker.exists()


def test_a_python_project_with_some_javascript_keeps_its_targets(tmp_path):
    _write(tmp_path, "pyproject.toml", "[tool.pytest.ini_options]\n")
    for n in range(4):
        _write(tmp_path, f"app/m{n}.py", "x = 1\n")
    _write(tmp_path, "app/static/site.js", "1;\n")  # no package.json: no Node signal
    assert detect.detect(tmp_path).test.command == "python -m pytest"


# --- part 1: the registry hosts; R33: the formatter commands ------------------------------ ------
def test_registries_follow_the_languages_found(tmp_path):
    _write(tmp_path, "Cargo.toml", '[package]\nname = "x"\nedition = "2018"\n')
    _write(tmp_path, "src/main.rs", "fn main() {}\n")
    signals = detect.language_signals(tmp_path)
    assert detect.registry_domains(signals) == ["crates.io", "index.crates.io", "static.crates.io"]
    assert detect.formatters(tmp_path, signals) == [
        {"glob": "*.rs", "fix": ["rustfmt --edition 2018 {file}"]}
    ]
    python_only = tmp_path / "py"
    _write(python_only, "app.py", "x = 1\n")
    assert detect.registry_domains(detect.language_signals(python_only)) == []  # in the base list


def test_node_dependencies_read_both_blocks_and_propose_prettier_and_eslint(tmp_path):
    pkg = {"dependencies": {"react": "1"}, "devDependencies": {"prettier": "3", "eslint": "9"}}
    assert detect.node_dependencies(pkg) == {"react", "prettier", "eslint"}
    _write(tmp_path, "package.json", json.dumps(pkg))
    (entry,) = detect.formatters(tmp_path)
    assert entry["glob"] == detect.NODE_GLOBS
    assert entry["fix"] == ["npx --no prettier --write {file}", "npx --no eslint --fix {file}"]
    assert entry["check"] == ["npx --no eslint {file}"]


def test_a_black_project_gets_its_own_formatter_not_ruff(tmp_path):
    _write(tmp_path, "pyproject.toml", "[tool.black]\nline-length = 88\n")
    _write(tmp_path, "m.py", "x = 1\n")
    assert detect.formatters(tmp_path) == [
        {"glob": ["*.py", "*.pyi"], "fix": ["python -m black --quiet {file}"]}
    ]
    _write(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    assert detect.formatters(tmp_path) == []  # ruff stays the default, with no entry


# --- part 5: the secret-shaped paths ---------------------------------------------------------- --
def test_a_gitignored_secret_file_is_still_proposed(tmp_path):
    """A local key is usually gitignored: the scan walks the disk, not git's list."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    _write(tmp_path, ".gitignore", "certs/\n")
    _write(tmp_path, "certs/dev.pem")
    assert "certs/dev.pem" not in detect.project_files(tmp_path)
    assert detect.secret_paths(tmp_path) == ["*.pem"]
    assert detect.detect(tmp_path).secrets == ["*.pem"]


def test_secret_shaped_paths_are_proposed(tmp_path):
    _write(tmp_path, "certs/server.pem")
    _write(tmp_path, "deploy/credentials.json")
    _write(tmp_path, ".npmrc")
    _write(tmp_path, "node_modules/pkg/test.key")  # a tool folder: left out
    assert detect.secret_paths(tmp_path) == ["*.pem", "credentials.json", ".npmrc"]
    assert sdlc_init.read_deny_rules(["*.pem"]) == ["Read(*.pem)", "Read(**/*.pem)"]


# --- the install writes all of it -------------------------------------------------------------- -
def _rust_project(root: Path) -> Path:
    _write(root, "Cargo.toml", '[package]\nname = "x"\nedition = "2021"\n')
    _write(root, "src/main.rs", "fn main() {}\n")
    _write(root, "keys/dev.pem")
    return root


def test_init_on_a_rust_project_writes_the_shape(tmp_path):
    root = _rust_project(tmp_path / "rs")
    report = _run_init(
        root, "--build", "cargo build", "--test", "cargo test", "--lint", "cargo clippy",
        "--setup", "", "--env", "TEST_DB_URL",
    )  # fmt: skip
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    cfg = yamlish.loads(text)
    assert cfg["sandbox"]["allowed_domains"] == ["crates.io", "index.crates.io", "static.crates.io"]
    assert cfg["protected_paths"] == ["*.pem"]
    assert cfg["hooks"] == {
        "formatters": [{"glob": "*.rs", "fix": ["rustfmt --edition 2021 {file}"]}]
    }
    assert cfg["commands"]["env"] == ["TEST_DB_URL"]
    yaml = pytest.importorskip("yaml")
    assert yaml.safe_load(text) == cfg
    settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert {"Read(*.pem)", "Read(**/*.pem)"} <= set(settings["permissions"]["deny"])
    assert "crates.io" in settings["sandbox"]["network"]["allowedDomains"]
    assert report["proposed"]["protected_paths"] == ["*.pem"]
    build = yaml.safe_load((root / ".github" / "workflows" / "sdlc-build.yml").read_text())
    steps = build["jobs"][next(iter(build["jobs"]))]["steps"]
    named = [s for s in steps if "TEST_DB_URL" in (s.get("env") or {})]
    assert len(named) == 2  # the setup step and the phase step
    assert named[0]["env"]["TEST_DB_URL"] == "${{ secrets.TEST_DB_URL || vars.TEST_DB_URL }}"


def test_a_re_run_keeps_the_env_names_and_the_owner_s_lists(tmp_path):
    """The review of 1.0.29: a re-run without --env still writes the names sdlc.yaml lists
    into a reinstalled workflow; settings follow the protected_paths and allowed_domains the
    kept sdlc.yaml carries, and the report names what it did not add."""
    root = _rust_project(tmp_path / "rs")
    _run_init(root, "--test", "cargo test", "--env", "TEST_DB_URL")
    path = root / "sdlc.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace('protected_paths: ["*.pem"]', "protected_paths: []")
    text = text.replace('"index.crates.io", ', "")
    path.write_text(text, encoding="utf-8")
    (root / ".claude" / "settings.json").unlink()
    (root / ".github" / "workflows" / "sdlc-build.yml").unlink()
    report = _run_init(root, "--test", "cargo test", "--env", "OTHER_TOKEN")
    build = (root / ".github" / "workflows" / "sdlc-build.yml").read_text(encoding="utf-8")
    assert "TEST_DB_URL: ${{ secrets.TEST_DB_URL" in build and "OTHER_TOKEN:" in build
    assert any("add OTHER_TOKEN to it" in n for n in report["notes"])
    settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Read(*.pem)" not in settings["permissions"]["deny"]
    assert "index.crates.io" not in settings["sandbox"]["network"]["allowedDomains"]
    assert any("*.pem" in n and "protected_paths" in n for n in report["notes"])
    assert report["files"][".github/workflows/sdlc-design.yml"].endswith(
        "may lack the commands.env lines for TEST_DB_URL, OTHER_TOKEN"
    )


def test_init_refuses_a_reserved_env_name(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(INIT), "--root", str(tmp_path), "--env", "GITHUB_TOKEN"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2 and "reserved" in proc.stderr
    assert not (tmp_path / "sdlc.yaml").exists()


def test_an_upgrade_adds_the_new_keys_and_keeps_the_comments(tmp_path):
    """A project written by 1.0.27 (``hooks.format_on_edit``, no ``sandbox`` block) gains
    ``hooks.formatters`` and ``sandbox`` by a text edit, its comments kept."""
    root = _rust_project(tmp_path / "rs")
    _run_init(root, "--test", "cargo test")
    path = root / "sdlc.yaml"
    old = path.read_text(encoding="utf-8")
    head, _, rest = old.partition("hooks:\n")
    pinned = rest[rest.index("# --- pinned process") :]
    old = "# my own note\n" + head + "hooks:\n  format_on_edit: true\n\n" + pinned
    path.write_text(old, encoding="utf-8")
    report = _run_init(root, "--test", "cargo test")
    assert "hooks.formatters" in report["files"]["sdlc.yaml"]
    assert "sandbox" in report["files"]["sdlc.yaml"]
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# my own note\n")
    cfg = yamlish.loads(text)
    assert cfg["hooks"]["format_on_edit"] is True  # kept as the owner's; no longer read
    assert cfg["hooks"]["formatters"][0]["glob"] == "*.rs"
    assert cfg["sandbox"]["allowed_domains"][0] == "crates.io"


# --- part 3: the maintain metric's workflow -----------------------------------------------------
def test_the_maintain_source_names_the_workflow_that_runs_the_tests(tmp_path):
    _write(tmp_path, "m.py", "x = 1\n")
    _write(tmp_path, "pyproject.toml", "[tool.pytest.ini_options]\n")
    wf = tmp_path / ".github" / "workflows"
    _write(
        wf, "ci.yml", 'name: "CI: tests"\non: push\njobs: {t: {steps: [{run: python -m pytest}]}}\n'
    )
    _write(wf, "lint.yml", "name: Lint\non: push\n")
    _write(wf, "nightly.yml", "name: Nightly # docs\non: schedule\n")
    report = _run_init(tmp_path, "--detect-only")
    assert report["maintain"]["source"] == "github-actions:CI: tests"
    assert report["maintain"]["observation"].startswith("ok: 1 project workflow(s)")
    _run_init(tmp_path)
    cfg = yamlish.load_file(tmp_path / "sdlc.yaml")
    assert cfg["maintain"]["source"] == "github-actions:CI: tests"
    assert yamlish.load_file(tmp_path / "bands.yaml")["source"] == "github-actions:CI: tests"
    # the owner's own answer wins
    report = _run_init(tmp_path, "--detect-only", "--maintain-source", "github-actions")
    assert report["maintain"]["source"] == "github-actions"


def test_a_runner_installed_or_named_in_a_comment_is_not_taken_for_the_tests(tmp_path):
    wf = tmp_path / ".github" / "workflows"
    _write(wf, "a.yml", "name: Evals\njobs:\n  e:\n    steps:\n      - run: pip install pytest\n")
    _write(wf, "b.yml", "name: Checks\n# runs pytest via tasks.py\njobs: {}\n")
    assert sdlc_init.testing_workflow(tmp_path, "python -m pytest") is None


def test_a_re_run_reports_the_source_sdlc_yaml_keeps(tmp_path):
    _write(tmp_path, "m.py", "x = 1\n")
    _run_init(tmp_path)  # one workflow or none: github-actions
    wf = tmp_path / ".github" / "workflows"
    _write(wf, "ci.yml", "name: CI\njobs: {t: {steps: [{run: python -m unittest}]}}\n")
    _write(wf, "lint.yml", "name: Lint\n")
    report = _run_init(tmp_path)
    assert report["maintain"]["source"] == "github-actions"
    assert report["maintain"]["why"] == "kept from sdlc.yaml"


def test_time_commands_before_the_install_says_so(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(INIT), "--root", str(tmp_path), "--time-commands"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2 and "run the install first" in proc.stderr


def test_one_workflow_keeps_the_plain_source(tmp_path):
    _write(tmp_path / ".github" / "workflows", "ci.yml", "name: CI\n")
    args = sdlc_init.build_parser().parse_args(["--root", str(tmp_path)])
    det = detect.detect(tmp_path)
    assert sdlc_init.maintain_source(tmp_path, args, det)[0] == "github-actions"


# --- part 4: the targets' duration and environment -------------------------------------------- --
def test_time_commands_raises_the_timeout_to_three_times_the_longest_run(tmp_path):
    root = tmp_path / "p"
    _write(root, "m.py", "x = 1\n")
    _run_init(root)
    durations = iter([0, 10, 100, 700, 1000, 1001])  # build 10 s, test 600 s, lint 1 s
    calls = []

    def fake_run(command, cwd, timeout):
        calls.append((command, timeout))
        return {"command": command, "exit_code": 0, "output": "ok"}

    report = sdlc_init.time_commands(root, run_command=fake_run, clock=lambda: next(durations))
    assert [t["seconds"] for t in report["targets"]] == [10, 600, 1]
    assert all(timeout == 900 for _c, timeout in calls)
    assert report["command_timeout"] == "raised from 900 to 1800"
    cfg = yamlish.load_file(root / "sdlc.yaml")
    assert cfg["gate"]["command_timeout"] == 1800
    assert report["workflows"].startswith("raise timeout-minutes and SDLC_JOB_TIMEOUT_MINUTES")
    assert "timed_out" not in report and not any(t["timed_out"] for t in report["targets"])
    # a quick project keeps the template's value and the job's minutes
    durations = iter([0, 1, 1, 2, 2, 3])
    root2 = tmp_path / "q"
    _write(root2, "m.py", "x = 1\n")
    _run_init(root2)
    report = sdlc_init.time_commands(root2, run_command=fake_run, clock=lambda: next(durations))
    assert report["command_timeout"].startswith("kept at 900")
    assert report["workflows"].startswith("unchanged")


def test_time_commands_says_when_a_target_hit_the_timeout(tmp_path):
    root = tmp_path / "p"
    _write(root, "m.py", "x = 1\n")
    _run_init(root)
    durations = iter([0, 1, 1, 901, 901, 902])

    def fake_run(command, cwd, timeout):
        timed_out = "unittest" in command
        return {"command": command, "exit_code": None if timed_out else 0, "output": ""}

    report = sdlc_init.time_commands(root, run_command=fake_run, clock=lambda: next(durations))
    assert [t["timed_out"] for t in report["targets"]] == [False, True, False]
    assert report["timed_out"].startswith("a target hit the timeout")


def test_the_session_s_bash_timeout_follows_command_timeout(tmp_path):
    config = {"gate": {"command_timeout": 1200}}
    env = run_phase.session_env({"PATH": "/bin"}, tmp_path, "c", config)
    assert env["BASH_DEFAULT_TIMEOUT_MS"] == env["BASH_MAX_TIMEOUT_MS"] == "1200000"
    kept = run_phase.session_env({"BASH_DEFAULT_TIMEOUT_MS": "5"}, tmp_path, "c", config)
    assert kept["BASH_DEFAULT_TIMEOUT_MS"] == "5"  # the workflow's own value wins


# --- the CI session's settings (parts 1 and 5) ----------------------------------------------- ---
def test_ci_settings_follow_the_project(tmp_path):
    _write(
        tmp_path,
        "sdlc.yaml",
        "commands:\n"
        '  build: "cargo build --release"\n'
        '  test: "cargo test"\n'
        '  lint: "echo no lint target"\n'
        '  setup: ""\n'
        "sandbox:\n"
        '  allowed_domains: ["crates.io", "*.crates.io", "evil.com/path", "a b"]\n'
        'protected_paths: ["*.pem", "config/credentials.json", "migrations/", "gen/"]\n',
    )
    data = json.loads(run_phase.ci_settings_file(ROOT, tmp_path).read_text(encoding="utf-8"))
    allow = data["permissions"]["allow"]
    assert "Bash(cargo build --release *)" in allow and "Bash(cargo test *)" in allow
    assert not any(r.startswith("Bash(echo") for r in allow)
    domains = data["sandbox"]["network"]["allowedDomains"]
    assert domains[-2:] == ["crates.io", "*.crates.io"]  # malformed entries left out
    base = run_phase._posix_root(tmp_path.resolve().as_posix())
    deny = data["permissions"]["deny"]
    for rule in (
        f"Read({base}/*.pem)",
        f"Read({base}/**/*.pem)",
        f"Read({base}/config/credentials.json)",
    ):
        assert rule in deny, rule
    assert f"Read({base}/**/config/credentials.json)" not in deny  # anchored: the root only
    # the review of 1.0.29: the sandbox hides a denied path from the tests too, so a protected
    # folder that is not secret-shaped stays readable (it stays unwritable: denyWrite)
    assert not any("migrations" in r or "gen" in r for r in deny if r.startswith("Read("))


# --- R33: the formatter hook --------------------------------------------------------------------
FAKE = """import os, sys
path = sys.argv[2]
mode = sys.argv[1]
with open(os.path.join(os.environ["LOG_DIR"], "calls.txt"), "a", encoding="utf-8") as fh:
    fh.write(mode + " " + path + " " + str("ANTHROPIC_API_KEY" in os.environ) + "\\n")
if mode == "fix":
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("fixed\\n")
sys.exit({"fix": 0, "check1": 1, "check2": 2}[mode])
"""


def _hook_project(tmp_path: Path, check: str) -> tuple[Path, Path]:
    fake = _write(tmp_path / "tools", "fmt.py", FAKE)
    py = sys.executable.replace("\\", "/")
    root = tmp_path / "proj"
    _write(
        root,
        "sdlc.yaml",
        "hooks:\n  formatters:\n"
        f'    - glob: ["*.ts"]\n      fix: ["\\"{py}\\" \\"{fake.as_posix()}\\" fix {{file}}"]\n'
        f'      check: ["\\"{py}\\" \\"{fake.as_posix()}\\" {check} {{file}}"]\n',
    )
    return root, _write(root, "src/a & b.ts", "x\n")


def _payload(path: Path, root: Path) -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": str(path)}, "cwd": str(root)}


@pytest.mark.parametrize("check, blocks", [("check1", True), ("check2", False)])
def test_the_hook_runs_the_project_s_commands(tmp_path, monkeypatch, check, blocks):
    root, target = _hook_project(tmp_path, check)
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    d = format_on_edit.decide(_payload(target, root), [], env={"CLAUDE_PROJECT_DIR": str(root)})
    assert d.block is blocks
    assert target.read_text(encoding="utf-8") == "x\nfixed\n"
    calls = (tmp_path / "calls.txt").read_text(encoding="utf-8").splitlines()
    rel = os.path.join("src", "a & b.ts")
    assert calls == [f"fix {rel} False", f"{check} {rel} False"]  # the path whole, no key
    assert [c["exit_code"] for c in d.log["commands"]] == [0, int(check[-1])]


def test_a_ci_session_does_not_run_the_project_s_commands(tmp_path, monkeypatch):
    """The review of 1.0.29: a hook runs outside the sandbox, and a project command runs code
    the session can write (an eslint configuration), so a CI session leaves it to the lint
    target."""
    root, target = _hook_project(tmp_path, "check1")
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    env = {"CLAUDE_PROJECT_DIR": str(root), "SDLC_GATE_COMMANDS": "runner"}
    d = format_on_edit.decide(_payload(target, root), [], env=env)
    assert not d.block and target.read_text(encoding="utf-8") == "x\n"
    assert not (tmp_path / "calls.txt").exists()
    assert format_on_edit.ci_session({"GITHUB_ACTIONS": "true"})


def test_a_tool_npx_cannot_find_never_blocks(tmp_path):
    def fake_run(command, cwd, timeout, env=None):
        return {"exit_code": 1, "output": "npm error npx canceled due to missing packages"}

    entry = {"glob": ["*"], "fix": [], "check": ["npx --no eslint {file}"]}
    clean, _note = format_on_edit.run_project_commands(entry, "a.ts", tmp_path, [], fake_run)
    assert clean


def test_a_missing_tool_and_a_bad_mapping_never_block(tmp_path):
    root = tmp_path / "proj"
    _write(
        root,
        "sdlc.yaml",
        'hooks:\n  formatters:\n    - glob: "*.ts"\n      fix: ["no-such-tool-xyz {file}"]\n',
    )
    target = _write(root, "a.ts", "x\n")
    d = format_on_edit.decide(_payload(target, root), [], env={"CLAUDE_PROJECT_DIR": str(root)})
    # cmd.exe exits 1 for an unknown command, a POSIX shell 127: a fixer's exit is never a block
    assert not d.block and d.log["commands"][0]["exit_code"] != 0
    _write(root, "sdlc.yaml", "hooks:\n  formatters: [a, b]\n")
    assert not format_on_edit.decide(
        _payload(target, root), [], env={"CLAUDE_PROJECT_DIR": str(root)}
    ).block


def test_an_explicit_python_entry_replaces_ruff(tmp_path, monkeypatch):
    root, _ = _hook_project(tmp_path, "check2")
    text = (root / "sdlc.yaml").read_text(encoding="utf-8").replace('"*.ts"', '"*.py"')
    (root / "sdlc.yaml").write_text(text, encoding="utf-8")
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    target = _write(root, "m.py", "x=1\n")
    format_on_edit.decide(_payload(target, root), [], env={"CLAUDE_PROJECT_DIR": str(root)})
    assert target.read_text(encoding="utf-8") == "x=1\nfixed\n"  # not ruff's "x = 1"


def test_the_budget_stops_the_commands(tmp_path, monkeypatch):
    monkeypatch.setattr(format_on_edit, "BUDGET", 0)
    ran: list = []
    entry = {"glob": ["*"], "fix": ["anything {file}"], "check": []}
    clean, note = format_on_edit.run_project_commands(entry, "a.ts", tmp_path, ran)
    assert clean and "budget" in note and ran == []


def test_a_path_that_reads_as_an_option_is_passed_as_a_path(tmp_path):
    seen = []

    def fake_run(command, cwd, timeout, env=None):
        seen.append(command)
        return {"exit_code": 0, "output": ""}

    entry = {"glob": ["*"], "fix": ["fmt {file}"], "check": []}
    format_on_edit.run_project_commands(entry, "-rf.ts", tmp_path, [], fake_run)
    assert seen[0] in ("fmt ./-rf.ts", 'fmt ".\\-rf.ts"')


def test_paths_are_quoted_for_the_platform_shell():
    assert format_on_edit.quote_path("a & b.ts", windows=True) == '"a & b.ts"'
    assert format_on_edit.quote_path("100%.ts", windows=True) is None
    assert format_on_edit.quote_path("a & b.ts", windows=False) == "'a & b.ts'"


@pytest.mark.skipif(os.name != "nt", reason="cmd.exe and a .cmd shim exist on Windows only")
def test_a_cmd_shim_gets_a_path_with_a_space_and_an_ampersand_whole(tmp_path):
    """The proposal's first open point (docs/proposals/formatter-per-language.md, "What to
    settle"): npm's tools are .cmd shims that pass ``%*`` on, as this fake does; the hook
    starts them through cmd.exe with the path in double quotes."""
    shim = _write(tmp_path / "bin", "fmt.cmd", '@echo off\r\necho %*> "%~dp0args.txt"\r\n')
    root = tmp_path / "proj"
    target = _write(root, "src/a & b.ts", "x\n")
    entry = {"glob": ["*.ts"], "fix": [f'"{shim}" --write {{file}}'], "check": []}
    ran: list = []
    clean, _note = format_on_edit.run_project_commands(
        entry, os.path.relpath(target, root), root, ran
    )
    assert clean and ran[0]["exit_code"] == 0
    args = (shim.parent / "args.txt").read_text(encoding="utf-8").strip()
    assert args == '--write "src\\a & b.ts"'


def test_the_template_renders_an_installable_sdlc_yaml():
    values = {**_values(), "FORMATTERS": sdlc_init._formatters_yaml(detect.formatters(ROOT))}
    cfg = yamlish.loads(render_file(ROOT / "template" / "sdlc.yaml", values))
    assert "format_on_edit" not in cfg["hooks"]
    assert cfg["sandbox"] == {"allowed_domains": []} and cfg["commands"]["env"] == []


def _values() -> dict:
    sys.path.insert(0, str(ROOT / "tests"))
    from test_templates import VALUES  # noqa: PLC0415

    return dict(VALUES)
