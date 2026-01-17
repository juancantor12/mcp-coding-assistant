"""Tests for core.interpreter.GraphChangeApplier add operations."""
from __future__ import annotations

import json


def test_interpreter_add_nodes(
    graph_service, interpreter, project_name, project_root, sample_python_file
):
    graph = graph_service.build(project_name)
    code_hash = graph["code_hash"]
    class_node = next(node for node in graph["nodes"] if node["kind"] == "class")

    proposal = {
        "schema_version": "0.1.0",
        "project": project_name,
        "base_code_hash": code_hash,
        "created_at": "2025-01-01T00:00:00Z",
        "operations": [
            {
                "op": "add_node",
                "node": {
                    "id": "n1000",
                    "kind": "function",
                    "name": "extra_fn",
                    "file": "sample.py",
                    "range": {"start_line": 1, "end_line": 1},
                    "extra": {},
                },
            },
            {
                "op": "add_node",
                "node": {
                    "id": "n1001",
                    "kind": "method",
                    "name": "new_method",
                    "file": "sample.py",
                    "range": {"start_line": 1, "end_line": 1},
                    "extra": {},
                },
            },
            {
                "op": "add_edge",
                "edge": {"from": class_node["id"], "to": "n1001", "kind": "belongs_to"},
            },
            {
                "op": "add_node",
                "node": {
                    "id": "n1002",
                    "kind": "import",
                    "name": "math",
                    "file": "sample.py",
                    "range": {"start_line": 1, "end_line": 1},
                    "extra": {},
                },
            },
        ],
    }

    proposal_path = project_root / "proposal.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    result = interpreter.apply_proposal(project_name, str(proposal_path))
    assert result["applied"] is True

    content = (project_root / "sample.py").read_text(encoding="utf-8")
    assert "def extra_fn()" in content
    assert "def new_method(self)" in content
    assert "import math" in content
