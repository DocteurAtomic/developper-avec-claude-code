from pachaplan.cli import main


def test_cli_sessions_runs_without_error(db_path, capsys):
    main(["--db", str(db_path), "--today", "2026-11-02", "sessions", "--below", "50"])
    out = capsys.readouterr().out
    assert "Error" not in out
