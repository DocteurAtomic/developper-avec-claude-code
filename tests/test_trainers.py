from pachaplan.planning import assign_trainers


def test_trainer_board_lists_sessions_of_the_day(conn):
    result = assign_trainers(conn, "2026-11-11")
    board = result["board"]
    assert [b["session_id"] for b in board] == [101]
    assert board[0]["trainer"] == "Julie Lambert"
    assert board[0]["day"] == "2/2"
    assert board[0]["travel"] == "no"
    assert result["warnings"] == []
