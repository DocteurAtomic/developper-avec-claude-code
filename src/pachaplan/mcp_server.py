"""MCP server of pachaplan: the planning questions, without a shell.

Run over stdio with `uv run pachaplan-mcp [--db PATH]`. Two read-only tools:

- sessions_in_week: the sessions starting in the week that holds a day;
- trainer_load: the session days of a trainer in a month.

The database is opened read-only by db.py (SQLite URI with mode=ro). That alone
does not stop a write: `mode=ro` covers the main file only, and an ATTACH can
still create and fill another one. So the server locks every connection on top
of it, with `PRAGMA query_only` and an SQLite authorizer that allows reads only.
The lock is in this code, not in the tool descriptions.
"""

import argparse
import os
import sqlite3
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from . import __version__, planning
from .db import connect, query, resolve_path

# The authorizer actions a SELECT needs. Everything else (INSERT, UPDATE, DELETE,
# CREATE, DROP, ATTACH, PRAGMA, transactions) is denied.
READ_ACTIONS = frozenset(
    {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
)

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)


def read_only_authorizer(action, arg1, arg2, db_name, trigger):
    """SQLite authorizer: allow reads, deny everything else."""
    return sqlite3.SQLITE_OK if action in READ_ACTIONS else sqlite3.SQLITE_DENY


def open_read_only(path):
    """Open the database read-only through db.py, then lock the connection.

    `query_only` is set first, while PRAGMA is still allowed; the authorizer then
    denies PRAGMA too, so the setting cannot be turned off.
    """
    conn = connect(path, readonly=True)
    conn.execute("PRAGMA query_only = ON")
    conn.set_authorizer(read_only_authorizer)
    return conn


def server_db_path(db_arg=None):
    """The database of the server: --db, PACHAPLAN_DB, then data/pachaplan.sqlite.

    Claude Code starts the server in the directory where `claude` was launched,
    and passes the same directory in CLAUDE_PROJECT_DIR. A relative path is looked
    for there and in its parents, so the server also starts from a subdirectory.
    """
    path = resolve_path(db_arg)
    if path.is_absolute():
        return path
    start = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    for base in (start, *start.parents):
        if (base / path).exists():
            return base / path
    return start / path


def week_bounds(text):
    """Monday and Sunday of the week that holds day `text` (YYYY-MM-DD)."""
    try:
        day = planning.parse_day(text)
    except ValueError:
        raise ToolError(f"invalid date {text!r}, expected YYYY-MM-DD") from None
    monday = day - timedelta(days=day.weekday())
    return monday, monday + timedelta(days=6)


def month_bounds(text):
    """First and last day of month `text` (YYYY-MM)."""
    try:
        first, following = planning.parse_month(text)
    except ValueError:
        raise ToolError(f"invalid month {text!r}, expected YYYY-MM") from None
    return first, following - timedelta(days=1)


def sessions_in_week(conn, day):
    """Sessions starting in the week (Monday to Sunday) that holds `day`, canceled ones out."""
    monday, sunday = week_bounds(day)
    rows = query(
        conn,
        """
        SELECT s.session_id, s.start_date, s.duration_days, s.status_code, s.remarks,
               c.code, c.title, c.max_attendees, l.city, l.name AS location,
               s.trainer_id, tc.first_name AS trainer_first_name, tc.last_name AS trainer_last_name
        FROM session s
        JOIN course c ON c.course_id = s.course_id
        LEFT JOIN room r ON r.room_id = s.room_id
        LEFT JOIN location l ON l.location_id = r.location_id
        LEFT JOIN trainer t ON t.trainer_id = s.trainer_id
        LEFT JOIN contact tc ON tc.contact_id = t.contact_id
        WHERE s.start_date BETWEEN ? AND ?
          AND s.status_code <> 'CANCELED'
        ORDER BY s.start_date, s.session_id
        """,
        (monday.isoformat(), sunday.isoformat()),
    )
    sessions = [
        {
            "session_id": s["session_id"],
            "start_date": s["start_date"],
            "end_date": planning.session_end(s["start_date"], s["duration_days"]).isoformat(),
            "course": s["code"] or "",
            "title": s["title"],
            "city": s["city"] or s["location"] or "",
            "trainer_id": s["trainer_id"],
            "trainer": planning.session_trainer(s),
            "status": s["status_code"],
            "enrolled": planning.count_enrollments(conn, s["session_id"]),
            "capacity": s["max_attendees"],
            "remarks": s["remarks"] or "",
        }
        for s in rows
    ]
    return {"week_start": monday.isoformat(), "week_end": sunday.isoformat(), "sessions": sessions}


