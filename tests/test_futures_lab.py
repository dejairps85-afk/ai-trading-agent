import csv, tempfile, unittest
from datetime import datetime
from pathlib import Path
from futures_lab import CsvMarketFeed, MarketEvent, PaperBroker, RiskLimits, TapeReader, TapeReaderConfig
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
        self.assertTrue(b.open_position("WIN", "BUY", 1, 100)["ok"])
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


class TapeReaderTests(unittest.TestCase):
    def make_events(self, buy, sell, prices, instrument="WIN", depth=False):
        rows = []
        for i, (b, s, price) in enumerate(zip(buy, sell, prices)):
            rows.append(MarketEvent(datetime(2026, 1, 1, 9, 0, i), instrument, "TRADE", price,
                                    aggressor_buy_volume=b, aggressor_sell_volume=s,
                                    bid_depth=80 if depth else None, ask_depth=20 if depth else None))
        return rows

    def test_detects_buy_pressure_with_aggression(self):
        result = TapeReader().analyze(self.make_events([80, 70, 90], [20, 30, 10], [100, 101, 102]))
        self.assertEqual(result["classification"], "BUY_PRESSURE")
        self.assertEqual(result["delta"], 180)
        self.assertFalse(result["is_trade_recommendation"])

    def test_marks_possible_absorption_not_confirmed(self):
        result = TapeReader().analyze(self.make_events([90, 90, 90], [10, 10, 10], [100, 100, 99]))
        self.assertEqual(result["classification"], "POSSIBLE_BUY_ABSORPTION")

    def test_requires_real_aggressor_data(self):
        rows = [MarketEvent(datetime(2026, 1, 1, 9, 0, i), "WDO", "BAR", 5000) for i in range(3)]
        result = TapeReader().analyze(rows)
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")

    def test_calculates_optional_book_imbalance(self):
        result = TapeReader().analyze(self.make_events([10, 10, 10], [10, 10, 10],
                                                        [5000, 5001, 5002], "WDO", depth=True))
        self.assertAlmostEqual(result["book_imbalance"], 0.6)

    def test_rejects_mixed_instruments(self):
        rows = self.make_events([10, 10, 10], [5, 5, 5], [100, 101, 102])
        rows[1] = MarketEvent(rows[1].timestamp, "WDO", "TRADE", 5000,
                              aggressor_buy_volume=10, aggressor_sell_volume=5)
        with self.assertRaises(ValueError):
            TapeReader().analyze(rows)

    def test_minimum_event_guard(self):
        result = TapeReader(TapeReaderConfig(min_events=4)).analyze(
            self.make_events([10, 10, 10], [1, 1, 1], [100, 101, 102]))
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")

    def test_rejects_non_finite_or_negative_market_fields(self):
        with self.assertRaises(ValueError):
            MarketEvent(datetime(2026, 1, 1), "WIN", "TRADE", float("nan"))
        with self.assertRaises(ValueError):
            MarketEvent(datetime(2026, 1, 1), "WIN", "BOOK", 100, bid_depth=-1)
        with self.assertRaises(ValueError):
            MarketEvent(datetime(2026, 1, 1), "WIN", "TRADE", 100,
                        aggressor_buy_volume=float("inf"))

    def test_rejects_non_market_event_before_reading_fields(self):
        with self.assertRaises(TypeError):
            TapeReader().analyze([object()])

    def test_rejects_non_finite_tape_threshold(self):
        with self.assertRaises(ValueError):
            TapeReaderConfig(pressure_delta_ratio=float("nan"))


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



