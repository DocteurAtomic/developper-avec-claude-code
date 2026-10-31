import sqlite3
from datetime import date
from pathlib import Path

import pytest

from pachaplan.db import connect

FIXTURE = Path(__file__).with_name("fixture.sql")
TODAY = date(2026, 11, 2)


def pytest_addoption(parser):
    parser.addoption(
        "--fail-on-skip",
        action="store_true",
        help="exit with an error if any test is skipped (used by the CI)",
    )


def pytest_sessionfinish(session, exitstatus):
    """With --fail-on-skip, turn a run with skipped tests into a failed run."""
    if not session.config.getoption("fail_on_skip"):
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    skipped = len(reporter.stats.get("skipped", [])) if reporter else 0
    if skipped and exitstatus == pytest.ExitCode.OK:
        print(f"\n--fail-on-skip: {skipped} test(s) skipped, failing the run")
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


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
