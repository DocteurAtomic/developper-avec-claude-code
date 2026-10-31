"""Weekly payment reminders for accounting, grouped by reminder level.

Uses the same rule as `pachaplan unpaid --days 30`: an invoice issued 30 days
ago or more, not settled, whose next action starts with "send". Reads the
database read-only and sends nothing.

    uv run python .claude/skills/relances/scripts/relances.py [--today YYYY-MM-DD]
        [--db PATH] [--detail first|second|formal] [-o FILE]

Exit codes: 0 on success, 1 when a guard refuses to go on, 2 on a usage error.
"""

import argparse
import csv
import os
import sys
from datetime import date

from pachaplan import planning
from pachaplan.db import connect, resolve_path

WINDOW_DAYS = 30

# The next actions of `pachaplan unpaid` that are reminders, in sending order.
LEVELS = {
    "send first reminder": ("first", "first reminder"),
    "send second reminder": ("second", "second reminder"),
    "send formal notice": ("formal", "formal notice"),
}


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="relances", description=__doc__.splitlines()[0])
    parser.add_argument("--today", help="reference date (default: $PACHAPLAN_TODAY, then today)")
    parser.add_argument("--db", help="database (default: $PACHAPLAN_DB, then the data/ file)")
    parser.add_argument("--detail", choices=[key for key, _ in LEVELS.values()],
                        help="also list the invoices of one level")
    parser.add_argument("-o", "--output", help="write all the reminders to a new CSV file")
    args = parser.parse_args(argv)
    text = args.today or os.environ.get("PACHAPLAN_TODAY")
    try:
        args.today = planning.parse_day(text) if text else date.today()
    except ValueError:
        parser.error(f"invalid date {text!r}, expected YYYY-MM-DD")
    return args


def reminders(conn, today):
    """The invoices to remind, by level key, and the hand-overs to collections."""
    result = planning.unpaid_invoices(conn, today, WINDOW_DAYS)
    groups = {key: [] for key, _ in LEVELS.values()}
    handovers = 0
    for row in result["rows"]:
        action = row["action"]
        if action in LEVELS:
            groups[LEVELS[action][0]].append(row)
        elif action.startswith("send"):
            # A new kind of reminder in pachaplan: refuse rather than drop it.
            raise ValueError(f"unknown reminder action {action!r} on {row['invoice_code']}")
        elif action == "hand over to collections":
            handovers += 1
    return groups, handovers, result["cutoff"]


def main(argv=None):
    args = parse_args(argv)
    if args.output and os.path.exists(args.output):
        # Unlike `pachaplan export -o`, never overwrite a file.
        print(f"relances: {args.output} already exists, nothing written", file=sys.stderr)
        return 1
    try:
        conn = connect(resolve_path(args.db))
    except FileNotFoundError as exc:
        print(f"relances: {exc}", file=sys.stderr)
        return 1
    with conn:
        try:
            groups, handovers, cutoff = reminders(conn, args.today)
        except ValueError as exc:
            print(f"relances: {exc}", file=sys.stderr)
            return 1

    print(f"Reminders for {args.today.isoformat()} (invoices issued on or before {cutoff})")
    table = []
    for key, label in LEVELS.values():
        rows = groups[key]
        table.append((label, len(rows), planning.money(sum(r["balance"] for r in rows))))
    everything = [r for rows in groups.values() for r in rows]
    table.append(("total", len(everything), planning.money(sum(r["balance"] for r in everything))))
    planning.print_table(table, ["level", "invoices", "balance"])
    print(f"Not reminders: {handovers} invoice(s) to hand over to collections.")

    if args.detail:
        print()
        for r in groups[args.detail]:
            print(f"{r['invoice_code']};{r['invoice_date']};{r['days_late']};"
                  f"{r['customer']};{r['balance']:.2f}")

    if args.output:
        try:
            with open(args.output, "x", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["level", "invoice_code", "invoice_date", "days_late",
                                 "customer", "balance"])
                for key, _ in LEVELS.values():
                    for r in groups[key]:
                        writer.writerow([key, r["invoice_code"], r["invoice_date"],
                                         r["days_late"], r["customer"], f"{r['balance']:.2f}"])
        except FileExistsError:
            print(f"relances: {args.output} already exists, nothing written", file=sys.stderr)
            return 1
        print(f"{len(everything)} reminder(s) written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
