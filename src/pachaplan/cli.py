"""Command line interface of pachaplan."""

import argparse
import os
import sys
from datetime import date

from . import __version__, planning
from .db import connect, resolve_path


def build_parser():
    parser = argparse.ArgumentParser(
        prog="pachaplan",
        description="Planning reports for the PachaData training team.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--db",
        help="path to the SQLite database (default: $PACHAPLAN_DB, then data/pachaplan.sqlite)",
    )
    parser.add_argument(
        "--today",
        type=planning.parse_day,
        default=None,
        help="reference date YYYY-MM-DD (default: $PACHAPLAN_TODAY, then the current date)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("sessions", help="upcoming sessions filled under a percentage")
    p.add_argument("--below", type=float, required=True, metavar="PCT",
                   help="fill rate threshold, in percent")

    p = sub.add_parser("trainers", help="trainers teaching on a given day")
    p.add_argument("--date", type=planning.parse_day, required=True, metavar="YYYY-MM-DD")

    p = sub.add_parser("unpaid", help="invoices still unpaid N days after they were issued")
    p.add_argument("--days", type=int, required=True, metavar="N")

    p = sub.add_parser("export", help="CSV export of the invoice lines of a month")
    p.add_argument("--month", required=True, metavar="YYYY-MM")
    p.add_argument("-o", "--output", help="write the CSV to this file instead of stdout")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    env_today = os.environ.get("PACHAPLAN_TODAY")
    today = args.today or (planning.parse_day(env_today) if env_today else date.today())
    try:
        conn = connect(resolve_path(args.db))
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    with conn:
        if args.command == "sessions":
            rows = planning.low_fill_sessions(conn, today, args.below)
            planning.print_low_fill(rows, args.below, today)
        elif args.command == "trainers":
            result = planning.assign_trainers(conn, args.date)
            planning.print_trainer_day(result)
        elif args.command == "unpaid":
            result = planning.unpaid_invoices(conn, today, args.days)
            planning.print_unpaid(result, args.days)
        elif args.command == "export":
            if args.output:
                with open(args.output, "w", newline="", encoding="utf-8") as f:
                    count, total = planning.export_month(conn, args.month, f)
                print(f"{count} lines written to {args.output}, total {total:.2f}")
            else:
                planning.export_month(conn, args.month, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
