"""Check the monthly export: its TOTAL line against the invoices in the database.

    uv run python .claude/skills/monthly-export/check_export.py YYYY-MM

Runs `pachaplan export --month YYYY-MM` in the current project, reads the gross
total on its TOTAL line, and compares it with the sum of the gross amounts of
the invoices of the month in data/pachaplan.sqlite (opened read-only).
Exit codes: 0 when they match, 1 when they differ, 2 when the check cannot run.
"""

import re
import sqlite3
import subprocess
import sys
from pathlib import Path

DB = Path("data") / "pachaplan.sqlite"
REFERENCE = (
    "SELECT printf('%.2f', SUM(gross_amount)) FROM invoice "
    "WHERE strftime('%Y-%m', invoice_date) = ?"
)


def export_total(month):
    """The last column of the TOTAL line of the export, as printed."""
    done = subprocess.run(
        [sys.executable, "-m", "pachaplan.cli", "--db", str(DB), "export", "--month", month],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        raise RuntimeError(f"pachaplan export exited with {done.returncode}: {done.stderr.strip()}")
    for line in done.stdout.splitlines():
        # csv.writer ends its lines with \r\n: strip it before reading the last column.
        if line.startswith("TOTAL,"):
            return line.rstrip("\r").split(",")[-1]
    raise RuntimeError("no TOTAL line in the export")


def reference_total(month):
    if not DB.exists():
        raise RuntimeError(f"database not found: {DB} (run from the project root)")
    conn = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
    try:
        value = conn.execute(REFERENCE, (month,)).fetchone()[0]
    finally:
        conn.close()
    return value or "0.00"


def main(argv):
    if len(argv) != 1 or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", argv[0]):
        print("usage: check_export.py YYYY-MM", file=sys.stderr)
        return 2
    month = argv[0]
    try:
        exported = export_total(month)
        expected = reference_total(month)
    except RuntimeError as exc:
        print(f"check_export: {exc}", file=sys.stderr)
        return 2
    status = "OK" if exported == expected else "DIFFERENT"
    print(f"{month}  export {exported}  invoices {expected}  {status}")
    return 0 if status == "OK" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
