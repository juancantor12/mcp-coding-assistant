"""Tests for core.projects.ProjectManager."""
from __future__ import annotations

import os

import pytest


def test_project_manager_make_rename_scaffolding(project_manager, project_root, project_name):
    project_manager.make_dir(project_name, "a/b")
    assert (project_root / "a" / "b").is_dir()

    project_manager.rename_dir(project_name, "a/b", "a/c")
    assert (project_root / "a" / "c").is_dir()

    (project_root / "a" / "c" / "file.txt").write_text("ok", encoding="utf-8")
    scaffolding = project_manager.scaffolding(project_name)
    assert scaffolding["folder_name"] == project_name

    def find_file(node, filename):
        if filename in node.get("files", []):
            return True
        for child in node.get("subfolders", []):
            if find_file(child, filename):
                return True
        return False

    assert find_file(scaffolding, "file.txt")


def test_project_manager_inverted_index(project_manager, project_root, project_name):
    (project_root / "dir").mkdir(parents=True, exist_ok=True)
    (project_root / "dir" / "alpha.py").write_text("x=1", encoding="utf-8")
    index = project_manager.inverted_index(project_name)

    assert "alpha" in index
    assert "py" in index
    assert any(os.path.join("dir", "alpha.py") in path for path in index["py"])


def test_project_manager_invalid_project(project_manager):
    with pytest.raises(ValueError):
        project_manager.make_dir("invalid", "x")
