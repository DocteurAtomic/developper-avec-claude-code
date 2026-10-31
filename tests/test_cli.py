import os
import subprocess
import sys

import pytest

from pachaplan.cli import main


def test_cli_sessions_lists_low_fill_sessions(db_path):
    # Run in a subprocess: print_low_fill binds sys.stdout as a default argument at
    # import time, so capsys and capfd never see what it prints.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pachaplan.cli",
            "--db",
            str(db_path),
            "--today",
            "2026-11-02",
            "sessions",
            "--below",
            "50",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.splitlines()
    rows = [line.split() for line in lines if line[:3].isdigit()]
    assert rows == [
        [
            "101",
            "2026-11-10",
            "8",
            "SQL:",
            "getting",
            "started",
            "Paris",
            "Julie",
            "Lambert",
            "CONFIRMED",
            "2/10",
            "20%",
        ],
    ]
    assert lines[-1] == "1 session(s) under 50.0% between 2026-11-02 and 2026-12-02."


@pytest.mark.parametrize("month", ["2026-13", "2026-00", "2026", "abcd-ef", "2026-1-1"])
def test_cli_export_rejects_invalid_month(db_path, capsys, month):
    with pytest.raises(SystemExit) as exc:
        main(["--db", str(db_path), "export", "--month", month])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert err.strip().splitlines()[-1] == (
        f"pachaplan export: error: argument --month: invalid month '{month}', expected YYYY-MM"
    )


@pytest.mark.parametrize(
    "option,args",
    [
        ("--date", ["trainers", "--date", "2026-11-31"]),
        ("--today", ["--today", "2026-11-31", "sessions", "--below", "50"]),
    ],
)
def test_cli_rejects_invalid_date(db_path, capsys, option, args):
    with pytest.raises(SystemExit) as exc:
        main(["--db", str(db_path), *args])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert (
        err.strip()
        .splitlines()[-1]
        .endswith(f"error: argument {option}: invalid date '2026-11-31', expected YYYY-MM-DD")
    )


def test_cli_export_accepts_valid_month(db_path, capsys):
    assert main(["--db", str(db_path), "export", "--month", "2026-12"]) == 0
    assert capsys.readouterr().out.splitlines()[0].startswith("invoice_code")


@pytest.mark.parametrize(
    "args",
    [
        ["unpaid", "--days", "30"],
        ["sessions", "--below", "50"],
        ["trainers", "--date", "2026-11-10"],
        ["export", "--month", "2026-11"],
    ],
)
def test_cli_exits_quietly_when_stdout_is_closed(db_path, args):
    # The planning team reads reports with `pachaplan unpaid --days 30 | head`: once
    # head exits, writing to stdout raised BrokenPipeError with a traceback. Closing the
    # read end before the process starts reproduces this deterministically.
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pachaplan.cli", "--db", str(db_path), "--today", "2026-11-02"]
            + args,
            stdout=write_fd,
            stderr=subprocess.PIPE,
            text=True,
        )
    finally:
        os.close(write_fd)
    assert result.stderr == ""
    assert result.returncode == 0


@pytest.mark.parametrize("value", ["02/11/2026", "11/02/26", "2026-11-31"])
def test_cli_rejects_invalid_env_today(db_path, capsys, monkeypatch, value):
    # The planning team's script used PACHAPLAN_TODAY=$(date +%x), which follows the
    # locale (02/11/2026 in fr_FR) and crashed with a traceback.
    monkeypatch.setenv("PACHAPLAN_TODAY", value)
    with pytest.raises(SystemExit) as exc:
        main(["--db", str(db_path), "sessions", "--below", "50"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert (
        err.strip()
        .splitlines()[-1]
        .endswith(f"error: invalid PACHAPLAN_TODAY {value!r}, expected YYYY-MM-DD")
    )
