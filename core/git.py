"""Git command helpers."""
from __future__ import annotations

import subprocess
from typing import Sequence


class GitService:
    def __init__(self, repo_root: str) -> None:
        self._repo_root = repo_root

    def _run(self, args: Sequence[str]) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self._repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            raise RuntimeError(error or output or "Git command failed")
        return output

    def status(self) -> str:
        return self._run(["status", "-sb"])

    def add_all(self) -> str:
        return self._run(["add", "."])

    def current_branch(self) -> str:
        return self._run(["rev-parse", "--abbrev-ref", "HEAD"])

    def commit(self, message: str) -> str:
        return self._run(["commit", "-m", message])

    def push(self) -> str:
        branch = self.current_branch()
        return self._run(["push", "origin", branch])
