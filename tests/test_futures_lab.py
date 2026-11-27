import csv, tempfile, unittest
from datetime import datetime
from pathlib import Path
from futures_lab import CsvMarketFeed, MarketEvent, PaperBroker, RiskLimits
from unittest.mock import patch
from llm import LLMClient


class FuturesLabTests(unittest.TestCase):
    def test_delta_spread(self):
        e = MarketEvent(datetime(2026, 1, 1), "WIN", "TRADE", 130000,
                        aggressor_buy_volume=12, aggressor_sell_volume=7,
                        best_bid=129999, best_ask=130000)
        self.assertEqual(e.delta, 5)
        self.assertEqual(e.spread, 1)

    def test_csv_does_not_invent_tape(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["timestamp", "instrument", "event_type", "last_price"])
                w.writeheader()
                w.writerow({"timestamp": "2026-01-01T09:00:00", "instrument": "WDO",
                            "event_type": "BAR", "last_price": "5000"})
            e = next(iter(CsvMarketFeed(p)))
            self.assertIsNone(e.delta)
            self.assertEqual(e.instrument, "WDO")

    def test_short_pnl_with_costs(self):
        b = PaperBroker(10000, {"WIN": RiskLimits(max_contracts=2, point_value=.2,
                                                  fee_per_contract_side=.5, slippage_points=1)})
        self.assertTrue(b.open_position("WIN", "SELL", 2, 130000)["ok"])
        r = b.close_position("WIN", 129990)
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["trade"]["pnl"], 1.2)

    def test_long_stop_closes_at_stop_price(self):
        b = PaperBroker(limits={"WIN": RiskLimits(max_contracts=1, point_value=1)})
        b.open_position("WIN", "BUY", 1, 100, stop_price=95, target_price=110)
        result = b.process_price("WIN", 94)
        self.assertTrue(result["ok"])
        self.assertEqual(result["trade"]["reason"], "stop_loss")
        self.assertEqual(result["trade"]["exit_price"], 95)

    def test_short_target_closes_at_target_price(self):
        b = PaperBroker(limits={"WDO": RiskLimits(max_contracts=1, point_value=1)})
        b.open_position("WDO", "SELL", 1, 5000, stop_price=5010, target_price=4980)
        result = b.process_price("WDO", 4975)
        self.assertTrue(result["ok"])
        self.assertEqual(result["trade"]["reason"], "take_profit")
        self.assertEqual(result["trade"]["exit_price"], 4980)

    def test_limits_and_duplicate(self):
        b = PaperBroker(limits={"WDO": RiskLimits(max_contracts=1, point_value=10)})
        self.assertFalse(b.open_position("WDO", "BUY", 2, 5000)["ok"])
        self.assertTrue(b.open_position("WDO", "BUY", 1, 5000)["ok"])
        self.assertFalse(b.open_position("WDO", "SELL", 1, 5001)["ok"])

    def test_daily_loss_blocks_new_position(self):
        b = PaperBroker(limits={"WIN": RiskLimits(max_contracts=1, max_daily_loss=100, point_value=1)})
        self.assertTrue(b.open_position("WIN", "BUY", 1, 1000)["ok"])
        b.close_position("WIN", 899)
        blocked = b.open_position("WIN", "BUY", 1, 900)
        self.assertFalse(blocked["ok"])
        self.assertIn("perda diária", blocked["reason"])

    def test_mark_to_market_long_and_short(self):
        b = PaperBroker(limits={"WIN": RiskLimits(point_value=1), "WDO": RiskLimits(point_value=2)})
        b.open_position("WIN", "BUY", 1, 100)
        b.open_position("WDO", "SELL", 1, 5000)
        result = b.mark_to_market({"WIN": 110, "WDO": 4995})
        self.assertEqual(result["unrealized_pnl"], 20)
        self.assertEqual(result["equity"], 10020)

    def test_rejects_non_finite_prices(self):
        b = PaperBroker(limits={"WIN": RiskLimits()})
        self.assertFalse(b.open_position("WIN", "BUY", 1, float("nan"))["ok"])
        self.assertFalse(b.open_position("WIN", "BUY", 1, 100, stop_price=float("inf"))["ok"])
        with self.assertRaises(ValueError):
            b.mark_to_market({"WIN": float("nan")})

    def test_risk_limits_reject_non_finite_values(self):
        with self.assertRaises(ValueError):
            RiskLimits(max_daily_loss=float("nan"))
        with self.assertRaises(ValueError):
            RiskLimits(point_value=float("inf"))
        with self.assertRaises(ValueError):
            RiskLimits(slippage_points=float("nan"))


class StructuredDecisionTests(unittest.TestCase):
    def test_valid_json_object(self):
        client = LLMClient()
        with patch("llm.call_llama", return_value='{"approved": true, "confidence": 0.8}'):
            result = client.structured_decision("system", "prompt")
        self.assertTrue(result["approved"])

    def test_invalid_json_fails_closed(self):
        client = LLMClient()
        with patch("llm.call_llama", return_value="not json"):
            result = client.structured_decision("system", "prompt")
        self.assertFalse(result["approved"])
        self.assertEqual(result["position_size_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
