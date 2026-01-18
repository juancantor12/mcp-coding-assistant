"""Tests for core.config.AppConfig."""
from __future__ import annotations

import os
from types import SimpleNamespace

from core.config import AppConfig
from core.registry import ProjectRegistry


def test_app_config_from_globals_monkeypatched(monkeypatch) -> None:
    fake_globals = SimpleNamespace(
        BASE_PATH="C:/tmp/apps",
        PROJECTS={"a", "b"},
        ALLOWED_EXTENSIONS={"py", "txt"},
    )
    monkeypatch.setitem(
        __import__("sys").modules, "mcp-coding-assistant.globals", fake_globals
    )
    monkeypatch.setattr(ProjectRegistry, "load", lambda self: set())
    config = AppConfig.from_globals()

    assert os.path.isabs(config.base_path)
    assert config.projects == {"a", "b"}
    assert config.allowed_extensions == {"py", "txt"}
