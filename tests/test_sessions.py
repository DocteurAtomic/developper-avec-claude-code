from conftest import TODAY

from pachaplan.planning import low_fill_sessions


def test_low_fill_lists_sessions_under_threshold(conn):
    rows = low_fill_sessions(conn, TODAY, 50)
    assert [r["session_id"] for r in rows] == [101]
    assert rows[0]["enrolled"] == 2
    assert rows[0]["fill_rate"] == 20.0


def test_low_fill_skips_canceled_and_beyond_horizon(conn):
    rows = low_fill_sessions(conn, TODAY, 100)
    assert sorted(r["session_id"] for r in rows) == [101, 102]
