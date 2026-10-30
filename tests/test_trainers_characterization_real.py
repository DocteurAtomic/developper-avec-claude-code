"""Characterization tests of assign_trainers on the real database. Set PACHAPLAN_DB to run them.

Each snapshot in tests/snapshots/assign_trainers/ is what the function returned
for data/pachaplan.sqlite on that day, right or wrong, when the snapshot was
written. A failure means the output changed: decide whether the change is
wanted before rewriting the snapshot.
"""

import json
import os
from pathlib import Path

import pytest

from pachaplan.db import connect
from pachaplan.planning import assign_trainers

SNAPSHOTS = Path(__file__).with_name("snapshots") / "assign_trainers"

# 2026-10-20: confirmed and open sessions, in-house, remarks, travel yes/no/remote.
# 2026-11-17: the same mix a month later.
# 2027-02-16: mostly planned sessions, a single confirmed one.
DAYS = ["2026-10-20", "2026-11-17", "2027-02-16"]


@pytest.fixture(scope="module")
def real_conn():
    path = os.environ.get("PACHAPLAN_DB")
    if not path:
        pytest.skip("PACHAPLAN_DB is not set")
    c = connect(path)
    yield c
    c.close()


@pytest.mark.parametrize("include_unconfirmed, tag", [(True, "all"), (False, "confirmed")])
@pytest.mark.parametrize("day", DAYS)
def test_trainer_board_matches_snapshot(real_conn, day, include_unconfirmed, tag):
    snapshot = SNAPSHOTS / f"{day}_{tag}.json"
    expected = json.loads(snapshot.read_text(encoding="utf-8"))
    assert assign_trainers(real_conn, day, include_unconfirmed=include_unconfirmed) == expected
