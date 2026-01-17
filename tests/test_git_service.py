"""Tests for core.git.GitService."""
from __future__ import annotations

from unittest.mock import Mock

from core.git import GitService


def _fake_run(args, cwd=None, check=None, stdout=None, stderr=None, text=None):
    mock = Mock()
    mock.returncode = 0
    if args[1:3] == ["rev-parse", "--abbrev-ref"]:
        mock.stdout = "main"
    elif args[1:3] == ["status", "-sb"]:
        mock.stdout = "## main"
    else:
        mock.stdout = ""
    mock.stderr = ""
    return mock


def test_git_service_calls(monkeypatch, tmp_path):
    monkeypatch.setattr("core.git.subprocess.run", _fake_run)

    git = GitService(str(tmp_path))
    assert git.current_branch() == "main"
    assert git.status() == "## main"
    assert git.add_all() == ""
    assert git.commit("msg") == ""
    assert git.push() == ""