def find_trainer(conn, trainer):
    """(id, full name) of a trainer given by id, last name or full name; ToolError otherwise."""
    key = trainer.strip()
    rows = query(
        conn,
        """
        SELECT t.trainer_id, c.first_name, c.last_name
        FROM trainer t JOIN contact c ON c.contact_id = t.contact_id
        WHERE CAST(t.trainer_id AS TEXT) = ?
           OR lower(c.last_name) = lower(?)
           OR lower(COALESCE(c.first_name || ' ', '') || c.last_name) = lower(?)
        ORDER BY t.trainer_id
        """,
        (key, key, key),
    )
    if not rows:
        raise ToolError(f"no trainer matches {trainer!r}")
    if len(rows) > 1:
        names = ", ".join(
            f"{planning.full_name(r['first_name'], r['last_name'])} (id {r['trainer_id']})"
            for r in rows
        )
        raise ToolError(f"several trainers match {trainer!r}: {names}")
    row = rows[0]
    return row["trainer_id"], planning.full_name(row["first_name"], row["last_name"])


def trainer_load(conn, trainer, month):
    """The session days of a trainer in a month: each session with its days, and the total."""
    first, last = month_bounds(month)
    trainer_id, name = find_trainer(conn, trainer)
    rows = query(
        conn,
        """
        SELECT s.session_id, s.start_date, s.duration_days, s.status_code, c.code, c.title
        FROM session s
        JOIN course c ON c.course_id = s.course_id
        WHERE s.trainer_id = ?
          AND s.start_date <= ?
          AND date(s.start_date, '+' || (COALESCE(s.duration_days, 1) - 1) || ' days') >= ?
          AND s.status_code <> 'CANCELED'
        ORDER BY s.start_date, s.session_id
        """,
        (trainer_id, last.isoformat(), first.isoformat()),
    )
    sessions, all_days = [], set()
    for s in rows:
        start = planning.parse_day(s["start_date"])
        end = planning.session_end(start, s["duration_days"])
        span = (start + timedelta(days=i) for i in range((end - start).days + 1))
        days = [d for d in span if first <= d <= last]
        all_days.update(days)
        sessions.append(
            {
                "session_id": s["session_id"],
                "course": s["code"] or "",
                "title": s["title"],
                "status": s["status_code"],
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "days_in_month": [d.isoformat() for d in days],
            }
        )
    return {
        "trainer_id": trainer_id,
        "trainer": name,
        "month": f"{first:%Y-%m}",
        "sessions": sessions,
        "day_count": len(all_days),
    }


def create_server(db_path):
    """The MCP server, each tool call on its own locked connection to `db_path`."""
    server = MCPServer(
        name="pachaplan",
        version=__version__,
        instructions="Planning questions of the PachaData training team. Read-only.",
    )

    def run(fn, *args):
        conn = open_read_only(db_path)
        try:
            return fn(conn, *args)
        finally:
            conn.close()

    @server.tool(annotations=READ_ONLY)
    def sessions_starting_in_week(day: str) -> dict[str, Any]:
        """Sessions starting in the week (Monday to Sunday) that holds `day`, a YYYY-MM-DD date.

        Canceled sessions are left out. For each session: course, city, trainer,
        status, active enrollments (waiting list and cancellations excluded),
        capacity and remarks.
        """
        return run(sessions_in_week, day)

    @server.tool(annotations=READ_ONLY)
    def trainer_month_load(trainer: str, month: str) -> dict[str, Any]:
        """Session days of a trainer in `month` (YYYY-MM).

        `trainer` is a trainer id, a last name or a full name. Canceled sessions
        are left out. Returns each session with its days in the month, and in
        `day_count` the number of distinct days.
        """
        return run(trainer_load, trainer, month)

    return server


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pachaplan-mcp", description="MCP server (stdio) of pachaplan, read-only."
    )
    parser.add_argument(
        "--db", help="SQLite database (default: $PACHAPLAN_DB, then data/pachaplan.sqlite)"
    )
    args = parser.parse_args(argv)
    db_path = server_db_path(args.db)
    try:
        open_read_only(db_path).close()
    except FileNotFoundError as exc:
        # stdout belongs to the protocol: errors go to stderr.
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    create_server(db_path).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
