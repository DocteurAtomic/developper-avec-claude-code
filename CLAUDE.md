# pachaplan

CLI of the PachaData planning team. Python 3.13, managed by `uv`. Always run the tool
as `uv run pachaplan ...`; global options (`--db`, `--today`) go before the subcommand.

## Commands

- Full test suite: `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q`, 13 tests.
  Without the variable, `tests/test_integration.py` is skipped and pytest still exits 0
  (seen on 2026-11-02: eight tests announced, seven passed, one skipped). Report the
  passed and skipped counts, never "all tests pass" alone.
- Lint: `uv run ruff check`. It exits 1 today with 4 known errors (F401, two E501,
  B006); CI runs it with `--exit-zero`. Do not fix them unless asked.

## Data

- `data/pachaplan.sqlite` is never written. `db.py` opens it read-only; anything that
  writes takes a copy passed with `--db`.
- Unit tests build their own database from `tests/fixture.sql`.

## Conventions

- Code, comments and commit messages are in English, even when the request is in French.
