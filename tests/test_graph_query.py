"""Tests for core.graph.GraphService.query."""
from __future__ import annotations


def test_graph_query_filters(graph_service, project_name, sample_python_file):
    graph_service.build(project_name)

    result = graph_service.query(project_name, "Greeter")
    assert result["match_count"] >= 1
    assert any(node["kind"] == "class" for node in result["matches"])

    result = graph_service.query(project_name, "sample.py", kind="function")
    assert any(node["kind"] == "function" for node in result["matches"])
