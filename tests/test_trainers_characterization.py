"""Characterization tests of assign_trainers on the test database.

They pin what the function returns today, right or wrong, so that a refactoring
can be checked against it. They do not say the current output is correct: when
one of them fails, decide whether the change of behaviour is wanted before
updating the expected value.

The first tests use tests/fixture.sql as it is. The fixture has no warning
case, so the scenario tests add rows to the temporary copy of it (never to
fixture.sql itself) to reach every check of the trainer board.
"""

import sqlite3
from datetime import date

import pytest

from pachaplan.db import connect
from pachaplan.planning import assign_trainers

EMPTY_SUMMARY = {"in_house": 0, "sessions": 0, "trainers": 0, "travelling": 0}


def board_line(**fields):
    """A board line of the fixture, with the fields of session 101 by default."""
    line = {
        "session_id": 101,
        "course": "SQL-INTRO",
        "title": "SQL: getting started",
        "day": "1/2",
        "location": "Centre Pacha Paris",
        "city": "Paris",
        "room": "Codd",
        "status": "CONFIRMED",
        "trainer_id": 1,
        "trainer": "Julie Lambert",
        "home": "Paris",
        "travel": "no",
        "notes": [],
    }
    line.update(fields)
    return line


SESSION_102 = {
    "session_id": 102,
    "course": "SQL-TUNE",
    "title": "SQL: query tuning",
    "location": "Centre Pacha Lyon",
    "city": "Lyon",
    "room": "Date",
    "status": "OPEN",
    "trainer_id": 2,
    "trainer": "Paul Girard",
    "home": "Lyon",
}


# ---------------------------------------------------------------------------
# The fixture as it is
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "day, include_unconfirmed, board",
    [
        ("2026-11-10", True, [board_line(notes=["2 trainee(s)"])]),
        ("2026-11-10", False, [board_line(notes=["2 trainee(s)"])]),
        ("2026-11-11", True, [board_line(day="2/2")]),
        (
            "2026-11-12",
            True,
            [board_line(**SESSION_102, day="1/3", notes=["open", "3 trainee(s)"])],
        ),
        ("2026-11-12", False, []),
        ("2026-11-14", True, [board_line(**SESSION_102, day="3/3", notes=["open"])]),
        ("2026-11-14", False, []),
        (
            "2026-12-20",
            True,
            [board_line(session_id=104, status="PLANNED", notes=["planned", "0 trainee(s)"])],
        ),
        ("2026-12-20", False, []),
        # Before session 101, after session 102, canceled 103, completed 105.
        ("2026-11-09", True, []),
        ("2026-11-15", True, []),
        ("2026-11-16", True, []),
        ("2026-09-07", True, []),
    ],
)
def test_fixture_board(conn, day, include_unconfirmed, board):
    result = assign_trainers(conn, day, include_unconfirmed=include_unconfirmed)
    sessions = len(board)
    assert result == {
        "board": board,
        "warnings": [],
        "summary": {
            "day": day,
            "sessions": sessions,
            "trainers": sessions,
            "travelling": 0,
            "in_house": 0,
        },
    }


def test_fixture_default_includes_unconfirmed_sessions(conn):
    assert assign_trainers(conn, "2026-11-12") == assign_trainers(
        conn, "2026-11-12", include_unconfirmed=True
    )


def test_fixture_accepts_a_date_object(conn):
    assert assign_trainers(conn, date(2026, 11, 12)) == assign_trainers(conn, "2026-11-12")


def test_fixture_empty_day_summary(conn):
    assert assign_trainers(conn, "2026-11-09")["summary"] == {"day": "2026-11-09", **EMPTY_SUMMARY}


# ---------------------------------------------------------------------------
# Scenario: the fixture plus one busy day, 2026-12-01
# ---------------------------------------------------------------------------

