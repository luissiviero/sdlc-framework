"""Static tests for the five policy skills of build guide step 20: frontmatter with a trigger
description, a Source section naming the article pages (and "no owner source yet"), rules,
a Check section calling the skill's own deterministic script, and the scripts running against
the initialised fixture. Whether the model triggers a skill is a live check, not a layer-1
test."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from gate import preflight

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugin" / "skills"
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
NAMES = preflight.POLICY_SKILLS


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert m, path
    fm = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm, m.group(2)


@pytest.mark.parametrize("name", NAMES)
def test_policy_skill_shape(name):
    path = SKILLS / name / "SKILL.md"
    fm, body = frontmatter(path)
    assert fm["name"] == name
    assert (
        fm["description"].startswith(("The organization's", "What "))
        and "Use " in fm["description"]
    )
    assert '("' in fm["description"]  # example phrasings that trigger it, like intent-template
    for heading in ("## Source", "## Check"):
        assert heading in body, heading
    source = body.split("## Source", 1)[1].split("## ", 1)[0]
    assert re.search(r"p\.\d+", source), "cites article pages"
    assert "no owner source yet" in source
    assert f".claude/skills/{name}/SKILL.md" in source  # project override
    check = body.split("## Check", 1)[1]
    call = f'python "${{CLAUDE_PLUGIN_ROOT}}/plugin/skills/{name}/check.py"'
    assert call in check and (SKILLS / name / "check.py").is_file()
    assert "```" in check and "## " in check.split("```")[3]  # example output block
    assert "advisory" in check and "p.22" in check


def test_skill_names_match_preflight_list():
    assert sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file()) == sorted(
        [*NAMES, "intent-template", "spec-template", "plan-template"]
    )


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp("proj") / "proj"
    shutil.copytree(FIXTURE, root)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=o@x", "-c", "user.name=o", "add", "."], cwd=root, check=True
    )
    subprocess.run(
        ["git", "-c", "user.email=o@x", "-c", "user.name=o", "commit", "-q", "-m", "fixture"],
        cwd=root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(INIT), "--root", str(root)], check=True, capture_output=True
    )
    return root


def run_check(name: str, root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILLS / name / "check.py"), "--root", str(root), *extra],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_preflight_is_satisfied_by_the_plugins_own_skills(project):
    report = preflight.run_preflight(project, ROOT)
    skills = next(ch for ch in report["checks"] if ch["name"] == "policy_skills")
    assert skills["ok"] and set(skills["details"]["found"].values()) == {"plugin"}
    assert report["allow"] is True, report["reasons"]


def test_coding_standards_check_runs_lint_and_reports(project):
    proc = run_check("coding-standards", project)
    assert "## coding-standards check" in proc.stdout
    assert "lint target `python -m ruff check .` passed" in proc.stdout
    (project / "sample_pkg" / "big.py").write_text("x = 1\n" * 501, encoding="utf-8")
    proc = run_check("coding-standards", project)
    assert proc.returncode == 1 and "big.py is 501 lines" in proc.stdout
    assert "no test file changed" in proc.stdout
    (project / "sample_pkg" / "big.py").unlink()


def test_security_baseline_check_finds_secrets_and_dangerous_calls(project):
    proc = run_check("security-baseline", project)
    assert proc.returncode == 0, proc.stdout  # the initialised fixture is clean
    bad = project / "sample_pkg" / "bad.py"
    bad.write_text(
        'import subprocess\nsubprocess.run("ls", shell=True)\n'
        'AWS_SECRET_ACCESS_KEY = "AKIAABCDEFGHIJKLMNOP"\n',
        encoding="utf-8",
    )
    proc = run_check("security-baseline", project)
    assert proc.returncode == 1
    assert "bad.py:2: subprocess with shell=True" in proc.stdout
    assert "possible secret in added lines" in proc.stdout
    bad.unlink()


def test_ux_check_ignores_non_ui_and_wants_screenshots(project):
    proc = run_check("ux-conventions", project)
    assert proc.returncode == 0 and "do not apply" in proc.stdout
    page = project / "templates" / "index.html"
    page.parent.mkdir(exist_ok=True)
    page.write_text("<h1>Welcome to the portal now</h1>\n", encoding="utf-8")
    proc = run_check("ux-conventions", project, "--id", "0000")
    assert proc.returncode == 1
    assert "holds no screenshot" in proc.stdout and "visible copy hard-coded" in proc.stdout
    (project / "changes" / "0000-sdlc-init" / "evidence" / "home.png").write_bytes(b"\x89PNG")
    proc = run_check("ux-conventions", project, "--id", "0000")
    assert "holds no screenshot" not in proc.stdout
    shutil.rmtree(page.parent)


def test_data_check_flags_migrations_and_pii_in_logs(project):
    mig = project / "migrations" / "0001_add_ssn.sql"
    mig.parent.mkdir(exist_ok=True)
    mig.write_text("ALTER TABLE users ADD ssn TEXT;\n", encoding="utf-8")
    src = project / "sample_pkg" / "audit.py"
    src.write_text(
        "import logging\nlogging.info('user %s', user.ssn)\nphone_number = 1\n", encoding="utf-8"
    )
    proc = run_check("data-conventions", project)
    assert proc.returncode == 1
    assert "migrations/0001_add_ssn.sql: schema or migration file" in proc.stdout
    assert "audit.py:2: personal-data field in a logging statement" in proc.stdout
    assert "audit.py:3: new personal-data identifier 'phone_number'" in proc.stdout
    shutil.rmtree(mig.parent)
    src.unlink()


def test_definition_of_done_check_is_the_gate_dry_run(project):
    proc = run_check("definition-of-done", project, "--id", "0000", "--phase", "a")
    assert "## definition-of-done check (gate dry run)" in proc.stdout
    assert "- [x] artifacts" in proc.stdout and "verdict if run now" in proc.stdout
    assert not (project / "changes" / "0000-sdlc-init" / "evidence" / "gate-a.json").exists()
    proc = run_check("definition-of-done", project, "--id", "0042", "--phase", "a")
    assert proc.returncode == 1 and "gate could not run" in proc.stdout
