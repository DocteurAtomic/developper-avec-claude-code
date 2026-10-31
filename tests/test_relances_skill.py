"""Tests of the script of the `relances` skill (.claude/skills/relances)."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / ".claude" / "skills" / "relances" / "scripts" / "relances.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--today", "2026-11-02", *args],
        capture_output=True,
        text=True,
    )


def test_relances_groups_the_reminders_by_level(db_path):
    result = run("--db", str(db_path), "--detail", "second")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "Reminders for 2026-11-02 (invoices issued on or before 2026-10-03)"
    second = next(line for line in lines if line.startswith("second reminder"))
    assert second.split() == ["second", "reminder", "1", "600.00"]
    total = next(line for line in lines if line.startswith("total"))
    assert total.split() == ["total", "1", "600.00"]
    assert lines[-1] == "FA2;2026-09-15;18;Hugo Fabre;600.00"


def test_relances_never_overwrites_a_file(db_path, tmp_path):
    target = tmp_path / "relances.csv"
    target.write_text("keep me\n", encoding="utf-8")
    result = run("--db", str(db_path), "-o", str(target))
    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert target.read_text(encoding="utf-8") == "keep me\n"


def test_relances_refuses_an_unknown_reminder_action(conn, monkeypatch):
    spec = importlib.util.spec_from_file_location("relances_script", SCRIPT)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    fake = {"rows": [{"invoice_code": "FA9", "action": "send final warning"}], "cutoff": "x"}
    monkeypatch.setattr(script.planning, "unpaid_invoices", lambda *args: fake)
    with pytest.raises(ValueError, match="send final warning"):
        script.reminders(conn, None)
