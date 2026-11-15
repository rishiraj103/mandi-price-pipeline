import unittest
from datetime import date

import pandas as pd

from transform import build_model as bm

CURATED = pd.DataFrame({
    "state": ["Goa", "Goa"], "district": ["North Goa"] * 2, "market": ["Mapusa", "Panaji"],
    "commodity": ["Onion"] * 2, "commodity_code": [23, 23], "variety": ["Red"] * 2, "grade": ["FAQ"] * 2,
    "min_price": [2000.0, 2100.0], "max_price": [3000.0, 2900.0], "modal_price": [2500.0, 2600.0],
    "is_outlier": [False, False],
})


class TestBuildModel(unittest.TestCase):
    def test_hash_key_is_stable(self):
        keys = bm.hash_key(CURATED, bm.MARKET_COLS)
        self.assertEqual(keys.iloc[0], "34179b0b16aa1aa27375c4eda889b38c")  # md5('Goa|North Goa|Mapusa')
        self.assertNotEqual(keys.iloc[0], keys.iloc[1])

    def test_upsert_adds_only_new_members(self):
        dim = bm.market_rows(CURATED, {"West": ["Goa"]})
        merged = bm.upsert(dim.iloc[:1], dim, "market_key")
        self.assertEqual(len(merged), 2)
        self.assertEqual(set(merged["region"]), {"West"})

    def test_fact_rows(self):
        fact = bm.fact_rows(CURATED, date(2026, 11, 20))
        self.assertEqual(list(fact.columns), bm.FACT_COLS)
        self.assertEqual(list(fact["price_spread"]), [1000.0, 800.0])
        self.assertTrue((fact["date_key"] == 20261120).all())


if __name__ == "__main__":
    unittest.main()
