"""Command line interface of pachaplan."""

import argparse
import os
import sys
from datetime import date

from . import __version__, planning
from .db import connect, resolve_path


def month_arg(text):
    """Argparse type for --month: validate YYYY-MM, keep the text unchanged."""
    try:
        planning.parse_month(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid month {text!r}, expected YYYY-MM") from None
    return text


def day_arg(text):
    """Argparse type for --date and --today: parse YYYY-MM-DD into a date."""
    try:
        return planning.parse_day(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date {text!r}, expected YYYY-MM-DD") from None


def is_same_file(a, b):
    """True if both paths name the same existing file (symlinks and hard links included)."""
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


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
        type=day_arg,
        default=None,
        help="reference date YYYY-MM-DD (default: $PACHAPLAN_TODAY, then the current date)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("sessions", help="upcoming sessions filled under a percentage")
    p.add_argument(
        "--below", type=float, required=True, metavar="PCT", help="fill rate threshold, in percent"
    )

    p = sub.add_parser("trainers", help="trainers teaching on a given day")
    p.add_argument("--date", type=day_arg, required=True, metavar="YYYY-MM-DD")

    p = sub.add_parser("unpaid", help="invoices still unpaid N days after they were issued")
    p.add_argument("--days", type=int, required=True, metavar="N")

    p = sub.add_parser("export", help="CSV export of the invoice lines of a month")
    p.add_argument("--month", type=month_arg, required=True, metavar="YYYY-MM")
    p.add_argument("-o", "--output", help="write the CSV to this file instead of stdout")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    today = args.today
    if today is None:
        env_today = os.environ.get("PACHAPLAN_TODAY")
        if env_today:
            try:
                today = planning.parse_day(env_today)
            except ValueError:
                parser.error(f"invalid PACHAPLAN_TODAY {env_today!r}, expected YYYY-MM-DD")
        else:
            today = date.today()
    db_path = resolve_path(args.db)
    if args.command == "export" and args.output and is_same_file(args.output, db_path):
        # open(..., "w") would truncate the database before it is even read.
        parser.error(f"argument -o/--output: {args.output} is the database being read")
    try:
        conn = connect(db_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        run_command(args, conn, today)
        sys.stdout.flush()
    except BrokenPipeError:
        # The reader of stdout exited early, e.g. `pachaplan unpaid --days 30 | head`.
        # Redirect stdout to devnull so the interpreter's final flush does not fail again.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
    return 0


def run_command(args, conn, today):
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


if __name__ == "__main__":
    sys.exit(main())
