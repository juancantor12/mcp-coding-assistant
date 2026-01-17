"""Tests for core.interpreter.GraphChangeApplier update operations."""
from __future__ import annotations

import json


def test_interpreter_update_node(graph_service, interpreter, project_name, project_root):
    (project_root / "rename.py").write_text(
        "\n".join(
            [
                "class OldName:",
                "    pass",
                "",
                "def old_func():",
                "    pass",
                "",
            ]
        ),
        encoding="utf-8",
    )

    graph = graph_service.build(project_name)
    class_node = next(node for node in graph["nodes"] if node["name"] == "OldName")
    func_node = next(node for node in graph["nodes"] if node["name"] == "old_func")

    proposal = {
        "schema_version": "0.1.0",
        "project": project_name,
        "base_code_hash": graph["code_hash"],
        "created_at": "2025-01-01T00:00:00Z",
        "operations": [
            {
                "op": "update_node",
                "node_id": class_node["id"],
                "patch": {"name": "NewName"},
            },
            {
                "op": "update_node",
                "node_id": func_node["id"],
                "patch": {"name": "new_func"},
            },
        ],
    }

    proposal_path = project_root / "proposal_update.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    result = interpreter.apply_proposal(project_name, str(proposal_path))
    assert result["nodes_updated"] == 2

    content = (project_root / "rename.py").read_text(encoding="utf-8")
    assert "class NewName" in content
    assert "def new_func" in content