class DecisionEngineTests(unittest.TestCase):
    def make_events(self, buy, sell, prices, depth=False):
        return [MarketEvent(datetime(2026, 1, 1, 9, 0, i), "WIN", "TRADE", price,
                            aggressor_buy_volume=b, aggressor_sell_volume=s,
                            best_bid=price - 1, best_ask=price,
                            bid_depth=80 if depth else None,
                            ask_depth=20 if depth else None)
                for i, (b, s, price) in enumerate(zip(buy, sell, prices))]

    def test_buy_requires_flow_and_price_confirmation(self):
        from futures_lab import DecisionEngine
        result = DecisionEngine().evaluate(self.make_events([80, 70, 90], [20, 30, 10], [100, 101, 102]))
        self.assertEqual(result["decision"], "BUY")
        self.assertFalse(result["is_trade_recommendation"])

    def test_absorption_defaults_to_hold(self):
        from futures_lab import DecisionEngine
        result = DecisionEngine().evaluate(self.make_events([90, 90, 90], [10, 10, 10], [100, 100, 99]))
        self.assertEqual(result["decision"], "HOLD")

    def test_missing_spread_fails_closed_when_filter_enabled(self):
        from futures_lab import DecisionConfig, DecisionEngine
        events = [MarketEvent(datetime(2026, 1, 1, 9, 0, i), "WIN", "TRADE", p,
                              aggressor_buy_volume=80, aggressor_sell_volume=20)
                  for i, p in enumerate([100, 101, 102])]
        result = DecisionEngine(config=DecisionConfig(max_spread_points=2)).evaluate(events)
        self.assertEqual(result["decision"], "HOLD")

    def test_book_confirmation_blocks_opposing_book(self):
        from futures_lab import DecisionConfig, DecisionEngine
        events = [MarketEvent(datetime(2026, 1, 1, 9, 0, i), "WIN", "TRADE", p,
                              aggressor_buy_volume=80, aggressor_sell_volume=20,
                              bid_depth=10, ask_depth=90)
                  for i, p in enumerate([100, 101, 102])]
        result = DecisionEngine(config=DecisionConfig(require_book_confirmation=True)).evaluate(events)
        self.assertEqual(result["decision"], "HOLD")


class ReplayEngineTests(unittest.TestCase):
    def make_events(self, prices, buy=80, sell=20, start_day=1):
        return [MarketEvent(datetime(2026, 1, start_day, 9, 0, i), "WIN", "TRADE", price,
                            aggressor_buy_volume=buy, aggressor_sell_volume=sell,
                            best_bid=price - 1, best_ask=price)
                for i, price in enumerate(prices)]

    def test_replay_reports_metrics_and_closes_at_end(self):
        from futures_lab import ReplayConfig, ReplayEngine
        events = self.make_events([100, 101, 102, 103, 104])
        result = ReplayEngine(config=ReplayConfig(point_value=1, window_events=3,
                                                   take_profit_points=2)).run(events)
        metrics = result["metrics"]
        self.assertEqual(metrics["mode"], "PAPER_ONLY")
        self.assertEqual(metrics["event_count"], 5)
        self.assertGreaterEqual(metrics["trade_count"], 1)
        self.assertFalse(metrics["is_live_performance"])
        self.assertEqual(metrics["open_positions"], {})

    def test_replay_rejects_mixed_instruments(self):
        from futures_lab import ReplayConfig, ReplayEngine
        events = self.make_events([100, 101, 102])
        events.append(MarketEvent(datetime(2026, 1, 1, 9, 0, 4), "WDO", "TRADE", 5000,
                                  aggressor_buy_volume=80, aggressor_sell_volume=20))
        with self.assertRaises(ValueError):
            ReplayEngine(config=ReplayConfig(point_value=1)).run(events)

    def test_replay_requires_explicit_point_value(self):
        from futures_lab import ReplayEngine
        with self.assertRaises(ValueError):
            ReplayEngine()

    def test_replay_costs_are_included(self):
        from futures_lab import ReplayConfig, ReplayEngine
        events = self.make_events([100, 101, 102, 102.1])
        result = ReplayEngine(config=ReplayConfig(point_value=1, window_events=3,
                                                   fee_per_contract_side=0.5,
                                                   close_at_end=True)).run(events)
        self.assertLess(result["metrics"]["net_pnl"], 0.0)


    def test_warmup_context_allows_first_test_event_decision_without_counting_context(self):
        from futures_lab import ReplayConfig, ReplayEngine
        test_events = self.make_events([103, 104, 105])
        context = self.make_events([100, 101, 102])
        result = ReplayEngine(config=ReplayConfig(point_value=1, window_events=3)).run(
            test_events, warmup_events=context)
        self.assertEqual(result["metrics"]["event_count"], 3)
        self.assertEqual(result["decisions"][0]["timestamp"], test_events[0].timestamp.isoformat())

    def test_warmup_must_precede_test_period(self):
        from futures_lab import ReplayConfig, ReplayEngine
        events = self.make_events([100, 101, 102])
        with self.assertRaises(ValueError):
            ReplayEngine(config=ReplayConfig(point_value=1)).run(events, warmup_events=events[:1])


