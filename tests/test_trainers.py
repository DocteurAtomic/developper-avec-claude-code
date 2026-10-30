import sqlite3

from pachaplan.db import connect
from pachaplan.planning import assign_trainers


def test_trainer_board_lists_sessions_of_the_day(conn):
    result = assign_trainers(conn, "2026-11-11")
    board = result["board"]
    assert [b["session_id"] for b in board] == [101]
    assert board[0]["trainer"] == "Julie Lambert"
    assert board[0]["day"] == "2/2"
    assert board[0]["travel"] == "no"
    assert result["warnings"] == []


def test_trainer_board_warns_about_overlapping_sessions_of_a_trainer(db_path):
    # Session 301 gives Julie Lambert (trainer 1) a second session in Lyon on
    # 2026-11-11, the second day of her session 101 in Paris. Other room, so
    # the room check does not fire. Rows go into the temporary copy only.
    raw = sqlite3.connect(db_path)
    raw.execute(
        "INSERT INTO session VALUES (301, 1, 'FR', 2, 1, NULL, '2026-11-11', 2, 1500, "
        "NULL, 'CONFIRMED', 0, NULL, '2026-06-01')"
    )
    raw.commit()
    raw.close()

    conn = connect(db_path)
    try:
        result = assign_trainers(conn, "2026-11-11")
    finally:
        conn.close()

    assert sorted(b["session_id"] for b in result["board"]) == [101, 301]
    overlaps = [w for w in result["warnings"] if "101" in w and "301" in w]
    assert overlaps, f"no warning about sessions 101 and 301, got {result['warnings']}"
