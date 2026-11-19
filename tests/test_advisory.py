import unittest
from datetime import date
from unittest import mock

from genai import advisory

METRICS = {"commodity": "Onion", "state": "Maharashtra", "week": "2026-11-14 to 2026-11-20",
           "this_week_avg_price": 3790, "last_week_avg_price": 3557, "change_pct": -6.6,
           "national_avg_price": 4683, "top_3_markets": [{"market": "APMC Kamthi", "avg_price": 5650}],
           "lowest_3_markets": [], "avg_gap_between_min_and_max_price_within_a_market": 2744, "reports": 463}


class TestNumberCheck(unittest.TestCase):
    def test_traceable_answer_passes(self):
        text = ("Summary: Onion averaged ₹3,790 this week, down 6.6% from ₹3,557 (14 to 20 Nov 2026).\n"
                "Best markets to sell: 1. APMC Kamthi (5650)\nWatch out: 463 reports only.")
        self.assertEqual(advisory.untraceable_numbers(text, METRICS), [])

    def test_invented_number_is_caught(self):
        text = "Onion averaged ₹3,790, up from ₹3,200 last week; Kamthi paid 5650."
        self.assertEqual(advisory.untraceable_numbers(text, METRICS), [3200.0])

    def test_calculated_difference_is_caught(self):
        text = "Prices rose by ₹233 to ₹3,790."  # 3790 - 3557: a number the model computed itself
        self.assertEqual(advisory.untraceable_numbers(text, METRICS), [233.0])


class TestWeeklyAdvisory(unittest.TestCase):
    @mock.patch.object(advisory, "generate")
    @mock.patch.object(advisory, "get_metrics", return_value=dict(METRICS, reports=12))
    def test_too_few_reports_skips_the_model(self, _metrics, generate):
        result = advisory.weekly_advisory("Onion", "Goa", date(2026, 11, 20))
        self.assertEqual(result["status"], "not_enough_data")
        generate.assert_not_called()

    @mock.patch.object(advisory, "generate", return_value=("Average ₹9,999 this week.", {}))
    @mock.patch.object(advisory, "get_metrics", return_value=METRICS)
    def test_failed_check_hides_the_answer(self, _metrics, _generate):
        result = advisory.weekly_advisory("Onion", "Maharashtra", date(2026, 11, 20))
        self.assertEqual((result["status"], result["untraceable"]), ("failed_number_check", [9999.0]))


if __name__ == "__main__":
    unittest.main()
