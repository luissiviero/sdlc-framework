"""plugin/ci/checkout_check.py (0.2.27): the verification of the project checkout between
the two steps of a job that share it across a model's session, run from a framework
checkout the runner made afresh. The fresh-context review of the 0.2.27 diff showed a
check of a session-controlled tree defeated four ways; what is left to verify is the
project checkout's remote, refspec and config, the fresh framework's commit against the
framework origin, and the default branch's pin after a fetch by URL."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ci import checkout_check

SCRIPT = Path(__file__).resolve().parents[1] / "plugin" / "ci" / "checkout_check.py"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def init(path: Path, branch: str = "main") -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", branch)
    git(path, "config", "user.email", "owner@example.com")
    git(path, "config", "user.name", "Owner")


def setting(tmp_path: Path):
    """The framework origin tagged v0.2.16 and cloned into work/framework; the project with
    a bare origin whose main pins 0.2.16."""
    fw_origin = tmp_path / "framework-origin"
    init(fw_origin)
    (fw_origin / "plugin.py").write_text("PIN = 1\n", encoding="utf-8")
    git(fw_origin, "add", ".")
    git(fw_origin, "commit", "-q", "-m", "0.2.16")
    git(fw_origin, "tag", "v0.2.16")
    (fw_origin / "plugin.py").write_text("PIN = 2\n", encoding="utf-8")
    git(fw_origin, "commit", "-q", "-am", "later")
    bare = tmp_path / "bare.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    work = tmp_path / "work"
    init(work)
    (work / "sdlc.yaml").write_text("plugin:\n  version: 0.2.16\n", encoding="utf-8")
    (work / ".gitignore").write_text("framework/\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "pin 0.2.16")
    git(work, "remote", "add", "origin", str(bare))
    git(work, "push", "-q", "-u", "origin", "main")
    framework = work / "framework"
    subprocess.run(
        ["git", "clone", "-q", "--branch", "v0.2.16", str(fw_origin), str(framework)], check=True
    )
    # a GitHub-hosted runner has no git identity (NOTES section 14): the tests that commit
    # in this clone set one, as init() does for the repositories it creates
    git(framework, "config", "user.email", "owner@example.com")
    git(framework, "config", "user.name", "Owner")
    return work, bare, fw_origin, framework


def verify(work: Path, bare: Path, fw_origin: Path, *extra: str, env=None):
    import os

    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(work), "--framework", "framework",
         "--pin-ref", "v0.2.16", "--origin", str(bare), "--framework-origin", str(fw_origin),
         "--default-branch", "main", *extra],
        capture_output=True, text=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", **(env or {})},
    )  # fmt: skip


def test_a_clean_checkout_at_the_pin_passes_and_the_default_branch_is_fetched_by_url(tmp_path):
    work, bare, fw_origin, framework = setting(tmp_path)
    # a session rewrote the remote-tracking ref to a commit with another pin
    git(work, "checkout", "-q", "-b", "planted")
    (work / "sdlc.yaml").write_text("plugin:\n  version: 9.9.9\n", encoding="utf-8")
    git(work, "commit", "-q", "-am", "planted pin")
    git(work, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(work, "checkout", "-q", "main")
    proc = verify(work, bare, fw_origin)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "verified=framework@v0.2.16"
    assert git(work, "show", "refs/remotes/origin/main:sdlc.yaml").endswith("0.2.16")


def test_a_tampered_framework_is_refused_against_the_framework_origin(tmp_path):
    """The tree is judged against what the framework's origin carries for the tag, never
    against the checkout's own tags (a session can move those) — and a fresh checkout by
    the runner precedes this check in the workflows anyway."""
    work, bare, fw_origin, framework = setting(tmp_path)
    (framework / "plugin.py").write_text("PIN = 'planted'\n", encoding="utf-8")
    proc = verify(work, bare, fw_origin)
    assert proc.returncode == 3 and "framework checkout is not clean: plugin.py" in proc.stderr
    git(framework, "checkout", "-q", "--", "plugin.py")
    git(framework, "commit", "-q", "--allow-empty", "-m", "moved")
    git(framework, "tag", "-f", "v0.2.16")  # the moved tag does not help
    proc = verify(work, bare, fw_origin)
    assert proc.returncode == 3 and "not at v0.2.16 as" in proc.stderr
    git(framework, "checkout", "-q", "HEAD~1")
    git(framework, "update-index", "--skip-worktree", "plugin.py")
    proc = verify(work, bare, fw_origin)
    assert proc.returncode == 3 and "skip-worktree" in proc.stderr


def test_a_redirected_or_rewired_origin_is_refused(tmp_path):
    """The review of the 0.2.27 diff, H3: `url.<x>.insteadOf` redirects a fetch whatever
    the remote's URL says, so the config keys that redirect a fetch or run a command are
    refused, in the local and the global config."""
    work, bare, fw_origin, framework = setting(tmp_path)
    git(work, "config", "remote.origin.fetch", "+refs/heads/planted:refs/remotes/origin/main")
    proc = verify(work, bare, fw_origin)
    assert proc.returncode == 3 and "remote.origin.fetch is" in proc.stderr
    git(work, "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
    git(work, "config", "remote.origin.url", str(tmp_path / "elsewhere.git"))
    proc = verify(work, bare, fw_origin)
    assert proc.returncode == 3 and "remote.origin.url is" in proc.stderr
    git(work, "config", "remote.origin.url", str(bare))
    planted = tmp_path / "planted.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(planted)], check=True)
    git(work, "config", f"url.{planted}.insteadOf", str(bare))
    proc = verify(work, bare, fw_origin)
    assert proc.returncode == 3 and "insteadof" in proc.stderr and "local carries" in proc.stderr
    git(work, "config", "--unset", f"url.{planted}.insteadOf")
    for key in ("core.hooksPath", "core.fsmonitor", "remote.origin.pushurl", "include.path"):
        git(work, "config", key, "/tmp/x")
        proc = verify(work, bare, fw_origin)
        assert proc.returncode == 3 and key.lower() in proc.stderr, key
        git(work, "config", "--unset", key)
    global_cfg = tmp_path / "gitconfig"
    # forward slashes: a backslash escapes inside a gitconfig file, and a Windows path
    # written as is makes git refuse the whole file (the first Windows run, 0.2.28)
    global_cfg.write_text(
        f'[url "{planted.as_posix()}"]\n\tinsteadOf = {bare.as_posix()}\n', encoding="utf-8"
    )
    proc = verify(work, bare, fw_origin, env={"GIT_CONFIG_GLOBAL": str(global_cfg)})
    assert proc.returncode == 3 and "global carries" in proc.stderr
    assert verify(work, bare, fw_origin).returncode == 0


def test_a_pin_the_default_branch_no_longer_carries_is_refused(tmp_path, monkeypatch):
    work, bare, fw_origin, framework = setting(tmp_path)
    git(work, "checkout", "-q", "-b", "bump")
    (work / "sdlc.yaml").write_text("plugin:\n  version: 9.9.9\n", encoding="utf-8")
    git(work, "commit", "-q", "-am", "bump")
    git(work, "push", "-q", "origin", "bump:main", "--force")
    git(work, "checkout", "-q", "main")
    proc = verify(work, bare, fw_origin)
    assert proc.returncode == 3 and "the default branch's pin is v9.9.9" in proc.stderr
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(work), "--pin-ref=-x"],
        capture_output=True, text=True,
    )  # fmt: skip
    assert proc.returncode == 3 and "--pin-ref" in proc.stderr
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "no-such-gitconfig"))
    assert checkout_check.config_problems(work) == []
    # the global scope judges the redirect keys only: the runner image's own config (a
    # signing program, a credential helper) is not this framework's to refuse
    (tmp_path / "gitconfig").write_text(
        '[gpg "ssh"]\n\tprogram = /usr/bin/ssh-keygen\n[credential]\n\thelper = store\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    assert checkout_check.config_problems(work) == []
