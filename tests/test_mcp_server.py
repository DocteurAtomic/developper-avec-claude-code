import asyncio
import hashlib
import sqlite3
import sys

import pytest
from mcp import Client, StdioServerParameters
from mcp.server.mcpserver.exceptions import ToolError

from pachaplan.mcp_server import (
    open_read_only,
    server_db_path,
    sessions_in_week,
    trainer_load,
)

WRITES = [
    "INSERT INTO language VALUES ('EN', 'English')",
    "UPDATE session SET remarks = 'x' WHERE session_id = 101",
    "CREATE TABLE t (x)",
    "PRAGMA query_only = OFF",
    "ATTACH DATABASE 'other.sqlite' AS other",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("sql", WRITES)
def test_server_connection_refuses_writes(db_path, sql, monkeypatch):
    # db.connect opens the file with mode=ro, which does not stop an ATTACH from
    # creating another file: the server's own lock has to refuse it.
    monkeypatch.chdir(db_path.parent)
    before = digest(db_path)
    conn = open_read_only(db_path)
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute(sql)
    conn.close()
    assert digest(db_path) == before
    assert not (db_path.parent / "other.sqlite").exists()


def test_sessions_in_week_lists_the_week_from_monday(conn):
    result = sessions_in_week(conn, "2026-11-12")
    assert (result["week_start"], result["week_end"]) == ("2026-11-09", "2026-11-15")
    sessions = {s["session_id"]: s for s in result["sessions"]}
    assert list(sessions) == [101, 102]
    assert sessions[101]["trainer"] == "Julie Lambert"
    assert (sessions[101]["enrolled"], sessions[101]["capacity"]) == (2, 10)


def test_sessions_in_week_leaves_out_canceled_sessions(conn):
    # 103, on 2026-11-16, is the only session of that week, and it is canceled.
    assert sessions_in_week(conn, "2026-11-16")["sessions"] == []


def test_trainer_load_counts_the_days_in_the_month(conn):
    result = trainer_load(conn, "Girard", "2026-11")
    assert (result["trainer_id"], result["day_count"]) == (2, 3)
    assert trainer_load(conn, "1", "2026-11")["day_count"] == 2


def test_trainer_load_refuses_an_unknown_trainer(conn):
    with pytest.raises(ToolError, match="no trainer matches"):
        trainer_load(conn, "Nobody", "2026-11")


def test_relative_path_is_found_from_a_subdirectory(monkeypatch, tmp_path):
    # claude launched in src/: the server starts there, with CLAUDE_PROJECT_DIR=src.
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "pachaplan.sqlite").touch()
    (tmp_path / "src").mkdir()
    monkeypatch.delenv("PACHAPLAN_DB", raising=False)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "src"))
    assert server_db_path() == tmp_path / "data" / "pachaplan.sqlite"


def test_server_runs_over_stdio(db_path):
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "pachaplan.mcp_server", "--db", str(db_path)]
    )

    async def go():
        async with Client(params) as client:
            tools = (await client.list_tools()).tools
            result = await client.call_tool("sessions_starting_in_week", {"day": "2026-11-10"})
            return tools, result

    tools, result = asyncio.run(go())
    assert {"sessions_starting_in_week", "trainer_month_load"} <= {t.name for t in tools}
    assert all(t.annotations.read_only_hint for t in tools)
    assert [s["session_id"] for s in result.structured_content["sessions"]] == [101, 102]
