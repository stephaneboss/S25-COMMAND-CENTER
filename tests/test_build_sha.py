"""cockpit _resolve_build_sha: git wins, unchecked trees are never attested clean."""
import ast
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

SRC = Path(__file__).resolve().parents[1] / "cockpit_lumiere.py"


def _load(run, root):
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_resolve_build_sha"]
    ns = {"os": os, "Path": Path, "__file__": str(root / "cockpit_lumiere.py"),
          "subprocess": SimpleNamespace(run=run, TimeoutExpired=subprocess.TimeoutExpired)}
    exec(compile(ast.Module(fn, []), str(SRC), "exec"), ns)
    return ns["_resolve_build_sha"]


def _run(status):
    def run(cmd, **kw):
        if cmd[1] == "log":
            return SimpleNamespace(returncode=0, stdout="abc123\n")
        return status(cmd, **kw)
    return run


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("APP_BUILD_SHA", "abc123")   # would falsely match if used


@pytest.fixture
def repo(tmp_path):
    (tmp_path / ".git").mkdir()
    return tmp_path


def test_clean_tree(repo):
    f = _load(_run(lambda c, **k: SimpleNamespace(returncode=0, stdout="")), repo)
    assert f() == ("abc123", "git")


def test_dirty_tree(repo):
    f = _load(_run(lambda c, **k: SimpleNamespace(returncode=0, stdout=" M agents/x.py\n")), repo)
    assert f() == ("abc123-dirty", "git")


def test_status_timeout_is_unverified_not_env(repo):
    def boom(c, **k):
        raise subprocess.TimeoutExpired(c, 5)
    assert _load(_run(boom), repo)() == ("abc123-unverified", "git")


def test_status_error_is_unverified(repo):
    f = _load(_run(lambda c, **k: SimpleNamespace(returncode=128, stdout="")), repo)
    assert f() == ("abc123-unverified", "git")


def test_repo_present_git_log_timeout_never_uses_env(repo):
    # APP_BUILD_SHA == expected SHA must NOT be attested when git cannot be read
    def boom(c, **k):
        raise subprocess.TimeoutExpired(c, 5)
    assert _load(boom, repo)() == ("unverified", "git")


def test_repo_present_git_log_error_never_uses_env(repo):
    f = _load(lambda c, **k: SimpleNamespace(returncode=128, stdout=""), repo)
    assert f() == ("unverified", "git")


def test_no_repo_uses_env(tmp_path):
    def never(c, **k):
        raise AssertionError("git must not be called without a repo")
    assert _load(never, tmp_path)() == ("abc123", "env")
