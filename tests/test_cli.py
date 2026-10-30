import pytest

from pachaplan.cli import main


def test_cli_sessions_runs_without_error(db_path, capsys):
    main(["--db", str(db_path), "--today", "2026-11-02", "sessions", "--below", "50"])
    out = capsys.readouterr().out
    assert "Error" not in out


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


@pytest.mark.parametrize("option,args", [
    ("--date", ["trainers", "--date", "2026-11-31"]),
    ("--today", ["--today", "2026-11-31", "sessions", "--below", "50"]),
])
def test_cli_rejects_invalid_date(db_path, capsys, option, args):
    with pytest.raises(SystemExit) as exc:
        main(["--db", str(db_path), *args])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert err.strip().splitlines()[-1].endswith(
        f"error: argument {option}: invalid date '2026-11-31', expected YYYY-MM-DD"
    )


def test_cli_export_accepts_valid_month(db_path, capsys):
    assert main(["--db", str(db_path), "export", "--month", "2026-12"]) == 0
    assert capsys.readouterr().out.splitlines()[0].startswith("invoice_code")
