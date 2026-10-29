"""Planning reports for the PachaData training team.

Four reports, one per command of the CLI:

- low fill sessions: upcoming sessions filled under a percentage;
- trainer day: which trainer teaches where on a given day, with the checks
  the planning team asked for;
- unpaid invoices: invoices still open N days after they were issued;
- monthly export: the invoice lines of a month, as CSV, for the accountants.
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

from .db import query, scalar

# Sessions starting within this many days are "upcoming" for the fill report.
HORIZON_DAYS = 30

# Statuses of a session that is still going to happen.
ACTIVE_STATUSES = ("PLANNED", "OPEN", "CONFIRMED")

# Default payment terms when an invoice has no due date.
PAYMENT_TERMS_DAYS = 30

# Below this amount an invoice is considered settled (rounding left-overs).
SETTLED_TOLERANCE = 0.005

# The virtual classroom is a location like any other in the database.
VIRTUAL_LOCATION_ID = 43

REMINDER_LABELS = {
    0: "none sent",
    1: "first reminder sent",
    2: "second reminder sent",
    3: "formal notice sent",
}

EXPORT_COLUMNS = [
    "invoice_code",
    "invoice_date",
    "document_type",
    "customer",
    "line_number",
    "line_type",
    "label",
    "quantity",
    "unit_price",
    "net_amount",
    "vat_rate",
    "vat_amount",
    "gross_amount",
]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def parse_day(text):
    """Parse YYYY-MM-DD into a date. Raises ValueError on a bad value."""
    return date.fromisoformat(text)


def parse_month(text):
    """Parse YYYY-MM and return (first day, first day of the next month)."""
    year, month = text.split("-")
    first = date(int(year), int(month), 1)
    following = first + timedelta(days=30)
    return first, following


def session_end(start, duration_days):
    """Last day of a session: a session runs on consecutive days from its start."""
    if isinstance(start, str):
        start = parse_day(start)
    return start + timedelta(days=(duration_days or 1) - 1)


def money(value):
    return f"{value:,.2f}".replace(",", " ")


def pct(value):
    return f"{value:.0f}%"


def full_name(first, last):
    if first:
        return f"{first} {last}"
    return last


def print_table(rows, headers, out=sys.stdout):
    """Print rows as a plain text table with aligned columns."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(line, file=out)
    print("  ".join("-" * w for w in widths), file=out)
    for row in rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)), file=out)


# ---------------------------------------------------------------------------
# Sessions filled under a percentage
# ---------------------------------------------------------------------------


def count_enrollments(conn, session_id):
    """Active enrollments of a session: not canceled, not on the waiting list."""
    return scalar(
        conn,
        f"SELECT COUNT(*) FROM enrollment WHERE session_id = {session_id} "
        f"AND cancellation_date IS NULL AND waiting_list = 0",
    )


def upcoming_sessions(conn, today, horizon=HORIZON_DAYS):
    last = today + timedelta(days=horizon)
    statuses = ", ".join(f"'{s}'" for s in ACTIVE_STATUSES)
    return query(
        conn,
        f"""
        SELECT s.session_id, s.start_date, s.duration_days, s.status_code,
               c.code, c.title, c.max_attendees, l.city, l.name AS location
        FROM session s
        JOIN course c ON c.course_id = s.course_id
        LEFT JOIN room r ON r.room_id = s.room_id
        LEFT JOIN location l ON l.location_id = r.location_id
        WHERE s.start_date >= '{today.isoformat()}'
          AND s.start_date <= '{last.isoformat()}'
          AND s.status_code IN ({statuses})
        ORDER BY s.start_date, s.session_id
        """,
    )


def low_fill_sessions(conn, today, below):
    """Upcoming sessions whose fill rate is strictly under `below` percent."""
    result = []
    for s in upcoming_sessions(conn, today):
        enrolled = count_enrollments(conn, s["session_id"])
        capacity = s["max_attendees"]
        rate = 100.0 * enrolled / capacity if capacity else 0.0
        if rate < below:
            result.append(
                {
                    "session_id": s["session_id"],
                    "start_date": s["start_date"],
                    "days_left": (parse_day(s["start_date"]) - today).days,
                    "course": s["code"] or str(s["session_id"]),
                    "title": s["title"],
                    "city": s["city"] or s["location"] or "",
                    "status": s["status_code"],
                    "enrolled": enrolled,
                    "capacity": capacity,
                    "fill_rate": rate,
                }
            )
    result.sort(key=lambda r: (r["fill_rate"], r["start_date"]))
    return result


