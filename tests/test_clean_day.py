import unittest
from datetime import date

from transform.clean_day import clean

COMMODITIES = {"Onion": {"name": "Onion", "group": "vegetable"}}


class TestCleanDay(unittest.TestCase):
    def test_empty_day(self):
        curated, rejected, dq = clean([], date(2026, 11, 20), COMMODITIES)
        self.assertEqual((len(curated), len(rejected), dq["rows_read"]), (0, 0, 0))

    def test_summary_counts(self):
        row = {"Arrival_Date": "20/11/2026", "State": "Goa", "District": "North Goa", "Market": "Mapusa",
               "Commodity": "Onion", "Commodity_Code": 23, "Variety": "Red", "Grade": "FAQ",
               "Min_Price": 2000, "Max_Price": 3000, "Modal_Price": 2500}
        _, _, dq = clean([row, dict(row, Modal_Price=0)], date(2026, 11, 20), COMMODITIES)
        self.assertEqual((dq["rows_passed"], dq["by_reason"]), (1, {"non_positive_price": 1}))


if __name__ == "__main__":
    unittest.main()
