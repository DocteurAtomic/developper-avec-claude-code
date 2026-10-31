# pachaplan

CLI of the PachaData planning team. Python 3.13, managed by `uv`. Always run the tool
as `uv run pachaplan ...`; global options (`--db`, `--today`) go before the subcommand.

## Commands

- Full test suite: `PACHAPLAN_DB=data/pachaplan.sqlite uv run pytest -q`, 51 tests.
  Without the variable, `tests/test_integration.py` and
  `tests/test_trainers_characterization_real.py` are skipped and pytest still exits 0
  (43 passed, 8 skipped; seen on 2026-11-02 with an older suite: eight tests announced,
  seven passed, one skipped). Report the
  passed and skipped counts, never "all tests pass" alone.
- CI runs `uv run pytest -q --fail-on-skip` with `PACHAPLAN_DB` set: a skipped test
  fails the build. The option is defined in `tests/conftest.py`.
- Lint: `uv run ruff check`. It exits 0 and CI fails the build on any lint error.
  Fix new errors in the code; do not add `noqa` or ignore rules in `pyproject.toml`.

## Data

- `data/pachaplan.sqlite` is never written. `db.py` opens it read-only; anything that
  writes takes a copy passed with `--db`.
- Unit tests build their own database from `tests/fixture.sql`.

## Conventions

- Code, comments and commit messages are in English, even when the request is in French.

## Reporting

- End every task with three short lists: what succeeded, what failed, and what was not
  run or not checked. Give the command behind each item. "Not run" is never empty by
  default: say what you could not check from here.