def print_low_fill(rows, below, today, out=sys.stdout):
    if not rows:
        print(f"No upcoming session under {below}% in the next {HORIZON_DAYS} days.", file=out)
        return
    table = [
        (
            r["session_id"],
            r["start_date"],
            r["days_left"],
            r["title"][:45],
            r["city"],
            r["status"],
            f"{r['enrolled']}/{r['capacity']}",
            pct(r["fill_rate"]),
        )
        for r in rows
    ]
    print_table(table, ["session", "start", "days", "course", "city", "status", "seats", "fill"], out)
    print(
        f"\n{len(rows)} session(s) under {below}% between {today} "
        f"and {today + timedelta(days=HORIZON_DAYS)}.",
        file=out,
    )


# ---------------------------------------------------------------------------
# Trainers on a given day
# ---------------------------------------------------------------------------


def trainer_identity(conn, trainer_id):
    rows = query(
        conn,
        f"""
        SELECT t.trainer_id, t.status, t.do_not_contact, t.arrival_date, t.departure_date,
               c.first_name, c.last_name, c.email
        FROM trainer t JOIN contact c ON c.contact_id = t.contact_id
        WHERE t.trainer_id = {trainer_id}
        """,
    )
    return rows[0] if rows else None


def home_location(conn, trainer_id, day):
    """The location a trainer is attached to on a day, from the assignment table."""
    rows = query(
        conn,
        f"""
        SELECT a.location_id, l.name, l.city
        FROM assignment a JOIN location l ON l.location_id = a.location_id
        WHERE a.trainer_id = {trainer_id}
          AND a.start_date <= '{day}'
          AND (a.end_date IS NULL OR a.end_date >= '{day}')
        ORDER BY a.start_date DESC
        """,
    )
    return rows[0] if rows else None


