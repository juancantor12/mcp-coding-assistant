
# MCP Coding Assistant

A small MCP server that exposes file and project tools, plus a first-pass code
graph indexer meant to keep model context tight by pointing to exact file spans.

## Quickstart
- activate the virtual env
- run: `mcp dev .\server.py`
- confirm inspector installation (might require a fix in `requirements.txt`)
- when the webapp launches, connect with:
  - command: `mcp run`
  - arguments: `server.py`

## CLI entry point
Use the terminal chat client to talk to Ollama and propose graph changes:
```
python cli.py
```
Commands: `/actions`, `/help`, `/exit`
If you omit `--project`, the CLI will prompt you to select or create one.
Model defaults come from `OLLAMA_MODEL`/`OLLAMA_URL` or `globals.py`.

## Interpreter entry point
Apply approved graph proposals to code (internal use):
```
python interpreter_cli.py --project test --proposal graphs/proposals/test/<proposal>.json
```

## Projects and paths
- Projects live in `apps/`
- Allowed projects and extensions are listed in `globals.py`
- Code graphs are written to `graphs/<project>.codegraph.json`

## Code graph schema (v0.1.0)
The graph is JSON and intended to be easy to read, extend, and parse by other
models or tooling.

Top-level keys:
- `schema_version`: semver for the graph format
- `project`: project name
- `generated_at`: UTC timestamp
- `root`: project root path
- `files`: list of file entries with `path` and `language`
- `nodes`: graph nodes
- `edges`: graph edges
- `kinds`: allowed node/edge kinds in this version
- `extensions`: reserved object for future schema extensions

Node shape:
```
{
  "id": "n1",
  "kind": "class|function|method|module|import",
  "name": "SymbolName",
  "file": "relative/path.py",
  "range": { "start_line": 10, "end_line": 42 },
  "extra": { ... }
}
```

Edge shape:
```
{
  "from": "n1",
  "to": "n2",
  "kind": "defines|belongs_to|imports",
  "extra": { ... }
}
```

## MCP tools
- `build_code_graph(project)` builds the JSON graph for a project.
- `query_code_graph(project, term, kind=None)` filters nodes by name or file
  path and returns related edges.
- `save_graph_proposal(project, proposal)` validates and stores a graph change
  proposal under `graphs/proposals/<project>/`.
- `apply_graph_proposal(project, proposal_path)` applies a proposal to code and
  updates the graph (python-only, add-node/edge only).
- `create_project(project, description)` creates a new project and writes its
  `readme.md`.
- `git_status()` returns `git status -sb`.
- `git_add_all()` runs `git add .`.
- `git_commit(message)` runs `git commit -m <message>`.
- `git_push()` pushes the current branch to `origin`.

## Notes
- Current indexer only parses Python via `ast`.
- The schema is intentionally minimal; use `extensions` and `extra` for future
  additions (e.g., call graph, type info, or multi-language support).
