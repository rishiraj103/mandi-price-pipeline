import unittest
from datetime import date

import pandas as pd

from transform import rules

DAY = date(2026, 11, 20)


def raw(**overrides):
    row = {"Arrival_Date": "20/11/2026", "State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon",
           "Commodity": "Onion", "Commodity_Code": 23, "Variety": "Red", "Grade": "FAQ",
           "Min_Price": 2000, "Max_Price": 3000, "Modal_Price": 2500}
    row.update(overrides)
    return row


def frame(*rows):
    return rules.standardise(pd.DataFrame(list(rows)), {"Ginger(Green)": "Ginger"})


def priced(*rows):
    return rules.price_not_number(frame(*rows))[0]


class TestRules(unittest.TestCase):
    def assertSplit(self, result, n_good, n_bad, reason):
        good, bad = result
        self.assertEqual((len(good), len(bad)), (n_good, n_bad))
        self.assertTrue((bad["reject_reason"] == reason).all())

    def test_standardise(self):
        df = frame(raw(Market="  Ashta  APMC ", Commodity="Ginger(Green)"))
        self.assertEqual(df.loc[0, "market"], "Ashta APMC")
        self.assertEqual(df.loc[0, "commodity"], "Ginger")

    def test_missing_field(self):
        self.assertSplit(rules.missing_field(frame(raw(), raw(Market="  "), raw(Modal_Price=None))),
                         1, 2, "missing_field")

    def test_bad_date(self):
        df = frame(raw(), raw(Arrival_Date="2026-11-20"), raw(Arrival_Date="19/11/2026"),
                   raw(Arrival_Date="31/02/2026"))
        self.assertSplit(rules.bad_date(df, DAY, today=date(2026, 11, 21)), 1, 3, "bad_date")

    def test_future_date(self):
        self.assertSplit(rules.bad_date(frame(raw()), DAY, today=date(2026, 11, 19)), 0, 1, "bad_date")

    def test_price_not_number(self):
        good, bad = rules.price_not_number(frame(raw(), raw(Modal_Price="2,500"), raw(Min_Price="NR")))
        self.assertSplit((good, bad), 1, 2, "price_not_number")
        self.assertEqual(good["modal_price"].iloc[0], 2500.0)

    def test_non_positive_price(self):
        self.assertSplit(rules.non_positive_price(priced(raw(), raw(Min_Price=0), raw(Modal_Price=-5))),
                         1, 2, "non_positive_price")

    def test_price_order(self):
        df = priced(raw(), raw(Min_Price=2600), raw(Max_Price=2400), raw(Min_Price=2500, Modal_Price=2500))
        self.assertSplit(rules.price_order(df), 2, 2, "price_order")

    def test_duplicate_keeps_lowest_modal(self):
        good, bad = rules.duplicate(priced(raw(Modal_Price=2700), raw(Modal_Price=2500), raw(Grade="Local")))
        self.assertSplit((good, bad), 2, 1, "duplicate")
        self.assertEqual(good.loc[good["grade"] == "FAQ", "modal_price"].iloc[0], 2500.0)

    def test_flag_outliers(self):
        df = priced(*[raw(Market=m) for m in "ABC"], raw(Market="D", Modal_Price=20000, Max_Price=20000),
                    raw(Market="E", Min_Price=1, Modal_Price=1))
        flags = rules.flag_outliers(df).set_index("market")["is_outlier"]
        self.assertEqual(flags.to_dict(), {"A": False, "B": False, "C": False, "D": True, "E": True})

    def test_apply_rules(self):
        clean, rejected = rules.apply_rules(frame(raw(), raw(Modal_Price="x"), raw(Min_Price=4000)), DAY)
        self.assertEqual(len(clean), 1)
        self.assertEqual(sorted(rejected["reject_reason"]), ["price_not_number", "price_order"])


if __name__ == "__main__":
    unittest.main()
