"""Acceptance tests for `pachaplan cancel-candidates`. Copy this file into tests/.

The planning team's rules: sessions starting between the reference date and 15 days
later, both included, not canceled, filled strictly under 40 % (active enrollments over
the seats of the course), sorted by start date then session id. One line per session,
`session_id;start_date;title;enrolled;seats`, and nothing else on stdout.
"""

import subprocess
import sys

from pachaplan.db import connect


def run(db_path, today="2026-11-02"):
    """Run the real command line, in a separate process, and return its stdout lines."""
    result = subprocess.run(
        [sys.executable, "-m", "pachaplan.cli", "--db", str(db_path), "--today", today,
         "cancel-candidates"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.splitlines()


def add_session(db_path, session_id, start, status="OPEN", enrolled=0, course_id=1):
    conn = connect(db_path, readonly=False)
    conn.execute(
        "INSERT INTO session VALUES (?, ?, 'FR', 1, 1, NULL, ?, 2, 1500, NULL, ?, 0, NULL,"
        " '2026-06-01')",
        (session_id, course_id, start, status),
    )
    for n in range(enrolled):
        conn.execute(
            "INSERT INTO enrollment VALUES (?, ?, 1, '2026-09-01 10:00:00', NULL, 0, 0, 0, NULL)",
            (1000 * session_id + n, session_id),
        )
    conn.commit()
    conn.close()


def test_fixture_has_one_candidate(db_path):
    # 101: 2 active enrollments out of 10 (the canceled one does not count).
    # 102 is at 75 %, 103 is canceled, 104 starts beyond 15 days, 105 is past.
    assert run(db_path) == ["101;2026-11-10;SQL: getting started;2;10"]


def test_fifteenth_day_is_included_and_sixteenth_is_not(db_path):
    add_session(db_path, 201, "2026-11-17")
    add_session(db_path, 202, "2026-11-18")
    ids = [line.split(";")[0] for line in run(db_path)]
    assert "201" in ids
    assert "202" not in ids


def test_forty_percent_is_not_under_forty(db_path):
    add_session(db_path, 203, "2026-11-05", enrolled=4)  # 4 out of 10: 40 %
    add_session(db_path, 204, "2026-11-05", enrolled=3)  # 3 out of 10: 30 %
    lines = run(db_path)
    assert "204;2026-11-05;SQL: getting started;3;10" in lines
    assert not [line for line in lines if line.startswith("203;")]


def test_canceled_and_past_sessions_are_left_out(db_path):
    add_session(db_path, 205, "2026-11-03", status="CANCELED")
    add_session(db_path, 206, "2026-11-01")
    ids = [line.split(";")[0] for line in run(db_path)]
    assert "205" not in ids
    assert "206" not in ids


def test_sorted_by_start_date_then_session_id(db_path):
    add_session(db_path, 302, "2026-11-04")
    add_session(db_path, 301, "2026-11-04")
    add_session(db_path, 300, "2026-11-12", course_id=2)
    ids = [line.split(";")[0] for line in run(db_path)]
    assert ids == ["301", "302", "101", "300"]
