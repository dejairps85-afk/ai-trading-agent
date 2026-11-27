import tempfile
import unittest
from pathlib import Path

from futures_lab import ProfitCsvAdapter, ProfitCsvMapping, ReplayConfig, ReplayEngine
from futures_lab.import_pipeline import run_imported_replay


class ImportedReplayPipelineTests(unittest.TestCase):
    def test_valid_import_reaches_paper_replay_and_keeps_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bars.csv"
            path.write_text("ts,asset,kind,price\n"
                "2026-01-02T09:00:00,WIN,BAR,130000\n"
                "2026-01-02T09:05:00,WIN,BAR,130010\n", encoding="utf-8")
            mapping = ProfitCsvMapping(timestamp="ts", instrument="asset",
                event_type="kind", last_price="price")
            imported = ProfitCsvAdapter().read(path, mapping)
            engine = ReplayEngine(config=ReplayConfig(point_value=1, window_events=1))
            result = run_imported_replay(imported, engine)
            self.assertEqual(result["mode"], "PAPER_ONLY")
            self.assertFalse(result["is_live_performance"])
            self.assertTrue(result["import_report"]["replay_eligible"])
            self.assertEqual(result["metrics"]["event_count"], 2)

    def test_invalid_import_is_blocked_before_replay(self):
        from futures_lab.profit_csv import ImportResult
        invalid = ImportResult((), {"replay_eligible": False, "errors": ["invalid"]})
        engine = ReplayEngine(config=ReplayConfig(point_value=1))
        with self.assertRaisesRegex(ValueError, "replay bloqueado"):
            run_imported_replay(invalid, engine)


if __name__ == "__main__":
    unittest.main()
