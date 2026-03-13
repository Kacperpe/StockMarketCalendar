import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mt5_server"))

import ct_data_parser  # noqa: E402


class CtOverviewTests(unittest.TestCase):
    def test_compute_ct_overview_uses_cashflows_for_gain_and_totals(self):
        fake_rows = [{"dummy": True}]
        fake_trades = [
            {"pnl_net": 150.0, "close_time": "2026-01-10T00:00:00"},
            {"pnl_net": -50.0, "close_time": "2026-01-11T00:00:00"},
        ]
        cash_flows = [
            SimpleNamespace(delta=100000, balance=100000, moneyDigits=2),  # +1000
            SimpleNamespace(delta=-20000, balance=80000, moneyDigits=2),   # -200
        ]

        with patch.object(ct_data_parser, "_ct_deals_to_rows", return_value=fake_rows):
            with patch.object(ct_data_parser, "_aggregate_ct_rows", return_value=fake_trades):
                result = ct_data_parser.compute_ct_overview(
                    deals_all=[],
                    balance_now=900.0,
                    currency="USD",
                    cash_flows=cash_flows,
                    equity_now=905.0,
                )

        self.assertEqual(result["balance"], 900.0)
        self.assertEqual(result["equity"], 905.0)
        self.assertEqual(result["total_profit"], 100.0)
        self.assertEqual(result["deposits"], 1000.0)
        self.assertEqual(result["withdrawals"], 200.0)
        self.assertAlmostEqual(result["gain_pct"], 12.5, places=2)  # 100 / (1000-200)

    def test_compute_ct_overview_infers_balance_when_snapshot_empty(self):
        fake_rows = [{"dummy": True}]
        fake_trades = [
            {"pnl_net": 120.0, "close_time": "2026-01-10T00:00:00"},
            {"pnl_net": -20.0, "close_time": "2026-01-11T00:00:00"},
        ]
        cash_flows = [
            SimpleNamespace(delta=100000, balance=100000, moneyDigits=2),  # +1000
            SimpleNamespace(delta=-20000, balance=80000, moneyDigits=2),   # -200
        ]

        with patch.object(ct_data_parser, "_ct_deals_to_rows", return_value=fake_rows):
            with patch.object(ct_data_parser, "_aggregate_ct_rows", return_value=fake_trades):
                result = ct_data_parser.compute_ct_overview(
                    deals_all=[],
                    balance_now=0.0,
                    currency="USD",
                    cash_flows=cash_flows,
                    equity_now=0.0,
                )

        # Inferred balance = net deposits (800) + total profit (100)
        self.assertEqual(result["balance"], 900.0)
        self.assertEqual(result["equity"], 900.0)
        self.assertEqual(result["total_profit"], 100.0)
        self.assertEqual(result["deposits"], 1000.0)
        self.assertEqual(result["withdrawals"], 200.0)
        self.assertAlmostEqual(result["gain_pct"], 12.5, places=2)


if __name__ == "__main__":
    unittest.main()