SCENARIO = """
INSERT INTO company VALUES (2, 'Banque Morel', 'morel.example', 'FRA', NULL, 0, 'FR');
INSERT INTO contact VALUES (12, NULL, 'Bernard', NULL, NULL, NULL);
INSERT INTO location VALUES
  (43, 'Classe virtuelle', NULL, NULL, 'FRA', 0, '2020-01-01', NULL, 0);
INSERT INTO room VALUES (3, 43, 'Teams', 50, NULL), (4, 1, 'Boyce', 1, 0);
-- 3: no first name, do not contact, arrives after the day. 4: leaves on the day, no assignment.
INSERT INTO trainer VALUES
  (3, 12, 'E', 1, '2026-12-05', NULL),
  (4, 4, 'E', 0, '2020-01-01', '2026-12-01');
INSERT INTO assignment VALUES (3, 1, '2026-01-01', NULL);
-- 201: no trainer. 202: trainer 99 does not exist. 203 and 204: same room in Lyon.
-- 203: in-house for a company, with a remark, Paris trainer in Lyon.
-- 205 and 206: same virtual room. 207: no room, 3 days.
-- 208: in-house without company, NULL duration, 2 trainees for 1 seat. 209: canceled.
INSERT INTO session VALUES
  (201, 1, 'FR', 1, NULL, NULL, '2026-12-01', 2, 1500, NULL, 'CONFIRMED', 0, NULL, '2026-06-01'),
  (202, 1, 'FR', 2, 99, NULL, '2026-12-01', 2, 1500, NULL, 'CONFIRMED', 0, NULL, '2026-06-01'),
  (203, 1, 'FR', 2, 1, 2, '2026-12-01', 2, 1500, NULL, 'PLANNED', 1, 'Bring adapters.',
   '2026-06-01'),
  (204, 2, 'FR', 2, 2, NULL, '2026-11-30', 3, 2100, NULL, 'CONFIRMED', 0, NULL, '2026-06-01'),
  (205, 1, 'FR', 3, 3, NULL, '2026-12-01', 1, 1500, NULL, 'OPEN', 0, NULL, '2026-06-01'),
  (206, 1, 'FR', 3, 1, NULL, '2026-12-01', 1, 1500, NULL, 'CONFIRMED', 0, NULL, '2026-06-01'),
  (207, 2, 'FR', NULL, 4, NULL, '2026-11-30', 3, 2100, NULL, 'CONFIRMED', 0, NULL, '2026-06-01'),
  (208, 1, 'FR', 4, 2, NULL, '2026-12-01', NULL, 1500, NULL, 'CONFIRMED', 1, NULL, '2026-06-01'),
  (209, 1, 'FR', 1, 1, NULL, '2026-12-01', 2, 1500, NULL, 'CANCELED', 0, NULL, '2026-06-01');
-- 208: two active enrollments, one on the waiting list, one canceled.
INSERT INTO enrollment VALUES
  (20, 208, 1, '2026-10-01 10:00:00', NULL, 0, 0, 0, NULL),
  (21, 208, 2, '2026-10-01 10:00:00', NULL, 0, 0, 0, NULL),
  (22, 208, 3, '2026-10-01 10:00:00', NULL, 0, 0, 1, NULL),
  (23, 208, 4, '2026-10-01 10:00:00', '2026-10-15', 0, 0, 0, NULL);
"""


@pytest.fixture
def scenario(db_path):
    # Plain sqlite3 connection, without foreign keys, so that trainer 99 can be referenced.
    raw = sqlite3.connect(db_path)
    raw.executescript(SCENARIO)
    raw.close()
    c = connect(db_path)
    yield c
    c.close()


