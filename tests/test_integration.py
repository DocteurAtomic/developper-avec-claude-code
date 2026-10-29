"""Integration test on the real database. Set PACHAPLAN_DB to run it."""

import csv
import io
import os
import sqlite3

import pytest

from pachaplan.db import connect
from pachaplan.planning import export_month


def test_export_matches_invoice_lines_of_the_real_database():
    path = os.environ.get("PACHAPLAN_DB")
    if not path:
        pytest.skip("PACHAPLAN_DB is not set")
    conn = connect(path)
    out = io.StringIO()
    count, _total = export_month(conn, "2026-10", out)
    conn.close()

    raw = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    expected = raw.execute(
        "SELECT COUNT(*) FROM invoice_line l JOIN invoice i ON i.invoice_code = l.invoice_code "
        "WHERE i.invoice_date >= '2026-10-01' AND i.invoice_date < '2026-11-01'"
    ).fetchone()[0]
    raw.close()

    rows = list(csv.reader(io.StringIO(out.getvalue())))
    assert expected > 1000
    assert count == expected
    assert len(rows) == expected + 2
