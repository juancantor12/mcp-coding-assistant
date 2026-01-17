"""Configuration models for services."""
from __future__ import annotations

import os
from typing import Set

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    base_path: str = Field(..., description="Absolute path to apps root")
    projects: Set[str] = Field(default_factory=set, description="Allowed project names")
    allowed_extensions: Set[str] = Field(
        default_factory=set, description="Allowed file extensions"
    )

    @classmethod
    def from_globals(cls) -> "AppConfig":
        globals_mod = __import__("mcp-coding-assistant.globals", fromlist=[None])
        base_path = os.path.abspath(globals_mod.BASE_PATH)
        return cls(
            base_path=base_path,
            projects=set(globals_mod.PROJECTS),
            allowed_extensions=set(globals_mod.ALLOWED_EXTENSIONS),
        )
