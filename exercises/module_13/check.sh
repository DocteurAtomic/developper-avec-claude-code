#!/usr/bin/env bash
# Checks the module 13 exercise: the unpaid_invoices tool of the MCP server.
#
#   bash <(git show origin/course:exercises/module_13/check.sh)
#
# Run it from the root of the project, on your exercise-13 branch, after you have
# approved the pachaplan server in a claude session (/mcp). Six checks: the server in
# .mcp.json; the tool over stdio, read-only, with the count of the unpaid report and a
# result short enough for Claude Code; the connections of every tool (INSERT and
# ATTACH refused, by mcp_write_check.py from the same branch); the test suite; ruff;
# and claude mcp get. Nothing is written to data/pachaplan.sqlite.
set -u
export PACHAPLAN_TODAY=2026-11-02
COURSE=${COURSE:-origin/course}
failed=0
ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=$((failed + 1)); }

if [ ! -f pyproject.toml ] || [ ! -f data/pachaplan.sqlite ]; then
    echo "Run this from the root of the pachaplan project." >&2; exit 2
fi
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# 1. The server is declared for the project.
if uv run --quiet python - <<'PY'
import json, sys
servers = json.load(open(".mcp.json")).get("mcpServers", {})
entry = servers.get("pachaplan", {})
sys.exit(0 if "pachaplan-mcp" in [entry.get("command"), *entry.get("args", [])] else 1)
PY
then ok ".mcp.json declares the pachaplan server (pachaplan-mcp)"
else fail ".mcp.json has no pachaplan server running pachaplan-mcp"; fi

# 2. The tool, over stdio, as Claude Code starts it.
out=$(uv run --quiet python - <<'PY' 2>&1
import asyncio, json, os, sys
from mcp import Client, StdioServerParameters
from pachaplan.db import connect
from pachaplan.planning import parse_day, unpaid_invoices

expected = unpaid_invoices(connect("data/pachaplan.sqlite"), parse_day("2026-11-02"), 30)
count = expected["totals"]["count"]
latest = expected["rows"][0]["invoice_code"]

async def go():
    # The SDK passes only a few variables to the server; Claude Code passes them all.
    params = StdioServerParameters(command="uv", args=["run", "pachaplan-mcp"], env=dict(os.environ))
    async with Client(params) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
        if "unpaid_invoices" not in tools:
            return "no unpaid_invoices tool"
        if not (tools["unpaid_invoices"].annotations and tools["unpaid_invoices"].annotations.read_only_hint):
            return "unpaid_invoices is not marked read-only (read_only_hint)"
        result = await client.call_tool("unpaid_invoices", {"days": 30})
        if result.is_error:
            return "the call returned an error: " + result.content[0].text
        text = json.dumps(result.structured_content) if result.structured_content else \
            " ".join(getattr(c, "text", "") for c in result.content)
        if str(count) not in text:
            return f"the result does not give the {count} unpaid invoices of the report"
        if latest not in text:
            return f"the result does not show {latest}, the invoice most days late"
        if len(text) >= 50_000:
            return f"the result is {len(text)} characters: Claude Code saves it to a file past 50000"
        return f"OK {count} invoices, {len(text)} characters"

print(asyncio.run(go()))
PY
)
case "$out" in
    OK*) ok "unpaid_invoices over stdio: ${out#OK }" ;;
    *)   fail "unpaid_invoices over stdio: $(printf '%s' "$out" | tail -n 1)" ;;
esac

# 3. The connections of every tool.
helper=$work/mcp_write_check.py
if [ -n "${MCP_WRITE_CHECK:-}" ]; then cp "$MCP_WRITE_CHECK" "$helper"
else git show "$COURSE:exercises/module_13/mcp_write_check.py" > "$helper" 2>/dev/null; fi
if [ ! -s "$helper" ]; then
    fail "mcp_write_check.py not found on $COURSE (git fetch origin course)"
elif report=$(uv run --quiet python "$helper" 2>&1); then
    ok "every tool goes through open_read_only; INSERT and ATTACH refused"
else
    fail "connections: $(printf '%s\n' "$report" | grep FAIL | head -n 1)"
fi

# 4. The test suite, with the real database and no skipped test.
if summary=$(PACHAPLAN_DB=data/pachaplan.sqlite uv run --quiet pytest -q --fail-on-skip 2>&1); then
    ok "test suite: $(printf '%s\n' "$summary" | tail -n 1)"
else
    fail "test suite: $(printf '%s\n' "$summary" | tail -n 1)"
fi

# 5. Lint.
if uv run --quiet ruff check > /dev/null 2>&1; then ok "ruff check"
else fail "ruff check (uv run ruff check)"; fi

# 6. Claude Code sees the server connected.
status=$(claude mcp get pachaplan 2>&1 | grep -m 1 'Status:')
case "$status" in
    *Connected*) ok "claude mcp get pachaplan: connected" ;;
    *Pending*)   fail "claude mcp get pachaplan: pending approval (approve it in a claude session, /mcp)" ;;
    *)           fail "claude mcp get pachaplan: ${status:-no status}" ;;
esac

if [ "$failed" -eq 0 ]; then echo "All checks passed."; exit 0; fi
echo "$failed check(s) failed."; exit 1
