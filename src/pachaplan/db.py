"""Database access for pachaplan.

The database is a SQLite file. It is opened read-only unless the caller asks
otherwise, so that a report can never modify the planning data by accident.
"""

import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path("data") / "pachaplan.sqlite"


def resolve_path(db_arg=None):
    """Pick the database path: --db first, then PACHAPLAN_DB, then the default."""
    if db_arg:
        return Path(db_arg)
    env = os.environ.get("PACHAPLAN_DB")
    if env:
        return Path(env)
    return DEFAULT_DB


def connect(path, readonly=True):
    """Open the database. Read-only by default (SQLite URI with mode=ro)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"database not found: {path}")
    if readonly:
        conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query(conn, sql, params=()):
    """Run a query, values bound to its ? placeholders; return the rows as sqlite3.Row."""
    return conn.execute(sql, params).fetchall()


def scalar(conn, sql, params=()):
    """Run a query, values bound to its ? placeholders; return the first column of the first row."""
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None