if __name__ == "__main__":
    unittest.main()


class ChronologicalSplitTests(unittest.TestCase):
    def make_events(self, prices, instrument="WIN"):
        return [MarketEvent(datetime(2026, 1, 1, 9, 0, i), instrument, "TRADE", price,
                            aggressor_buy_volume=80, aggressor_sell_volume=20)
                for i, price in enumerate(prices)]

    def test_split_is_ordered_disjoint_and_nonempty(self):
        from futures_lab import chronological_split
        events = list(reversed(self.make_events([101, 102, 103, 104, 105, 106, 107, 108, 109, 110])))
        result = chronological_split(events, train_ratio=0.6, validation_ratio=0.2)
        self.assertEqual([e.last_price for e in result["train"]], [101, 102, 103, 104, 105, 106])
        self.assertEqual([e.last_price for e in result["validation"]], [107, 108])
        self.assertEqual([e.last_price for e in result["test"]], [109, 110])
        self.assertEqual(len(set(result["train"]) & set(result["validation"])), 0)
        self.assertEqual(len(set(result["validation"]) & set(result["test"])), 0)

    def test_split_rejects_mixed_instruments(self):
        from futures_lab import chronological_split
        events = self.make_events([100, 101, 102])
        events.append(self.make_events([5000], instrument="WDO")[0])
        with self.assertRaises(ValueError):
            chronological_split(events)

    def test_split_rejects_invalid_ratios_and_too_few_events(self):
        from futures_lab import chronological_split
        with self.assertRaises(ValueError):
            chronological_split(self.make_events([100, 101]), train_ratio=0.6, validation_ratio=0.2)
        with self.assertRaises(ValueError):
            chronological_split(self.make_events([100, 101, 102]), train_ratio=0.8, validation_ratio=0.3)

    def test_split_rejects_mixed_timezone_awareness(self):
        from datetime import timezone
        from futures_lab import chronological_split
        events = self.make_events([100, 101, 102])
        events[1] = MarketEvent(datetime(2026, 1, 1, 9, 0, 1, tzinfo=timezone.utc),
                                "WIN", "TRADE", 101,
                                aggressor_buy_volume=80, aggressor_sell_volume=20)
        with self.assertRaises(ValueError):
            chronological_split(events)


class WalkForwardTests(unittest.TestCase):
    def make_events(self, count):
        return [MarketEvent(datetime(2026, 1, 1, 9, 0, i), "WIN", "TRADE", 100 + i,
                            aggressor_buy_volume=80, aggressor_sell_volume=20,
                            best_bid=99 + i, best_ask=100 + i)
                for i in range(count)]

    def test_walk_forward_uses_non_overlapping_tests_and_warmup(self):
        from futures_lab import ReplayConfig, walk_forward_replay
        result = walk_forward_replay(
            self.make_events(18),
            ReplayConfig(point_value=1, window_events=3, take_profit_points=2),
            train_events=6, validation_events=3, test_events=3)
        self.assertEqual(result["fold_count"], 3)
        self.assertEqual(result["aggregate"]["test_event_count"], 9)
        self.assertTrue(result["test_blocks_non_overlapping"])
        self.assertFalse(result["parameter_fitting_performed"])
        self.assertEqual(result["folds"][0]["metrics"]["event_count"], 3)
        self.assertEqual(result["folds"][0]["decisions"][0]["timestamp"],
                         result["folds"][0]["test_range"][0])

    def test_walk_forward_rejects_insufficient_data_and_bad_windows(self):
        from futures_lab import ReplayConfig, walk_forward_replay
        with self.assertRaises(ValueError):
            walk_forward_replay(self.make_events(5), ReplayConfig(point_value=1), 3, 2, 1)
        with self.assertRaises(ValueError):
            walk_forward_replay(self.make_events(10), ReplayConfig(point_value=1), 0, 2, 1)
