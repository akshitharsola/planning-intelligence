## graphify

This project has a graphify knowledge graph at `graphify-out/`. It is
committed to the repo so every collaborator gets it on clone — no local
setup needed to browse the architecture.

Rules:
- Before answering architecture or codebase questions, read
  `graphify-out/GRAPH_REPORT.md` for god nodes and community structure.
- If `graphify-out/wiki/index.md` exists, navigate it instead of reading
  raw files.
- After modifying code files in this session, run `graphify update .` to
  keep the graph current (AST-only, no API cost) and commit the
  `graphify-out/` changes alongside your code changes in the same commit.
