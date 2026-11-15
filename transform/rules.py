"""Data-quality rules. Each rule takes a DataFrame and returns (good_df, bad_df);
bad rows carry a `reject_reason` column."""
from datetime import date

import pandas as pd

RENAME = {
    "Arrival_Date": "reported_date", "State": "state", "District": "district", "Market": "market",
    "Commodity": "commodity", "Commodity_Code": "commodity_code", "Variety": "variety", "Grade": "grade",
    "Min_Price": "min_price", "Max_Price": "max_price", "Modal_Price": "modal_price",
}
TEXT_COLS = ["reported_date", "state", "district", "market", "commodity", "variety", "grade"]
PRICE_COLS = ["min_price", "max_price", "modal_price"]
REQUIRED = ["reported_date", "state", "market", "commodity", "modal_price"]
NATURAL_KEY = ["state", "district", "market", "commodity", "variety", "grade"]  # date is fixed per run
OUTLIER_FACTOR = 5


def _split(df, bad_mask, reason):
    return df[~bad_mask], df[bad_mask].assign(reject_reason=reason)


def standardise(df, commodity_names):
    """Rename columns, trim and collapse whitespace, map commodity names. Rejects nothing."""
    df = df.rename(columns=RENAME).astype("string")
    for col in df.columns:
        df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True).replace("", pd.NA)
    df["commodity"] = df["commodity"].map(lambda c: commodity_names.get(c, c), na_action="ignore")
    return df


def missing_field(df):
    return _split(df, df[REQUIRED].isna().any(axis=1), "missing_field")


def bad_date(df, expected, today=None):
    parsed = pd.to_datetime(df["reported_date"], format="%d/%m/%Y", errors="coerce").dt.date
    bad = parsed.isna() | (parsed > (today or date.today())) | (parsed != expected)
    return _split(df, bad, "bad_date")


def price_not_number(df):
    prices = df[PRICE_COLS].apply(pd.to_numeric, errors="coerce")
    good, bad = _split(df, prices.isna().any(axis=1), "price_not_number")
    return good.assign(**prices.loc[good.index].astype(float)), bad


def non_positive_price(df):
    return _split(df, (df[PRICE_COLS] <= 0).any(axis=1), "non_positive_price")


def price_order(df):
    ordered = (df["min_price"] <= df["modal_price"]) & (df["modal_price"] <= df["max_price"])
    return _split(df, ~ordered, "price_order")


def duplicate(df):
    """Several reports for one natural key: keep the lowest modal (then min, max) so the choice is deterministic."""
    df = df.sort_values(NATURAL_KEY + ["modal_price", "min_price", "max_price"], na_position="first")
    return _split(df, df.duplicated(NATURAL_KEY, keep="first"), "duplicate")


def flag_outliers(df):
    """Flag (not reject) modal prices > 5x or < 1/5 of the commodity's national median for the day."""
    median = df.groupby("commodity")["modal_price"].transform("median")
    ratio = df["modal_price"] / median
    return df.assign(is_outlier=(ratio > OUTLIER_FACTOR) | (ratio < 1 / OUTLIER_FACTOR))


def apply_rules(df, expected_date):
    """Run every rule in order; returns (clean_df with is_outlier, rejected_df)."""
    rules = [missing_field, lambda d: bad_date(d, expected_date), price_not_number,
             non_positive_price, price_order, duplicate]
    rejected = []
    for rule in rules:
        df, bad = rule(df)
        rejected.append(bad.astype({c: "string" for c in PRICE_COLS}))
    return flag_outliers(df), pd.concat(rejected, ignore_index=True)
