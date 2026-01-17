"""Tests for core.files.FileService."""
from __future__ import annotations

import pytest


def test_file_service_save_load_remove(file_service, project_root, project_name):
    ok = file_service.save(project_name, "", "notes", "txt", "hello")
    assert ok
    assert (project_root / "notes.txt").is_file()
    assert file_service.load(project_name, "notes.txt") == "hello"
    assert file_service.remove(project_name, "notes.txt") is True


def test_file_service_execute(file_service, project_root, project_name):
    script = "print('hi')"
    file_service.save(project_name, "", "run_me", "py", script)
    result = file_service.execute(project_name, "run_me.py", [])
    assert b"hi" in result["outs"]


def test_file_service_invalid_project(file_service):
    with pytest.raises(ValueError):
        file_service.load("invalid", "x.txt")


def test_file_service_invalid_extension(file_service, project_name):
    with pytest.raises(ValueError):
        file_service.save(project_name, "", "bad", "exe", "nope")
