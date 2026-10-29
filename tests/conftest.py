import sqlite3
from datetime import date
from pathlib import Path

import pytest

from pachaplan.db import connect

FIXTURE = Path(__file__).with_name("fixture.sql")
TODAY = date(2026, 11, 2)


@pytest.fixture
def db_path(tmp_path):
    """A fresh copy of the small test database, built from fixture.sql."""
    path = tmp_path / "test.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript(FIXTURE.read_text(encoding="utf-8"))
    conn.close()
    return path


@pytest.fixture
def conn(db_path):
    c = connect(db_path)
    yield c
    c.close()
