"""Checks the connections of the pachaplan MCP server, for the module 13 exercise.

    uv run python mcp_write_check.py

Run it from the root of the project. It starts the server in memory on a copy of
data/pachaplan.sqlite, calls every tool once, and records each connection a tool
opens through open_read_only. Each of them must refuse an INSERT and an ATTACH,
and the copy must be unchanged. A tool that opens its own connection, outside
open_read_only, makes the check fail: nothing would then stop it from writing.
Exit code 0 when everything holds, 1 otherwise.
"""

import asyncio
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from mcp import Client

from pachaplan import mcp_server

ARGUMENTS = {
    "sessions_starting_in_week": {"day": "2026-11-16"},
    "trainer_month_load": {"trainer": "Prokopowicz", "month": "2026-11"},
    "unpaid_invoices": {"days": 30},
}
WRITES = {
    "INSERT": "INSERT INTO language VALUES ('XX', 'Test')",
    "ATTACH": "ATTACH DATABASE 'mcp_write_check.sqlite' AS other",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    failed = 0
    work = Path(tempfile.mkdtemp())
    db = work / "copy.sqlite"
    shutil.copy(Path("data") / "pachaplan.sqlite", db)
    before = digest(db)
    os.chdir(work)  # an ATTACH that succeeds creates its file here

    opened = []
    original = mcp_server.open_read_only

    def recording(path):
        conn = original(path)
        opened.append(conn)
        return conn

    mcp_server.open_read_only = recording

    async def call_all():
        async with Client(mcp_server.create_server(db)) as client:
            tools = (await client.list_tools()).tools
            for tool in tools:
                count = len(opened)
                result = await client.call_tool(tool.name, ARGUMENTS.get(tool.name, {}))
                yield tool, result, len(opened) > count

    async def run():
        nonlocal failed
        names = []
        async for tool, result, used in call_all():
            names.append(tool.name)
            if result.is_error:
                print(f"FAIL  {tool.name}: the call returned an error: {result.content[0].text}")
                failed += 1
            elif not used:
                print(f"FAIL  {tool.name}: no connection through open_read_only")
                failed += 1
            else:
                print(f"OK    {tool.name}: connection through open_read_only")
        if "unpaid_invoices" not in names:
            print("FAIL  the server has no unpaid_invoices tool")
            failed += 1

    asyncio.run(run())

    # The connections are closed by the tools; open one more the same way and try.
    conn = original(db)
    for label, sql in WRITES.items():
        try:
            conn.execute(sql)
        except sqlite3.DatabaseError as exc:
            print(f"OK    {label} refused ({exc})")
        else:
            print(f"FAIL  {label} accepted by the server's connection")
            failed += 1
    conn.close()
    if (work / "mcp_write_check.sqlite").exists():
        print("FAIL  the ATTACH created a database file")
        failed += 1
    if digest(db) != before:
        print("FAIL  the database copy changed")
        failed += 1
    shutil.rmtree(work)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
