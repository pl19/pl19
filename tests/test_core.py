import unittest

from src.importer import parse_money
from src.matcher import evaluate

PROFILE = {"min_revenue": 4_000_000, "sectors": {"Food": ["food"], "Aerospace": ["aerospace"]}}


class ParseMoney(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(parse_money(10765274), 10765274)
        self.assertEqual(parse_money("$10M-$40M"), 10_000_000)
        self.assertEqual(parse_money("$4.5 million"), 4_500_000)
        self.assertEqual(parse_money("Cash flow $2,954,803"), 2_954_803)
        self.assertIsNone(parse_money("On request"))


class Evaluate(unittest.TestCase):
    def test_below_minimum_rejected(self):
        ok, _, _ = evaluate({"name": "x", "sector": "Food", "revenue": "3000000"}, PROFILE)
        self.assertFalse(ok)

    def test_off_sector_rejected(self):
        ok, _, _ = evaluate({"name": "x", "sector": "Retail", "revenue": "9000000"}, PROFILE)
        self.assertFalse(ok)

    def test_cheap_listing_scores_high(self):
        row = {"name": "x", "kind": "listing", "sector": "Aerospace", "revenue": "6000000",
               "cash_flow": "$2,000,000", "asking_price": "$6,000,000", "notes": "Seller financing offered"}
        ok, score, _ = evaluate(row, PROFILE)
        self.assertTrue(ok)
        self.assertGreaterEqual(score, 95)


if __name__ == "__main__":
    unittest.main()
