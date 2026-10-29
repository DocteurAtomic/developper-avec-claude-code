import csv
import io

from pachaplan.planning import EXPORT_COLUMNS, export_month


def test_export_writes_one_row_per_line_and_a_total(conn):
    out = io.StringIO()
    count, _total = export_month(conn, "2026-09", out)
    rows = list(csv.reader(io.StringIO(out.getvalue())))
    assert count == 5
    assert rows[0] == EXPORT_COLUMNS
    assert len(rows) == 1 + 5 + 1
    assert [r[0] for r in rows[1:-1]] == ["FA1", "FA1", "FA2", "FA3", "AV1"]
    assert rows[-1][0] == "TOTAL"
