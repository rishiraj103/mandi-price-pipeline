"""Weekly price advisory: fixed SQL computes the numbers, the LLM only writes them up, and a strict
check rejects any answer containing a number that is not in the metrics.

Usage: python -m genai.advisory Onion Maharashtra [2026-11-20]
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from genai.llm_client import generate
from tools.db import query

MIN_REPORTS = 20
PROMPT = Path(__file__).parent / "prompts" / "weekly_advisory.txt"

SUMMARY_SQL = """
SELECT avg(CASE WHEN f.arrival_date >= ? AND m.state = ? THEN f.modal_price END)  AS this_week_avg,
       avg(CASE WHEN f.arrival_date <  ? AND m.state = ? THEN f.modal_price END)  AS last_week_avg,
       avg(CASE WHEN f.arrival_date >= ? THEN f.modal_price END)                  AS national_avg,
       avg(CASE WHEN f.arrival_date >= ? AND m.state = ? THEN f.price_spread END) AS avg_spread,
       count(CASE WHEN f.arrival_date >= ? AND m.state = ? THEN 1 END)            AS reports
FROM mandi.fact_price_report f
JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
JOIN mandi.dim_market    m ON m.market_key    = f.market_key
WHERE c.commodity = ? AND f.arrival_date BETWEEN ? AND ? AND NOT f.is_outlier
"""

MARKETS_SQL = """
SELECT m.market, avg(f.modal_price) AS avg_modal_price
FROM mandi.fact_price_report f
JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
JOIN mandi.dim_market    m ON m.market_key    = f.market_key
WHERE c.commodity = ? AND m.state = ? AND f.arrival_date BETWEEN ? AND ? AND NOT f.is_outlier
GROUP BY m.market
ORDER BY avg_modal_price DESC, m.market
"""


def get_metrics(commodity, state, week_end):
    this_start = (week_end - timedelta(days=6)).isoformat()
    last_start = (week_end - timedelta(days=13)).isoformat()
    end = week_end.isoformat()
    s = query(SUMMARY_SQL, [this_start, state, this_start, state, this_start, this_start, state,
                            this_start, state, commodity, last_start, end]).iloc[0]
    markets = query(MARKETS_SQL, [commodity, state, this_start, end])

    def rnd(x):
        return None if x is None or x != x else int(round(float(x)))  # x != x catches NaN

    this_avg, last_avg = rnd(s["this_week_avg"]), rnd(s["last_week_avg"])
    top = [{"market": r.market, "avg_price": rnd(r.avg_modal_price)} for r in markets.head(3).itertuples()]
    bottom = [{"market": r.market, "avg_price": rnd(r.avg_modal_price)} for r in markets.tail(3).itertuples()]
    return {
        "commodity": commodity, "state": state, "week": f"{this_start} to {end}",
        "this_week_avg_price": this_avg, "last_week_avg_price": last_avg,
        "change_pct": round(100 * (this_avg - last_avg) / last_avg, 1) if this_avg and last_avg else None,
        "national_avg_price": rnd(s["national_avg"]),
        "top_3_markets": top, "lowest_3_markets": bottom[::-1],
        "avg_gap_between_min_and_max_price_within_a_market": rnd(s["avg_spread"]), "reports": int(s["reports"]),
    }


def _metric_numbers(obj):
    if isinstance(obj, dict):
        return [n for v in obj.values() for n in _metric_numbers(v)]
    if isinstance(obj, list):
        return [n for v in obj for n in _metric_numbers(v)]
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return [float(obj)]
    if isinstance(obj, str):  # digits inside names, e.g. a market called "Sector 26"
        return [float(x) for x in re.findall(r"\d+", obj)]
    return []


def _variants(values):
    """A value and its roundings, ignoring sign: 3789.6 -> {3789.6, 3790.0}; -0.4 -> {0.4, 0.0}."""
    out = set()
    for v in values:
        v = abs(v)
        out |= {v, float(round(v)), round(v, 1)}
    return out


def untraceable_numbers(text, metrics):
    """Numbers in the text that cannot be traced to the metrics.

    A percentage must match change_pct. Other numbers must match a metric value (or its rounding),
    a digit of the week's dates (e.g. "14 to 20 Nov"), or be a list number 1-3. Date digits are never
    accepted as percentages, so an invented "up 14%" is caught even though 14 is in the date range.
    """
    numeric = {k: v for k, v in metrics.items() if not isinstance(v, str)}
    allowed = _variants(_metric_numbers(numeric)) | {1.0, 2.0, 3.0}
    allowed |= {float(x) for v in metrics.values() if isinstance(v, str) for x in re.findall(r"\d+", v)}
    pct_allowed = _variants([metrics["change_pct"]]) if metrics.get("change_pct") is not None else set()

    bad = []
    for number, percent in re.findall(r"(\d[\d,]*(?:\.\d+)?)(\s*%)?", text):
        n = float(number.replace(",", ""))
        if n not in (pct_allowed if percent else allowed):
            bad.append(n)
    return bad


def weekly_advisory(commodity, state, week_end):
    metrics = get_metrics(commodity, state, week_end)
    if metrics["reports"] < MIN_REPORTS:
        return {"status": "not_enough_data", "metrics": metrics,
                "text": f"Not enough data: only {metrics['reports']} reports this week (need {MIN_REPORTS})."}

    prompt = PROMPT.read_text().replace("{metrics_json}", json.dumps(metrics, indent=1))
    text, meta = generate(prompt)
    bad = untraceable_numbers(text, metrics)
    if bad:
        return {"status": "failed_number_check", "metrics": metrics, "meta": meta, "draft": text,
                "untraceable": bad,
                "text": "Warning: the AI note contained numbers not found in the data, so only the metrics are shown."}
    return {"status": "ok", "metrics": metrics, "meta": meta, "text": text}


def latest_date():
    return date.fromisoformat(str(query(
        "SELECT max(arrival_date) AS d FROM mandi.fact_price_report "
        "WHERE arrival_date >= cast(cast(current_date - INTERVAL '14' DAY AS date) AS varchar)").iloc[0]["d"])[:10])


if __name__ == "__main__":
    week_end = date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else latest_date()
    result = weekly_advisory(sys.argv[1], sys.argv[2], week_end)
    print(json.dumps(result, indent=1, ensure_ascii=False))