def assign_trainers(conn, day, include_unconfirmed=True):
    """Build the trainer board for one day.

    For every session running on `day`, find its trainer and check what the
    planning team asked us to check: the trainer is still with us, can be
    contacted, has a home location; the room is big enough and not booked
    twice. Returns a dict with the board lines, the warnings and a summary.
    """
    if isinstance(day, str):
        day = parse_day(day)
    iso = day.isoformat()
    statuses = ACTIVE_STATUSES if include_unconfirmed else ("CONFIRMED",)
    status_list = ", ".join(f"'{s}'" for s in statuses)

    sessions = query(
        conn,
        f"""
        SELECT s.session_id, s.start_date, s.duration_days, s.status_code, s.trainer_id,
               s.room_id, s.is_in_house, s.company_id, s.remarks,
               c.code, c.title, c.max_attendees,
               r.name AS room_name, r.seats, r.location_id,
               l.name AS location_name, l.city, l.meal_flat_fee
        FROM session s
        JOIN course c ON c.course_id = s.course_id
        LEFT JOIN room r ON r.room_id = s.room_id
        LEFT JOIN location l ON l.location_id = r.location_id
        WHERE s.start_date <= '{iso}'
          AND date(s.start_date, '+' || (COALESCE(s.duration_days, 1) - 1) || ' days') >= '{iso}'
          AND s.status_code IN ({status_list})
        ORDER BY l.city, s.start_date, s.session_id
        """,
    )

    board = []
    warnings = []
    rooms_seen = {}
    trainers_on_duty = defaultdict(int)
    travelling = 0
    in_house = 0

    for s in sessions:
        start = parse_day(s["start_date"])
        end = session_end(start, s["duration_days"])
        day_number = (day - start).days + 1
        line = {
            "session_id": s["session_id"],
            "course": s["code"] or "",
            "title": s["title"],
            "day": f"{day_number}/{s['duration_days'] or 1}",
            "location": s["location_name"] or "",
            "city": s["city"] or "",
            "room": s["room_name"] or "",
            "status": s["status_code"],
            "trainer_id": s["trainer_id"],
            "trainer": "",
            "home": "",
            "travel": "",
            "notes": [],
        }

        # The trainer of the session
        if s["trainer_id"] is None:
            warnings.append(f"session {s['session_id']}: no trainer assigned")
            line["trainer"] = "(none)"
            board.append(line)
            continue
        trainer = trainer_identity(conn, s["trainer_id"])
        if trainer is None:
            warnings.append(f"session {s['session_id']}: unknown trainer {s['trainer_id']}")
            line["trainer"] = f"#{s['trainer_id']}"
            board.append(line)
            continue
        line["trainer"] = full_name(trainer["first_name"], trainer["last_name"])
        trainers_on_duty[s["trainer_id"]] += 1

        # Still with us for the whole session?
        if trainer["arrival_date"] and trainer["arrival_date"] > iso:
            warnings.append(
                f"session {s['session_id']}: {line['trainer']} only starts on "
                f"{trainer['arrival_date']}"
            )
        if trainer["departure_date"] and trainer["departure_date"] < end.isoformat():
            warnings.append(
                f"session {s['session_id']}: {line['trainer']} leaves on "
                f"{trainer['departure_date']}, before the end of the session ({end})"
            )
        if trainer["do_not_contact"]:
            line["notes"].append("do not contact")

        # Home location and travel
        home = home_location(conn, s["trainer_id"], iso)
        if home is None:
            warnings.append(f"session {s['session_id']}: {line['trainer']} has no home location")
            line["home"] = "?"
        else:
            line["home"] = home["city"] or home["name"]
            if s["location_id"] == VIRTUAL_LOCATION_ID:
                line["travel"] = "remote"
            elif home["location_id"] != s["location_id"]:
                line["travel"] = "yes"
                travelling += 1
            else:
                line["travel"] = "no"

        # Room: big enough, and not booked twice the same day
        enrolled = count_enrollments(conn, s["session_id"])
        if s["room_id"] is not None:
            if s["seats"] is not None and enrolled > s["seats"]:
                warnings.append(
                    f"session {s['session_id']}: {enrolled} trainees for "
                    f"{s['seats']} seats in room {s['room_name']}"
                )
            if s["room_id"] in rooms_seen and s["location_id"] != VIRTUAL_LOCATION_ID:
                warnings.append(
                    f"room {s['room_name']} ({line['location']}) booked by sessions "
                    f"{rooms_seen[s['room_id']]} and {s['session_id']}"
                )
            rooms_seen[s["room_id"]] = s["session_id"]
        else:
            line["notes"].append("no room")

        # Notes for the planning team
        if s["is_in_house"]:
            in_house += 1
            if s["company_id"] is not None:
                client = scalar(conn, f"SELECT name FROM company WHERE company_id = {s['company_id']}")
                line["notes"].append(f"in-house: {client}")
            else:
                line["notes"].append("in-house")
        if s["status_code"] != "CONFIRMED":
            line["notes"].append(s["status_code"].lower())
        if day_number == 1:
            line["notes"].append(f"{enrolled} trainee(s)")
        if s["remarks"]:
            line["notes"].append(s["remarks"])

        board.append(line)

    board.sort(key=lambda b: (b["trainer"], b["session_id"]))
    summary = {
        "day": iso,
        "sessions": len(board),
        "trainers": len(trainers_on_duty),
        "travelling": travelling,
        "in_house": in_house,
    }
    return {"board": board, "warnings": warnings, "summary": summary}


def print_trainer_day(result, out=sys.stdout):
    summary = result["summary"]
    if not result["board"]:
        print(f"No session on {summary['day']}.", file=out)
        return
    table = [
        (
            b["trainer"],
            b["session_id"],
            b["title"][:40],
            b["day"],
            b["city"] or b["location"],
            b["home"],
            b["travel"],
            "; ".join(b["notes"]),
        )
        for b in result["board"]
    ]
    print_table(table, ["trainer", "session", "course", "day", "where", "home", "travel", "notes"], out)
    print(
        f"\n{summary['day']}: {summary['sessions']} session(s), {summary['trainers']} trainer(s) "
        f"on duty, {summary['travelling']} travelling, {summary['in_house']} in-house.",
        file=out,
    )
    if result["warnings"]:
        print(f"\n{len(result['warnings'])} warning(s):", file=out)
        for w in result["warnings"]:
            print(f"  - {w}", file=out)
    else:
        print("No warning.", file=out)


