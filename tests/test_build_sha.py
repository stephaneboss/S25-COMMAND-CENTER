"""cockpit _resolve_build_sha: git wins, unchecked trees are never attested clean."""
import ast
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

SRC = Path(__file__).resolve().parents[1] / "cockpit_lumiere.py"


def _load(run):
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_resolve_build_sha"]
    ns = {"os": os, "Path": Path, "__file__": str(SRC),
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


def test_clean_tree():
    f = _load(_run(lambda c, **k: SimpleNamespace(returncode=0, stdout="")))
    assert f() == ("abc123", "git")


def test_dirty_tree():
    f = _load(_run(lambda c, **k: SimpleNamespace(returncode=0, stdout=" M agents/x.py\n")))
    assert f() == ("abc123-dirty", "git")


def test_status_timeout_is_unverified_not_env():
    def boom(c, **k):
        raise subprocess.TimeoutExpired(c, 5)
    assert _load(_run(boom))() == ("abc123-unverified", "git")


def test_status_error_is_unverified():
    f = _load(_run(lambda c, **k: SimpleNamespace(returncode=128, stdout="")))
    assert f() == ("abc123-unverified", "git")


def test_no_git_falls_back_to_env():
    def nogit(c, **k):
        raise FileNotFoundError("git")
    assert _load(nogit)() == ("abc123", "env")
