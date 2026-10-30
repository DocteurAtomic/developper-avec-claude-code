import io

from conftest import TODAY

from pachaplan.db import connect
from pachaplan.planning import low_fill_sessions, print_low_fill


def test_low_fill_lists_sessions_under_threshold(conn):
    rows = low_fill_sessions(conn, TODAY, 50)
    assert [r["session_id"] for r in rows] == [101]
    assert rows[0]["enrolled"] == 2
    assert rows[0]["fill_rate"] == 20.0


def test_low_fill_skips_canceled_and_beyond_horizon(conn):
    rows = low_fill_sessions(conn, TODAY, 100)
    assert sorted(r["session_id"] for r in rows) == [101, 102]


def test_low_fill_shows_the_trainer_after_the_city(conn):
    rows = low_fill_sessions(conn, TODAY, 100)
    assert {r["session_id"]: r["trainer"] for r in rows} == {
        101: "Julie Lambert",
        102: "Paul Girard",
    }
    out = io.StringIO()
    print_low_fill(rows, 100, TODAY, out)
    headers = out.getvalue().splitlines()[0].split()
    assert headers[headers.index("city") + 1] == "trainer"


def test_low_fill_marks_a_session_without_trainer(db_path):
    writable = connect(db_path, readonly=False)
    writable.execute("UPDATE session SET trainer_id = NULL WHERE session_id = 102")
    writable.commit()
    writable.close()
    conn = connect(db_path)
    rows = low_fill_sessions(conn, TODAY, 100)
    conn.close()
    assert {r["session_id"]: r["trainer"] for r in rows} == {
        101: "Julie Lambert",
        102: "(none)",
    }
