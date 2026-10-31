from conftest import TODAY

from pachaplan.planning import print_unpaid, unpaid_invoices


def test_unpaid_skips_paid_and_credited_invoices(conn):
    result = unpaid_invoices(conn, TODAY, 30)
    assert [r["invoice_code"] for r in result["rows"]] == ["FA2"]
    assert result["rows"][0]["balance"] == 600
    assert result["rows"][0]["customer"] == "Hugo Fabre"


def test_unpaid_with_fewer_days_includes_recent_invoices(conn):
    result = unpaid_invoices(conn, TODAY, 10)
    assert sorted(r["invoice_code"] for r in result["rows"]) == ["FA2", "FA4"]
    assert result["totals"]["balance"] == 960


def test_print_unpaid_writes_to_current_stdout(conn, capsys):
    """Without out, the output goes to sys.stdout as it is at call time."""
    result = unpaid_invoices(conn, TODAY, 30)
    print_unpaid(result, 30)
    out = capsys.readouterr().out
    assert "FA2" in out
    assert "1 unpaid invoice(s) issued 30 days ago or more" in out
