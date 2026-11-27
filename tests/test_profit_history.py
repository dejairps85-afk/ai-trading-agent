import unittest
from datetime import date, time
from futures_lab.profit_history import daily_requests


class HistoryPlannerTests(unittest.TestCase):
    def test_weekend_and_format(self):
        rows = list(daily_requests('WINZ26', date(2026,11,27), date(2026,11,30), time(9), time(18)))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ('WINZ26','F','27/11/2026 09:00:00','27/11/2026 18:00:00'))
        self.assertEqual(rows[1][2], '30/11/2026 09:00:00')

    def test_reject_invalid(self):
        for symbol in ('WINFUT','WDO','PETR4'):
            with self.assertRaises(ValueError):
                list(daily_requests(symbol,date(2026,11,27),date(2026,11,27),time(9),time(18)))
        with self.assertRaises(ValueError):
            list(daily_requests('WINZ26',date(2026,11,27),date(2026,11,27),time(18),time(9)))
