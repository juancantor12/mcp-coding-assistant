"""Tests for core.graph.GraphService.save_proposal."""
from __future__ import annotations

import os

import pytest


def test_graph_proposal_rejects_hash_mismatch(graph_service, project_name, sample_python_file):
    graph_service.build(project_name)
    proposal = {
        "schema_version": "0.1.0",
        "project": project_name,
        "base_code_hash": "deadbeef",
        "created_at": "2025-01-01T00:00:00Z",
        "operations": [],
    }
    with pytest.raises(ValueError):
        graph_service.save_proposal(project_name, proposal)


def test_graph_proposal_accepts_valid(graph_service, project_name, sample_python_file):
    graph = graph_service.build(project_name)
    proposal = {
        "schema_version": "0.1.0",
        "project": project_name,
        "base_code_hash": graph["code_hash"],
        "created_at": "2025-01-01T00:00:00Z",
        "operations": [
            {
                "op": "add_node",
                "node": {
                    "id": "n900",
                    "kind": "function",
                    "name": "extra",
                    "file": "sample.py",
                    "range": {"start_line": 1, "end_line": 1},
                    "extra": {},
                },
            }
        ],
    }
    result = graph_service.save_proposal(project_name, proposal)
    assert result["saved"] is True
    assert os.path.exists(result["path"])
    assert result["proposal"]["created_at"]
