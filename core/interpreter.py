"""Applies graph change proposals to code."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from core.config import AppConfig
from core.files import FileService
from core.graph import GraphService
from core.projects import ProjectManager


class GraphChangeApplier:
    def __init__(
        self,
        config: AppConfig,
        projects: ProjectManager,
        files: FileService,
        graphs: GraphService,
    ) -> None:
        self._config = config
        self._projects = projects
        self._files = files
        self._graphs = graphs

    def _project_root(self, project: str) -> str:
        return os.path.join(self._config.base_path, project)

    def _graph_path(self, project: str) -> str:
        return os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            "graphs",
            f"{project}.codegraph.json",
        )

    def _load_graph(self, project: str) -> dict[str, Any]:
        graph_path = self._graph_path(project)
        if not os.path.exists(graph_path):
            raise ValueError("Graph not found, build it first")
        with open(graph_path, "r", encoding="UTF-8") as handle:
            return json.load(handle)

    def _write_graph(self, project: str, graph: dict[str, Any]) -> None:
        graph_path = self._graph_path(project)
        with open(graph_path, "w", encoding="UTF-8") as handle:
            json.dump(graph, handle, indent=2, ensure_ascii=True)

    def _split_file(self, file_rel: str) -> tuple[str, str, str]:
        folder, filename = os.path.split(file_rel)
        if "." not in filename:
            raise ValueError(f"Invalid file path: {file_rel}")
        name, ext = filename.rsplit(".", 1)
        return folder.replace("\\", "/"), name, ext

    def _read_file(self, project: str, file_rel: str) -> str:
        full_path = os.path.join(self._project_root(project), file_rel)
        if os.path.exists(full_path):
            return self._files.load(project, file_rel)
        return ""

    def _write_file(self, project: str, file_rel: str, content: str) -> None:
        folder, name, ext = self._split_file(file_rel)
        self._files.save(project, folder, name, ext, content)

    def _append_snippet(self, content: str, snippet_lines: list[str]) -> tuple[str, int, int]:
        lines = content.splitlines()
        if lines and lines[-1].strip() != "":
            lines.append("")
        start_line = len(lines) + 1
        lines.extend(snippet_lines)
        end_line = len(lines)
        return "\n".join(lines) + "\n", start_line, end_line

    def _insert_import(self, content: str, import_line: str) -> tuple[str, int, int]:
        lines = content.splitlines()
        idx = 0
        if lines and lines[0].startswith("#!"):
            idx = 1
        if idx < len(lines) and lines[idx].startswith("#") and "coding" in lines[idx]:
            idx += 1

        if idx < len(lines) and lines[idx].lstrip().startswith(('"""', "'''")):
            quote = '"""' if '"""' in lines[idx] else "'''"
            idx += 1
            while idx < len(lines):
                if quote in lines[idx]:
                    idx += 1
                    break
                idx += 1

        import_block_end = idx
        while import_block_end < len(lines):
            line = lines[import_block_end]
            if line.startswith("import ") or line.startswith("from "):
                import_block_end += 1
                continue
            if line.strip() == "":
                import_block_end += 1
                continue
            break

        insert_at = import_block_end
        lines.insert(insert_at, import_line)
        start_line = insert_at + 1
        end_line = start_line
        return "\n".join(lines) + "\n", start_line, end_line

    def _update_ranges_after_delta(
        self,
        nodes: list[dict[str, Any]],
        file_rel: str,
        anchor_end: int,
        delta: int,
    ) -> None:
        if delta == 0:
            return
        for node in nodes:
            if node.get("file") != file_rel:
                continue
            node_range = node.get("range") or {}
            start_line = node_range.get("start_line")
            end_line = node_range.get("end_line")
            if start_line is None or end_line is None:
                continue
            if start_line > anchor_end:
                node_range["start_line"] = start_line + delta
                node_range["end_line"] = end_line + delta

    def _find_class_block(self, lines: list[str], class_name: str) -> tuple[int, int, int] | None:
        for idx, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped.startswith("class "):
                continue
            header = stripped.split("(")[0].replace("class ", "").strip().rstrip(":")
            if header != class_name:
                continue
            class_indent = len(line) - len(stripped)
            end = len(lines)
            for j in range(idx + 1, len(lines)):
                line_j = lines[j]
                if not line_j.strip():
                    continue
                indent = len(line_j) - len(line_j.lstrip())
                if indent <= class_indent:
                    end = j
                    break
            return idx, end, class_indent
        return None

    def _insert_method(
        self, content: str, class_name: str, method_lines: list[str]
    ) -> tuple[str, int, int]:
        lines = content.splitlines()
        found = self._find_class_block(lines, class_name)
        if not found:
            raise ValueError(f"Class not found: {class_name}")
        _, end, class_indent = found
        method_indent = " " * (class_indent + 4)
        indented_lines = [
            f"{method_indent}{line}" if line else "" for line in method_lines
        ]
        insert_at = end
        if insert_at > 0 and lines[insert_at - 1].strip() != "":
            lines.insert(insert_at, "")
            insert_at += 1
        lines[insert_at:insert_at] = indented_lines
        start_line = insert_at + 1
        end_line = insert_at + len(indented_lines)
        return "\n".join(lines) + "\n", start_line, end_line

    def apply_proposal(self, project: str, proposal_path: str) -> dict[str, Any]:
        if project not in self._config.projects:
            raise ValueError("Invalid project")

        if not os.path.exists(proposal_path):
            raise ValueError("Proposal path not found")

        with open(proposal_path, "r", encoding="UTF-8") as handle:
            proposal = json.load(handle)

        current_hash = self._graphs.compute_code_hash(project)
        if proposal.get("base_code_hash") != current_hash:
            raise ValueError("Code hash mismatch")

        graph = self._load_graph(project)
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        nodes_by_id = {node["id"]: node for node in nodes}
        node_ids = set(nodes_by_id.keys())
        allowed_node_kinds = set(graph.get("kinds", {}).get("node", []))
        allowed_edge_kinds = set(graph.get("kinds", {}).get("edge", []))

        operations = proposal.get("operations", [])
        if not isinstance(operations, list):
            raise ValueError("Invalid proposal operations")

        add_nodes = [op for op in operations if op.get("op") == "add_node"]
        add_edges = [op for op in operations if op.get("op") == "add_edge"]
        update_nodes = [op for op in operations if op.get("op") == "update_node"]
        delete_nodes = [op for op in operations if op.get("op") == "delete_node"]
        delete_edges = [op for op in operations if op.get("op") == "delete_edge"]

        added_nodes = {op["node"]["id"]: op["node"] for op in add_nodes if op.get("node")}
        added_edges = [op.get("edge") for op in add_edges if op.get("edge")]

        for node_id in added_nodes:
            if node_id in node_ids:
                raise ValueError(f"Node already exists: {node_id}")

        for node in added_nodes.values():
            kind = node.get("kind")
            if allowed_node_kinds and kind not in allowed_node_kinds:
                raise ValueError(f"Invalid node kind: {kind}")
            if kind not in {"class", "function", "method", "import"}:
                raise ValueError(f"Unsupported node kind for apply: {kind}")
            if not node.get("name") or not node.get("file"):
                raise ValueError("add_node requires name and file")

        for edge in added_edges:
            if not edge:
                continue
            kind = edge.get("kind")
            if allowed_edge_kinds and kind not in allowed_edge_kinds:
                raise ValueError(f"Invalid edge kind: {kind}")

        for op in update_nodes:
            if not op.get("node_id") or not op.get("patch"):
                raise ValueError("update_node requires node_id and patch")
            if op["node_id"] not in node_ids:
                raise ValueError(f"Node not found: {op['node_id']}")
            if "file" in op["patch"]:
                raise ValueError("update_node does not support file moves")
            if "kind" in op["patch"]:
                raise ValueError("update_node does not support kind changes")

        for op in delete_nodes:
            if not op.get("node_id"):
                raise ValueError("delete_node requires node_id")
            if op["node_id"] not in node_ids:
                raise ValueError(f"Node not found: {op['node_id']}")

        for op in delete_edges:
            edge = op.get("edge")
            if not edge:
                raise ValueError("delete_edge requires edge")
            if edge.get("kind") and allowed_edge_kinds and edge["kind"] not in allowed_edge_kinds:
                raise ValueError(f"Invalid edge kind: {edge['kind']}")

        owner_by_method: dict[str, str] = {}
        for edge in added_edges:
            if not edge:
                continue
            if edge.get("kind") == "belongs_to":
                owner_by_method[edge.get("to")] = edge.get("from")

        file_updates: dict[str, str] = {}
        applied_nodes: list[dict[str, Any]] = []
        deleted_node_ids: set[str] = set()

        for node_id, node in added_nodes.items():
            kind = node["kind"]
            file_rel = node["file"]
            name = node["name"]
            content = file_updates.get(file_rel, self._read_file(project, file_rel))

            if kind == "class":
                snippet = [f"class {name}:", "    pass"]
                updated, start, end = self._append_snippet(content, snippet)
            elif kind == "function":
                snippet = [f"def {name}():", "    pass"]
                updated, start, end = self._append_snippet(content, snippet)
            elif kind == "import":
                import_line = f"import {name}" if "." not in name else f"from {name.rsplit('.', 1)[0]} import {name.rsplit('.', 1)[1]}"
                updated, start, end = self._insert_import(content, import_line)
            else:
                owner_id = owner_by_method.get(node_id)
                owner_name = None
                if owner_id:
                    if owner_id in added_nodes:
                        owner_name = added_nodes[owner_id].get("name")
                    else:
                        for existing in graph.get("nodes", []):
                            if existing.get("id") == owner_id:
                                owner_name = existing.get("name")
                                break
                if not owner_name:
                    owner_name = node.get("extra", {}).get("owner")
                if not owner_name:
                    raise ValueError(f"Method owner not found for node {node_id}")
                snippet = [f"def {name}(self):", "    pass"]
                updated, start, end = self._insert_method(content, owner_name, snippet)

            file_updates[file_rel] = updated
            node["range"] = {"start_line": start, "end_line": end}
            applied_nodes.append(node)

        for op in update_nodes:
            node_id = op["node_id"]
            node = nodes_by_id[node_id]
            patch = op["patch"]
            new_name = patch.get("name")
            if not new_name:
                continue
            file_rel = node["file"]
            content = file_updates.get(file_rel, self._read_file(project, file_rel))
            lines = content.splitlines()
            node_range = node.get("range") or {}
            start_line = node_range.get("start_line")
            if not start_line:
                raise ValueError(f"Node has no start_line: {node_id}")
            idx = start_line - 1
            line = lines[idx]
            if node["kind"] == "class" and line.lstrip().startswith("class "):
                lines[idx] = line.replace(f"class {node['name']}", f"class {new_name}", 1)
            elif node["kind"] in {"function", "method"} and line.lstrip().startswith("def "):
                lines[idx] = line.replace(f"def {node['name']}", f"def {new_name}", 1)
            elif node["kind"] == "import":
                lines[idx] = line.replace(node["name"], new_name, 1)
            else:
                raise ValueError(f"Unsupported update for node kind: {node['kind']}")
            node["name"] = new_name
            file_updates[file_rel] = "\n".join(lines) + "\n"

        for op in delete_nodes:
            node_id = op["node_id"]
            node = nodes_by_id[node_id]
            file_rel = node["file"]
            content = file_updates.get(file_rel, self._read_file(project, file_rel))
            lines = content.splitlines()
            node_range = node.get("range") or {}
            start_line = node_range.get("start_line")
            end_line = node_range.get("end_line")
            if not start_line or not end_line:
                raise ValueError(f"Node has no range: {node_id}")
            del lines[start_line - 1 : end_line]
            delta = -(end_line - start_line + 1)
            self._update_ranges_after_delta(nodes, file_rel, end_line, delta)
            file_updates[file_rel] = "\n".join(lines) + "\n"
            deleted_node_ids.add(node_id)

        for file_rel, content in file_updates.items():
            self._write_file(project, file_rel, content)

        if deleted_node_ids:
            nodes[:] = [node for node in nodes if node.get("id") not in deleted_node_ids]
            edges[:] = [
                edge
                for edge in edges
                if edge.get("from") not in deleted_node_ids
                and edge.get("to") not in deleted_node_ids
            ]

        for op in delete_edges:
            edge = op.get("edge")
            if not edge:
                continue
            edges[:] = [
                e
                for e in edges
                if not (
                    e.get("from") == edge.get("from")
                    and e.get("to") == edge.get("to")
                    and e.get("kind") == edge.get("kind")
                )
            ]

        for node in applied_nodes:
            nodes.append(node)
            nodes_by_id[node["id"]] = node
        for edge in added_edges:
            if edge:
                edges.append(edge)

        graph["generated_at"] = datetime.now(timezone.utc).isoformat()
        graph["code_hash"] = self._graphs.compute_code_hash(project)
        self._write_graph(project, graph)

        return {
            "applied": True,
            "files_updated": sorted(file_updates.keys()),
            "nodes_added": [node["id"] for node in applied_nodes],
            "edges_added": len([e for e in added_edges if e]),
            "nodes_updated": len(update_nodes),
            "nodes_deleted": len(deleted_node_ids),
            "edges_deleted": len(delete_edges),
            "new_code_hash": graph["code_hash"],
        }
