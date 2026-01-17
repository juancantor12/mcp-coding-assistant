"""Tests for core.interpreter.GraphChangeApplier delete operations."""
from __future__ import annotations

import json


def test_interpreter_delete_node(graph_service, interpreter, project_name, project_root):
    (project_root / "delete.py").write_text(
        "\n".join(
            [
                "class RemoveMe:",
                "    pass",
                "",
                "def keep_me():",
                "    pass",
                "",
            ]
        ),
        encoding="utf-8",
    )

    graph = graph_service.build(project_name)
    remove_node = next(node for node in graph["nodes"] if node["name"] == "RemoveMe")
    keep_node = next(node for node in graph["nodes"] if node["name"] == "keep_me")
    original_keep_start = keep_node["range"]["start_line"]

    proposal = {
        "schema_version": "0.1.0",
        "project": project_name,
        "base_code_hash": graph["code_hash"],
        "created_at": "2025-01-01T00:00:00Z",
        "operations": [
            {"op": "delete_node", "node_id": remove_node["id"]},
        ],
    }

    proposal_path = project_root / "proposal_delete.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    result = interpreter.apply_proposal(project_name, str(proposal_path))
    assert result["nodes_deleted"] == 1

    content = (project_root / "delete.py").read_text(encoding="utf-8")
    assert "RemoveMe" not in content
    assert "keep_me" in content

    updated_graph = graph_service.build(project_name)
    updated_keep = next(node for node in updated_graph["nodes"] if node["name"] == "keep_me")
    assert updated_keep["range"]["start_line"] < original_keep_start
