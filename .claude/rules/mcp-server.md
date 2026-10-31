---
paths:
  - "src/pachaplan/mcp_server.py"
  - "tests/test_mcp_server.py"
---

# MCP server

- Every tool opens its connection with `open_read_only`: `mode=ro`, then
  `PRAGMA query_only` and an authorizer that allows reads only. `mode=ro` alone lets
  an `ATTACH` create and write another file.
- A new tool goes through `open_read_only` and runs fixed SQL with bound values,
  never SQL it receives.
