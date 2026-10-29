from conftest import TODAY

from pachaplan.planning import unpaid_invoices


def test_unpaid_skips_paid_and_credited_invoices(conn):
    result = unpaid_invoices(conn, TODAY, 30)
    assert [r["invoice_code"] for r in result["rows"]] == ["FA2"]
    assert result["rows"][0]["balance"] == 600
    assert result["rows"][0]["customer"] == "Hugo Fabre"


def test_unpaid_with_fewer_days_includes_recent_invoices(conn):
    result = unpaid_invoices(conn, TODAY, 10)
    assert sorted(r["invoice_code"] for r in result["rows"]) == ["FA2", "FA4"]
    assert result["totals"]["balance"] == 960