LINE_201 = board_line(session_id=201, trainer_id=None, trainer="(none)", home="", travel="")
LINE_202 = board_line(
    session_id=202,
    location="Centre Pacha Lyon",
    city="Lyon",
    room="Date",
    trainer_id=99,
    trainer="#99",
    home="",
    travel="",
)
LINE_203 = board_line(
    session_id=203,
    location="Centre Pacha Lyon",
    city="Lyon",
    room="Date",
    status="PLANNED",
    travel="yes",
    notes=["in-house: Banque Morel", "planned", "0 trainee(s)", "Bring adapters."],
)
LINE_204 = board_line(**{**SESSION_102, "session_id": 204, "status": "CONFIRMED", "day": "2/3"})
LINE_205 = board_line(
    session_id=205,
    day="1/1",
    location="Classe virtuelle",
    city="",
    room="Teams",
    status="OPEN",
    trainer_id=3,
    trainer="Bernard",
    travel="remote",
    notes=["do not contact", "open", "0 trainee(s)"],
)
LINE_206 = board_line(
    session_id=206,
    day="1/1",
    location="Classe virtuelle",
    city="",
    room="Teams",
    travel="remote",
    notes=["0 trainee(s)"],
)
LINE_207 = board_line(
    session_id=207,
    course="SQL-TUNE",
    title="SQL: query tuning",
    day="2/3",
    location="",
    city="",
    room="",
    trainer_id=4,
    trainer="Hugo Fabre",
    home="?",
    travel="",
    notes=["no room"],
)
LINE_208 = board_line(
    session_id=208,
    day="1/1",
    room="Boyce",
    trainer_id=2,
    trainer="Paul Girard",
    home="Lyon",
    travel="yes",
    notes=["in-house", "2 trainee(s)"],
)


def test_scenario_busy_day(scenario):
    assert assign_trainers(scenario, "2026-12-01") == {
        "board": [LINE_202, LINE_201, LINE_205, LINE_207, LINE_203, LINE_206, LINE_204, LINE_208],
        "warnings": [
            "session 207: Hugo Fabre leaves on 2026-12-01, before the end of the session "
            "(2026-12-02)",
            "session 207: Hugo Fabre has no home location",
            "session 205: Bernard only starts on 2026-12-05",
            "session 202: unknown trainer 99",
            "trainer Julie Lambert assigned to sessions 206 and 203",
            "room Date (Centre Pacha Lyon) booked by sessions 204 and 203",
            "session 201: no trainer assigned",
            "trainer Paul Girard assigned to sessions 204 and 208",
            "session 208: 2 trainees for 1 seats in room Boyce",
        ],
        "summary": {
            "day": "2026-12-01",
            "sessions": 8,
            "trainers": 4,
            "travelling": 2,
            "in_house": 2,
        },
    }


def test_scenario_busy_day_confirmed_only(scenario):
    assert assign_trainers(scenario, "2026-12-01", include_unconfirmed=False) == {
        "board": [LINE_202, LINE_201, LINE_207, LINE_206, LINE_204, LINE_208],
        "warnings": [
            "session 207: Hugo Fabre leaves on 2026-12-01, before the end of the session "
            "(2026-12-02)",
            "session 207: Hugo Fabre has no home location",
            "session 202: unknown trainer 99",
            "session 201: no trainer assigned",
            "trainer Paul Girard assigned to sessions 204 and 208",
            "session 208: 2 trainees for 1 seats in room Boyce",
        ],
        "summary": {
            "day": "2026-12-01",
            "sessions": 6,
            "trainers": 3,
            "travelling": 1,
            "in_house": 1,
        },
    }


def test_scenario_next_day(scenario):
    assert assign_trainers(scenario, "2026-12-02") == {
        "board": [
            {**LINE_202, "day": "2/2"},
            {**LINE_201, "day": "2/2"},
            {**LINE_207, "day": "3/3"},
            {
                **LINE_203,
                "day": "2/2",
                "notes": ["in-house: Banque Morel", "planned", "Bring adapters."],
            },
            {**LINE_204, "day": "3/3"},
        ],
        "warnings": [
            "session 207: Hugo Fabre leaves on 2026-12-01, before the end of the session "
            "(2026-12-02)",
            "session 207: Hugo Fabre has no home location",
            "session 202: unknown trainer 99",
            "room Date (Centre Pacha Lyon) booked by sessions 204 and 203",
            "session 201: no trainer assigned",
        ],
        "summary": {
            "day": "2026-12-02",
            "sessions": 5,
            "trainers": 3,
            "travelling": 1,
            "in_house": 1,
        },
    }
