"""Internal CLI to apply graph proposals."""
from __future__ import annotations

import argparse

from core.config import AppConfig
from core.files import FileService
from core.graph import GraphService
from core.interpreter import GraphChangeApplier
from core.projects import ProjectManager


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply a graph proposal to code (interpreter only)."
    )
    parser.add_argument("--project", default="test", help="Target project name.")
    parser.add_argument("--proposal", required=True, help="Path to proposal JSON.")
    args = parser.parse_args()

    config = AppConfig.from_globals()
    projects = ProjectManager(config)
    files = FileService(config, projects)
    graphs = GraphService(config)
    interpreter = GraphChangeApplier(config, projects, files, graphs)

    result = interpreter.apply_proposal(project=args.project, proposal_path=args.proposal)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
