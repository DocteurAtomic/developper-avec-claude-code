from conftest import TODAY

from pachaplan.mcp_server import unpaid
from pachaplan.planning import unpaid_invoices


def test_unpaid_gives_the_totals_of_the_report(conn):
    report = unpaid_invoices(conn, TODAY, 30)
    result = unpaid(conn, TODAY, 30, 20)
    assert result["count"] == report["totals"]["count"]
    assert [r["invoice_code"] for r in result["invoices"]] == [
        r["invoice_code"] for r in report["rows"][:20]
    ]


def test_unpaid_shows_at_most_limit_invoices(conn):
    result = unpaid(conn, TODAY, 0, 1)
    assert result["shown"] == len(result["invoices"]) == min(1, result["count"])
