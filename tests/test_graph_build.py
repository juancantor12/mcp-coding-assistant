"""Tests for core.graph.GraphService.build."""
from __future__ import annotations


def test_graph_build_schema(graph_service, project_name, project_root, sample_python_file):
    graph = graph_service.build(project_name)

    assert graph["schema_version"]
    assert graph["project"] == project_name
    assert graph["code_hash"]
    assert graph["nodes"]
    assert graph["edges"]
    assert any(entry["path"] == "sample.py" for entry in graph["files"])


def test_graph_build_hash_determinism(graph_service, project_name, project_root, sample_python_file):
    first = graph_service.compute_code_hash(project_name)
    second = graph_service.compute_code_hash(project_name)
    assert first == second

    (project_root / "note.txt").write_text("x", encoding="utf-8")
    changed = graph_service.compute_code_hash(project_name)
    assert changed != first