# ---------------------------------------------------------------------------
# Unpaid invoices
# ---------------------------------------------------------------------------


def unpaid_invoices(conn, today, days, statuses=["I"]):
    """Invoices issued at least `days` days ago and not fully paid.

    The balance of an invoice is its gross amount, minus the payments
    received, minus the credit notes issued against it. An invoice is late
    when its due date (or invoice date + payment terms) is past.
    """
    cutoff = today - timedelta(days=days)
    types = ", ".join(f"'{t}'" for t in statuses)
    invoices = query(
        conn,
        f"""
        SELECT i.invoice_code, i.invoice_date, i.due_date, i.gross_amount, i.net_amount,
               i.reminder_level, i.reminder_date, i.session_id, i.company_id, i.contact_id
        FROM invoice i
        WHERE i.document_type IN ({types})
          AND i.invoice_date IS NOT NULL
          AND i.invoice_date <= '{cutoff.isoformat()}'
        ORDER BY i.invoice_date, i.invoice_code
        """,
    )

    rows = []
    totals = {"count": 0, "gross": 0.0, "paid": 0.0, "credited": 0.0, "balance": 0.0}
    by_customer = defaultdict(float)
    for inv in invoices:
        code = inv["invoice_code"]
        paid = scalar(
            conn, f"SELECT COALESCE(SUM(amount), 0) FROM payment WHERE invoice_code = '{code}'"
        )
        credited = scalar(
            conn,
            f"SELECT COALESCE(SUM(gross_amount), 0) FROM invoice "
            f"WHERE document_type = 'C' AND original_invoice_code = '{code}'",
        )
        # Credit notes carry negative amounts.
        balance = inv["gross_amount"] + credited - paid
        if balance <= SETTLED_TOLERANCE:
            continue

        if inv["due_date"]:
            due = parse_day(inv["due_date"])
        else:
            due = parse_day(inv["invoice_date"]) + timedelta(days=PAYMENT_TERMS_DAYS)
        days_late = (today - due).days
        age = (today - parse_day(inv["invoice_date"])).days

        # Who owes it: the company when there is one, otherwise the person.
        if inv["company_id"] is not None:
            customer = scalar(
                conn, f"SELECT name FROM company WHERE company_id = {inv['company_id']}"
            )
        elif inv["contact_id"] is not None:
            person = query(
                conn,
                f"SELECT first_name, last_name FROM contact WHERE contact_id = {inv['contact_id']}",
            )
            customer = full_name(person[0]["first_name"], person[0]["last_name"]) if person else "?"
        else:
            customer = "?"

        # The trainees on the invoice, for the phone call.
        trainees = query(
            conn,
            f"""
            SELECT DISTINCT c.first_name, c.last_name
            FROM invoice_line l
            JOIN enrollment e ON e.enrollment_id = l.enrollment_id
            JOIN contact c ON c.contact_id = e.contact_id
            WHERE l.invoice_code = '{code}'
            ORDER BY c.last_name, c.first_name
            """,
        )
        names = [full_name(t["first_name"], t["last_name"]) for t in trainees]

        course = ""
        if inv["session_id"] is not None:
            course = scalar(
                conn,
                f"SELECT c.title FROM session s JOIN course c ON c.course_id = s.course_id "
                f"WHERE s.session_id = {inv['session_id']}",
            )

        # What to do next, from the reminders already sent and the delay.
        level = inv["reminder_level"] or 0
        if days_late <= 0:
            action = "wait (not due yet)"
        elif level == 0:
            action = "send first reminder"
        elif level == 1 and days_late > 15:
            action = "send second reminder"
        elif level == 2 and days_late > 30:
            action = "send formal notice"
        elif level >= 3 and days_late > 60:
            action = "hand over to collections"
        else:
            action = "wait"

        rows.append(
            {
                "invoice_code": code,
                "invoice_date": inv["invoice_date"],
                "due_date": due.isoformat(),
                "age": age,
                "days_late": days_late,
                "customer": customer,
                "course": course,
                "trainees": names,
                "gross": inv["gross_amount"],
                "paid": paid,
                "credited": credited,
                "balance": round(balance, 2),
                "reminders": REMINDER_LABELS.get(level, f"level {level}"),
                "action": action,
            }
        )
        totals["count"] += 1
        totals["gross"] += inv["gross_amount"]
        totals["paid"] += paid
        totals["credited"] += credited
        totals["balance"] += balance
        by_customer[customer] += balance

    rows.sort(key=lambda r: (-r["days_late"], r["invoice_code"]))
    top = sorted(by_customer.items(), key=lambda kv: -kv[1])[:5]
    return {"rows": rows, "totals": totals, "top_customers": top, "cutoff": cutoff.isoformat()}


