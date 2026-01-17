"""Interactive terminal for Ollama-driven graph proposals."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from typing import Any

from server import (
    build_code_graph,
    list_available_extensions,
    list_available_projects,
    query_code_graph,
    save_graph_proposal,
)


TOOL_DEFS = [
    {
        "name": "build_code_graph",
        "description": "Builds the project graph and returns metadata including code_hash.",
        "params": {"project": "string"},
    },
    {
        "name": "query_code_graph",
        "description": "Queries the graph by name or file path and returns matches.",
        "params": {"project": "string", "term": "string", "kind": "string|null"},
    },
    {
        "name": "save_graph_proposal",
        "description": "Validates and stores a graph change proposal.",
        "params": {"project": "string", "proposal": "object"},
    },
]

TOOL_MAP = {
    "build_code_graph": build_code_graph,
    "query_code_graph": query_code_graph,
    "save_graph_proposal": save_graph_proposal,
}


class OllamaClient:
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))


class AgentTerminal:
    def __init__(self, project: str, model: str, base_url: str) -> None:
        self._project = project
        self._client = OllamaClient(base_url, model)
        self._messages: list[dict[str, str]] = []

    def _system_prompt(self) -> str:
        return (
            "You are a coding assistant that operates via graph changes only. "
            "Never request direct file edits or file tools. "
            "Respond ONLY with valid JSON in this shape:\n"
            "{\n"
            '  "assistant_message": "text for the user",\n'
            '  "actions": [\n'
            '    {"tool": "tool_name", "args": {"project": "...", ...}}\n'
            "  ]\n"
            "}\n"
            "Available tools:\n"
            f"{json.dumps(TOOL_DEFS, indent=2)}\n"
            "To create a proposal, first call build_code_graph to get code_hash."
        )

    def _print_actions(self) -> None:
        print("\nAvailable actions:")
        for tool in TOOL_DEFS:
            print(f"- {tool['name']}: {tool['description']}")
        print()

    def _execute_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for action in actions:
            tool_name = action.get("tool")
            args = action.get("args", {})
            if tool_name not in TOOL_MAP:
                results.append(
                    {"tool": tool_name, "error": "Unknown tool", "args": args}
                )
                continue
            if "project" not in args:
                args["project"] = self._project

            if tool_name == "save_graph_proposal":
                confirm = input("Approve proposal and save? [y/N]: ").strip().lower()
                if confirm != "y":
                    results.append(
                        {"tool": tool_name, "skipped": True, "reason": "Not approved"}
                    )
                    continue

            try:
                result = TOOL_MAP[tool_name](**args)
                results.append({"tool": tool_name, "result": result})
            except Exception as exc:
                results.append({"tool": tool_name, "error": str(exc)})
        return results

    def _parse_model_response(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"assistant_message": content, "actions": []}

    def run(self) -> None:
        projects = list_available_projects()
        extensions = list_available_extensions()
        print("MCP Coding Assistant CLI")
        print(f"Project: {self._project}")
        print(f"Available projects: {projects}")
        print(f"Allowed extensions: {extensions}")
        self._print_actions()

        system_message = {"role": "system", "content": self._system_prompt()}
        self._messages.append(system_message)

        while True:
            user_input = input("You> ").strip()
            if not user_input:
                continue
            if user_input in {"/exit", "/quit"}:
                break
            if user_input == "/actions":
                self._print_actions()
                continue
            if user_input == "/help":
                print("Commands: /actions, /help, /exit")
                continue

            self._messages.append({"role": "user", "content": user_input})
            response = self._client.chat(self._messages)
            content = response.get("message", {}).get("content", "")
            parsed = self._parse_model_response(content)
            actions = parsed.get("actions", [])
            if not isinstance(actions, list):
                actions = []

            if actions:
                results = self._execute_actions(actions)
                print("\nTool results:")
                print(json.dumps(results, indent=2))
            message = parsed.get("assistant_message", content)
            print(f"\nAssistant> {message}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interactive terminal for Ollama-driven graph proposals."
    )
    parser.add_argument("--project", default="test", help="Target project name.")
    parser.add_argument("--model", default="llama3.1", help="Ollama model name.")
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Base URL for Ollama.",
    )
    args = parser.parse_args()

    terminal = AgentTerminal(args.project, args.model, args.ollama_url)
    terminal.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
