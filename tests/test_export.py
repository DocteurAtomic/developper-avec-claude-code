import csv
import io
import sqlite3
from datetime import date

from pachaplan.db import connect
from pachaplan.planning import EXPORT_COLUMNS, export_month, parse_month


def test_export_writes_one_row_per_line_and_a_total(conn):
    out = io.StringIO()
    count, _total = export_month(conn, "2026-09", out)
    rows = list(csv.reader(io.StringIO(out.getvalue())))
    assert count == 5
    assert rows[0] == EXPORT_COLUMNS
    assert len(rows) == 1 + 5 + 1
    assert [r[0] for r in rows[1:-1]] == ["FA1", "FA1", "FA2", "FA3", "AV1"]
    assert rows[-1][0] == "TOTAL"


def add_invoice(db_path, code, day, net, gross):
    """Insert an invoice with one line into the test copy of the database."""
    raw = sqlite3.connect(db_path)
    raw.execute(
        "INSERT INTO invoice VALUES (?, 'I', NULL, 105, 1, NULL, ?, NULL, ?, ?, 20, NULL, 0, "
        "NULL, NULL)",
        (code, day, net, gross),
    )
    raw.execute(
        "INSERT INTO invoice_line VALUES (?, 1, 'COUR', 8, 'Training', 1, ?, ?)",
        (code, net, net),
    )
    raw.commit()
    raw.close()


def export_rows(db_path, month):
    conn = connect(db_path)
    out = io.StringIO()
    export_month(conn, month, out)
    conn.close()
    return list(csv.reader(io.StringIO(out.getvalue())))


def test_parse_month_ends_on_the_first_of_the_next_month():
    assert parse_month("2026-03") == (date(2026, 3, 1), date(2026, 4, 1))
    assert parse_month("2026-02") == (date(2026, 2, 1), date(2026, 3, 1))
    assert parse_month("2026-12") == (date(2026, 12, 1), date(2027, 1, 1))


def test_export_includes_the_last_day_of_a_31_day_month(db_path):
    add_invoice(db_path, "FA31", "2026-10-31", 100, 120)
    rows = export_rows(db_path, "2026-10")

    raw = sqlite3.connect(db_path)
    expected = raw.execute(
        "SELECT SUM(gross_amount) FROM invoice "
        "WHERE invoice_date >= '2026-10-01' AND invoice_date < '2026-11-01'"
    ).fetchone()[0]
    raw.close()

    # FA4 of the fixture is in October too: the total covers both invoices.
    assert "FA31" in [r[0] for r in rows[1:-1]]
    assert rows[-1][12] == f"{expected:.2f}"


def test_february_export_stops_before_march(db_path):
    add_invoice(db_path, "FA0301", "2026-03-01", 100, 120)
    rows = export_rows(db_path, "2026-02")
    assert "FA0301" not in [r[0] for r in rows[1:-1]]
