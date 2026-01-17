"""Code graph generation and querying."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Iterable

from pydantic import BaseModel, Field

from core.config import AppConfig


class Range(BaseModel):
    start_line: int | None
    end_line: int | None


class Node(BaseModel):
    id: str
    kind: str
    name: str
    file: str
    range: Range
    extra: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    kind: str
    extra: dict[str, Any] = Field(default_factory=dict)


class Graph(BaseModel):
    schema_version: str
    project: str
    generated_at: str
    root: str
    nodes: list[Node]
    edges: list[Edge]
    files: list[dict[str, Any]]
    kinds: dict[str, list[str]]
    extensions: dict[str, Any]
    code_hash: str


class GraphChangeOperation(BaseModel):
    op: str
    node: dict[str, Any] | None = None
    node_id: str | None = None
    edge: dict[str, Any] | None = None
    patch: dict[str, Any] | None = None


class GraphProposal(BaseModel):
    schema_version: str
    project: str
    base_code_hash: str
    created_at: str
    rationale: str = ""
    operations: list[GraphChangeOperation]


def _model_dump(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(by_alias=True)
    return model.dict(by_alias=True)


class GraphService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def _repo_root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _graph_dir(self) -> str:
        path = os.path.join(self._repo_root(), "graphs")
        os.makedirs(path, exist_ok=True)
        return path

    def _graph_path(self, project: str) -> str:
        return os.path.join(self._graph_dir(), f"{project}.codegraph.json")

    def _proposal_dir(self, project: str) -> str:
        path = os.path.join(self._graph_dir(), "proposals", project)
        os.makedirs(path, exist_ok=True)
        return path

    def _project_root(self, project: str) -> str:
        return os.path.join(self._config.base_path, project)

    def _iter_code_files(self, project: str) -> Iterable[tuple[str, str]]:
        root = self._project_root(project)
        extensions = {ext.lower().lstrip(".") for ext in self._config.allowed_extensions}
        for current_root, _, filenames in os.walk(root):
            for filename in filenames:
                ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                if extensions and ext not in extensions:
                    continue
                full_path = os.path.join(current_root, filename)
                rel_path = os.path.relpath(full_path, root).replace("\\", "/")
                yield full_path, rel_path

    def compute_code_hash(self, project: str) -> str:
        """Computes a deterministic hash for the project files."""
        if project not in self._config.projects:
            raise ValueError("Invalid project")
        hasher = hashlib.sha256()
        files = sorted(self._iter_code_files(project), key=lambda item: item[1])
        for full_path, rel_path in files:
            hasher.update(rel_path.encode("utf-8"))
            with open(full_path, "rb") as handle:
                hasher.update(handle.read())
        return hasher.hexdigest()

    def build(self, project: str) -> dict[str, Any]:
        """Builds a code graph for a project and writes it to disk."""
        if project not in self._config.projects:
            raise ValueError("Invalid project")

        nodes: list[Node] = []
        edges: list[Edge] = []
        files: list[dict[str, Any]] = []
        node_id = 0

        def next_id() -> str:
            nonlocal node_id
            node_id += 1
            return f"n{node_id}"

        def add_node(
            kind: str,
            name: str,
            file_rel: str,
            start_line: int | None,
            end_line: int | None,
            extra: dict[str, Any] | None = None,
        ) -> str:
            nid = next_id()
            nodes.append(
                Node(
                    id=nid,
                    kind=kind,
                    name=name,
                    file=file_rel,
                    range=Range(start_line=start_line, end_line=end_line),
                    extra=extra or {},
                )
            )
            return nid

        def add_edge(
            from_id: str,
            to_id: str,
            kind: str,
            extra: dict[str, Any] | None = None,
        ) -> None:
            edges.append(
                Edge(
                    from_id=from_id,
                    to_id=to_id,
                    kind=kind,
                    extra=extra or {},
                )
            )

        project_root = self._project_root(project)
        for full_path, file_rel in self._iter_code_files(project):
            if not file_rel.endswith(".py"):
                continue
            files.append({"path": file_rel, "language": "python"})
            try:
                with open(full_path, "r", encoding="UTF-8") as handle:
                    source = handle.read()
                tree = ast.parse(source, filename=full_path)
            except (SyntaxError, OSError):
                continue

                module_id = add_node(
                    "module",
                    os.path.splitext(filename)[0],
                    file_rel,
                    1,
                    getattr(tree, "end_lineno", None),
                    extra={},
                )

                class_stack: list[str] = []

                class Visitor(ast.NodeVisitor):
                    def visit_ClassDef(self, node: ast.ClassDef) -> None:
                        bases = []
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                bases.append(base.id)
                            elif isinstance(base, ast.Attribute):
                                bases.append(base.attr)
                        class_id = add_node(
                            "class",
                            node.name,
                            file_rel,
                            node.lineno,
                            getattr(node, "end_lineno", node.lineno),
                            extra={"bases": bases},
                        )
                        add_edge(module_id, class_id, "defines")
                        if class_stack:
                            add_edge(class_stack[-1], class_id, "defines")
                        class_stack.append(class_id)
                        self.generic_visit(node)
                        class_stack.pop()

                    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                        self._handle_function(node)

                    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                        self._handle_function(node)

                    def _handle_function(self, node: ast.AST) -> None:
                        name = getattr(node, "name", "<lambda>")
                        kind = "method" if class_stack else "function"
                        func_id = add_node(
                            kind,
                            name,
                            file_rel,
                            getattr(node, "lineno", None),
                            getattr(node, "end_lineno", None),
                            extra={},
                        )
                        add_edge(module_id, func_id, "defines")
                        if class_stack:
                            add_edge(class_stack[-1], func_id, "belongs_to")
                        self.generic_visit(node)

                    def visit_Import(self, node: ast.Import) -> None:
                        for alias in node.names:
                            imp_id = add_node(
                                "import",
                                alias.name,
                                file_rel,
                                node.lineno,
                                getattr(node, "end_lineno", node.lineno),
                                extra={"asname": alias.asname},
                            )
                            add_edge(module_id, imp_id, "imports")
                        self.generic_visit(node)

                    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                        module = node.module or ""
                        for alias in node.names:
                            name = f"{module}.{alias.name}" if module else alias.name
                            imp_id = add_node(
                                "import",
                                name,
                                file_rel,
                                node.lineno,
                                getattr(node, "end_lineno", node.lineno),
                                extra={"level": node.level, "asname": alias.asname},
                            )
                            add_edge(module_id, imp_id, "imports")
                        self.generic_visit(node)

                Visitor().visit(tree)

        graph = Graph(
            schema_version="0.1.0",
            project=project,
            generated_at=datetime.now(timezone.utc).isoformat(),
            root=project_root.replace("\\", "/"),
            nodes=nodes,
            edges=edges,
            files=files,
            kinds={
                "node": ["module", "class", "function", "method", "import"],
                "edge": ["defines", "belongs_to", "imports"],
            },
            extensions={},
            code_hash=self.compute_code_hash(project),
        )

        graph_dict = _model_dump(graph)
        with open(self._graph_path(project), "w", encoding="UTF-8") as handle:
            json.dump(graph_dict, handle, indent=2, ensure_ascii=True)

        return graph_dict

    def query(self, project: str, term: str, kind: str | None = None) -> dict[str, Any]:
        """Query nodes by name/file and return matching nodes with related edges."""
        if project not in self._config.projects:
            raise ValueError("Invalid project")
        graph_path = self._graph_path(project)
        if not os.path.exists(graph_path):
            raise ValueError("Graph not found, build it first")

        with open(graph_path, "r", encoding="UTF-8") as handle:
            graph = json.load(handle)

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        term_lower = term.lower()
        matches = [
            node
            for node in nodes
            if (
                (not kind or node.get("kind") == kind)
                and (
                    term_lower in str(node.get("name", "")).lower()
                    or term_lower in str(node.get("file", "")).lower()
                )
            )
        ]
        matched_ids = {node["id"] for node in matches}
        related_edges = [
            edge
            for edge in edges
            if edge.get("from") in matched_ids or edge.get("to") in matched_ids
        ]

        return {
            "matches": matches,
            "related_edges": related_edges,
            "match_count": len(matches),
        }

    def save_proposal(self, project: str, proposal: dict[str, Any]) -> dict[str, Any]:
        """Validates and stores a graph change proposal."""
        if project not in self._config.projects:
            raise ValueError("Invalid project")

        current_hash = self.compute_code_hash(project)
        proposal_copy = dict(proposal)
        proposal_copy.setdefault("created_at", datetime.now(timezone.utc).isoformat())

        proposal_model = GraphProposal(**proposal_copy)
        if proposal_model.project != project:
            raise ValueError("Proposal project mismatch")
        if proposal_model.base_code_hash != current_hash:
            raise ValueError("Code hash mismatch")

        graph_path = self._graph_path(project)
        if not os.path.exists(graph_path):
            raise ValueError("Graph not found, build it first")
        with open(graph_path, "r", encoding="UTF-8") as handle:
            graph = json.load(handle)

        node_ids = {node["id"] for node in graph.get("nodes", [])}
        edge_keys = {
            (edge.get("from"), edge.get("to"), edge.get("kind"))
            for edge in graph.get("edges", [])
        }
        allowed_node_kinds = set(graph.get("kinds", {}).get("node", []))
        allowed_edge_kinds = set(graph.get("kinds", {}).get("edge", []))

        added_nodes: set[str] = set()
        deleted_nodes: set[str] = set()
        added_edges: set[tuple[str, str, str]] = set()
        deleted_edges: set[tuple[str, str, str]] = set()

        def node_exists(node_id: str) -> bool:
            if node_id in deleted_nodes:
                return False
            return node_id in node_ids or node_id in added_nodes

        for op in proposal_model.operations:
            if op.op == "add_node":
                if not op.node:
                    raise ValueError("add_node requires node")
                node = op.node
                node_id = node.get("id")
                if not node_id:
                    raise ValueError("add_node requires node.id")
                if node_id in node_ids or node_id in added_nodes:
                    raise ValueError(f"Node already exists: {node_id}")
                kind = node.get("kind")
                if allowed_node_kinds and kind not in allowed_node_kinds:
                    raise ValueError(f"Invalid node kind: {kind}")
                if not node.get("name") or not node.get("file") or not node.get("range"):
                    raise ValueError("add_node requires name, file, range")
                added_nodes.add(node_id)
            elif op.op == "update_node":
                if not op.node_id or not op.patch:
                    raise ValueError("update_node requires node_id and patch")
                if not node_exists(op.node_id):
                    raise ValueError(f"Node not found: {op.node_id}")
                if "kind" in op.patch and allowed_node_kinds:
                    if op.patch["kind"] not in allowed_node_kinds:
                        raise ValueError(f"Invalid node kind: {op.patch['kind']}")
            elif op.op == "delete_node":
                if not op.node_id:
                    raise ValueError("delete_node requires node_id")
                if not node_exists(op.node_id):
                    raise ValueError(f"Node not found: {op.node_id}")
                deleted_nodes.add(op.node_id)
            elif op.op == "add_edge":
                if not op.edge:
                    raise ValueError("add_edge requires edge")
                edge = op.edge
                from_id = edge.get("from")
                to_id = edge.get("to")
                kind = edge.get("kind")
                if not from_id or not to_id or not kind:
                    raise ValueError("add_edge requires from, to, kind")
                if allowed_edge_kinds and kind not in allowed_edge_kinds:
                    raise ValueError(f"Invalid edge kind: {kind}")
                if not node_exists(from_id) or not node_exists(to_id):
                    raise ValueError("add_edge references unknown node")
                key = (from_id, to_id, kind)
                if key in edge_keys or key in added_edges:
                    raise ValueError("Edge already exists")
                added_edges.add(key)
            elif op.op == "delete_edge":
                if not op.edge:
                    raise ValueError("delete_edge requires edge")
                edge = op.edge
                from_id = edge.get("from")
                to_id = edge.get("to")
                kind = edge.get("kind")
                key = (from_id, to_id, kind)
                if key not in edge_keys and key not in added_edges:
                    raise ValueError("Edge not found")
                deleted_edges.add(key)
            else:
                raise ValueError(f"Unknown operation: {op.op}")

        proposal_dict = _model_dump(proposal_model)
        proposal_blob = json.dumps(proposal_dict, sort_keys=True).encode("utf-8")
        proposal_hash = hashlib.sha256(proposal_blob).hexdigest()[:8]
        filename = f"{proposal_model.created_at.replace(':', '-')}_{proposal_hash}.json"
        path = os.path.join(self._proposal_dir(project), filename)

        with open(path, "w", encoding="UTF-8") as handle:
            json.dump(proposal_dict, handle, indent=2, ensure_ascii=True)

        return {"saved": True, "path": path.replace("\\", "/"), "proposal": proposal_dict}
