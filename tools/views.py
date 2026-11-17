"""Views the app reads. Each view is the matching analytics query, so the SQL lives in one place."""
from pathlib import Path

VIEWS = {
    "v_weekly_prices": "sql/analytics/q1_weekly_price_change.sql",
    "v_market_ranking": "sql/analytics/q2_market_ranking.sql",
    "v_latest_price": "sql/analytics/q3_latest_price.sql",
}


def view_ddl(name):
    query = Path(VIEWS[name]).read_text().strip().rstrip(";")
    return f"CREATE OR REPLACE VIEW mandi.{name} AS\n{query}"
