"""Tests for MCP tool wrappers in server.py."""
from __future__ import annotations

import json

import server


class FakeGit:
    def __init__(self) -> None:
        self.calls = []

    def status(self) -> str:
        self.calls.append("status")
        return "ok"

    def add_all(self) -> str:
        self.calls.append("add_all")
        return "added"

    def commit(self, message: str) -> str:
        self.calls.append(("commit", message))
        return "committed"

    def push(self) -> str:
        self.calls.append("push")
        return "pushed"


def test_mcp_wrappers(monkeypatch, project_name, graph_service, interpreter, project_root):
    monkeypatch.setattr(server, "graphs", graph_service)
    monkeypatch.setattr(server, "interpreter", interpreter)

    fake_git = FakeGit()
    monkeypatch.setattr(server, "git", fake_git)

    (project_root / "mcp.py").write_text("def test():\n    pass\n", encoding="utf-8")
    graph = server.build_code_graph(project_name)
    assert graph["project"] == project_name

    result = server.query_code_graph(project_name, "test")
    assert result["match_count"] >= 1

    proposal = {
        "schema_version": "0.1.0",
        "project": project_name,
        "base_code_hash": graph["code_hash"],
        "created_at": "2025-01-01T00:00:00Z",
        "operations": [],
    }
    save = server.save_graph_proposal(project_name, proposal)
    assert save["saved"] is True

    proposal_path = project_root / "proposal_apply.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    apply_result = server.apply_graph_proposal(project_name, str(proposal_path))
    assert apply_result["applied"] is True

    assert server.git_status() == "ok"
    assert server.git_add_all() == "added"
    assert server.git_commit("msg") == "committed"
    assert server.git_push() == "pushed"