def print_unpaid(result, days, out=sys.stdout):
    rows = result["rows"]
    if not rows:
        print(f"No unpaid invoice issued before {result['cutoff']}.", file=out)
        return
    table = [
        (
            r["invoice_code"],
            r["invoice_date"],
            r["days_late"],
            r["customer"][:30],
            money(r["balance"]),
            r["reminders"],
            r["action"],
        )
        for r in rows
    ]
    print_table(table, ["invoice", "date", "late", "customer", "balance", "reminders", "next"], out)
    t = result["totals"]
    print(
        f"\n{t['count']} unpaid invoice(s) issued {days} days ago or more "
        f"(on or before {result['cutoff']}), balance {money(t['balance'])}.",
        file=out,
    )
    print("Largest balances:", file=out)
    for customer, balance in result["top_customers"]:
        print(f"  {customer}: {money(balance)}", file=out)


# ---------------------------------------------------------------------------
# Monthly export for the accountants
# ---------------------------------------------------------------------------


def export_month(conn, month, out=sys.stdout):
    """Write the invoice lines of a month as CSV, with a TOTAL line at the end.

    One CSV line per invoice line. Credit notes are included, with negative
    amounts. Returns the number of lines written and the gross total.
    """
    first, following = parse_month(month)
    lines = query(
        conn,
        f"""
        SELECT i.invoice_code, i.invoice_date, i.document_type, i.vat_rate,
               COALESCE(co.name, ct.first_name || ' ' || ct.last_name, '') AS customer,
               l.line_number, l.line_type_code, l.label, l.quantity, l.unit_price, l.net_amount
        FROM invoice i
        JOIN invoice_line l ON l.invoice_code = i.invoice_code
        LEFT JOIN company co ON co.company_id = i.company_id
        LEFT JOIN contact ct ON ct.contact_id = i.contact_id
        WHERE i.invoice_date >= '{first.isoformat()}' AND i.invoice_date < '{following.isoformat()}'
        ORDER BY i.invoice_date, i.invoice_code, l.line_number
        """,
    )
    writer = csv.writer(out)
    writer.writerow(EXPORT_COLUMNS)
    total_net = 0.0
    total_vat = 0.0
    total_gross = 0.0
    for ln in lines:
        net = ln["net_amount"]
        vat = round(net * ln["vat_rate"] / 100, 2)
        gross = round(net + vat, 2)
        writer.writerow(
            [
                ln["invoice_code"],
                ln["invoice_date"],
                ln["document_type"],
                ln["customer"],
                ln["line_number"],
                ln["line_type_code"],
                ln["label"],
                f"{ln['quantity']:.2f}",
                f"{ln['unit_price']:.2f}",
                f"{net:.2f}",
                f"{ln['vat_rate']:.2f}",
                f"{vat:.2f}",
                f"{gross:.2f}",
            ]
        )
        total_net += net
        total_vat += vat
        total_gross += gross
    writer.writerow(
        ["TOTAL", month, "", "", "", "", f"{len(lines)} lines", "", "",
         f"{total_net:.2f}", "", f"{total_vat:.2f}", f"{total_gross:.2f}"]
    )
    return len(lines), round(total_gross, 2)
