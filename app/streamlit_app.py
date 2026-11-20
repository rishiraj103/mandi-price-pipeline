"""Mandi Price Tracker app. Data source: SOURCE=local (DuckDB on data/) or SOURCE=athena.

Run: streamlit run app/streamlit_app.py
"""
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so `tools` and `genai` import when run by streamlit
from genai.advisory import latest_date, weekly_advisory  # noqa: E402
from tools.db import query  # noqa: E402

BLUE = "#2a78d6"
st.set_page_config(page_title="Mandi Price Tracker", layout="wide")


@st.cache_data(ttl=3600, show_spinner=False)
def q(sql, params=()):
    return query(sql, list(params))


def line(df, x, y, title, y_label):
    fig = px.line(df, x=x, y=y, title=title, markers=True, labels={x: "", y: y_label})
    fig.update_traces(line=dict(color=BLUE, width=2), marker=dict(size=8))
    fig.update_layout(margin=dict(t=50, b=10), hovermode="x unified")
    return fig


def pick_commodity_state(key):
    commodities = q("SELECT DISTINCT commodity FROM mandi.dim_commodity ORDER BY 1")["commodity"].tolist()
    c1, c2 = st.columns(2)
    commodity = c1.selectbox("Commodity", commodities, index=commodities.index("Onion"), key=f"c_{key}")
    states = q("SELECT DISTINCT state FROM mandi.v_weekly_prices WHERE commodity = ? ORDER BY 1",
               [commodity])["state"].tolist()
    default = states.index("Maharashtra") if "Maharashtra" in states else 0
    return commodity, c2.selectbox("State", states, index=default, key=f"s_{key}")


def prices_page():
    st.header("Prices")
    commodity, state = pick_commodity_state("prices")
    weekly = q("SELECT week_start, avg_modal_price, reports, wow_change_pct FROM mandi.v_weekly_prices "
               "WHERE commodity = ? AND state = ? ORDER BY week_start", [commodity, state])
    if weekly.empty:
        st.info("No reports for this pair in the last 8 weeks.")
        return
    weekly["week_start"] = pd.to_datetime(weekly["week_start"]).dt.date
    last = weekly.iloc[-1]
    k1, k2, k3 = st.columns(3)
    k1.metric("Average modal price, latest week", f"₹{last.avg_modal_price:,.0f} / quintal",
              None if pd.isna(last.wow_change_pct) else f"{last.wow_change_pct:+.1f}% vs previous week")
    k2.metric("Reports, latest week", f"{int(last.reports):,}")
    k3.metric("Week starting", str(last.week_start))
    st.plotly_chart(line(weekly, "week_start", "avg_modal_price",
                         f"Weekly average modal price — {commodity}, {state}", "₹ / quintal"),
                    width="stretch")
    st.dataframe(weekly, hide_index=True, width="stretch")


def markets_page():
    st.header("Markets")
    commodity, state = pick_commodity_state("markets")
    ranking = q("SELECT market, district, avg_modal_price, reports, cheap_rank, costly_rank "
                "FROM mandi.v_market_ranking WHERE commodity = ? AND state = ?", [commodity, state])
    left, right = st.columns(2)
    cols = ["market", "avg_modal_price", "reports", "district"]
    left.subheader("Highest-paying markets (last 7 days)")
    left.dataframe(ranking[ranking.costly_rank <= 5].sort_values("costly_rank")[cols],
                   hide_index=True, width="stretch")
    right.subheader("Lowest-paying markets (last 7 days)")
    right.dataframe(ranking[ranking.cheap_rank <= 5].sort_values("cheap_rank")[cols],
                    hide_index=True, width="stretch")
    st.subheader("Latest price in each market")
    st.dataframe(q("SELECT market, district, price_date, modal_price, min_price, max_price, variety, grade "
                   "FROM mandi.v_latest_price WHERE commodity = ? AND state = ? ORDER BY price_date DESC, market",
                   [commodity, state]), hide_index=True, width="stretch")


def quality_page():
    st.header("Data quality")
    dq = q("SELECT arrival_date, rows_read, rows_passed, rows_rejected, outliers_flagged FROM mandi.dq "
           "ORDER BY arrival_date")
    dq["arrival_date"] = pd.to_datetime(dq["arrival_date"]).dt.date
    k1, k2, k3 = st.columns(3)
    k1.metric("Newest arrival date loaded", str(dq["arrival_date"].max()))
    k2.metric("Rows passed (all days)", f"{int(dq.rows_passed.sum()):,}")
    k3.metric("Rows rejected (all days)", f"{int(dq.rows_rejected.sum()):,}")
    st.plotly_chart(line(dq, "arrival_date", "rows_passed", "Rows loaded per day", "rows"),
                    width="stretch")
    reasons = q("SELECT reject_reason, count(*) AS rows_rejected FROM mandi.rejected "
                "WHERE arrival_date >= '2023-01-01' GROUP BY 1 ORDER BY 2 DESC")
    fig = px.bar(reasons, x="rows_rejected", y="reject_reason", orientation="h",
                 title="Rejected rows by reason", labels={"rows_rejected": "rows", "reject_reason": ""})
    fig.update_traces(marker_color=BLUE)
    fig.update_layout(margin=dict(t=50, b=10), height=260, bargap=0.4, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width="stretch")
    st.dataframe(dq.sort_values("arrival_date", ascending=False), hide_index=True, width="stretch")


def advisory_page():
    st.header("Weekly advisory")
    commodity, state = pick_commodity_state("advisory")
    week_end = st.date_input("Week ending", value=q_latest_date())
    if not st.button("Write advisory"):
        return
    with st.spinner("Computing metrics and asking the local model…"):
        result = weekly_advisory(commodity, state, week_end)
    left, right = st.columns(2)
    m = result["metrics"]
    left.subheader("Metrics (from SQL)")
    scalars = {k: v for k, v in m.items() if not isinstance(v, list)}
    left.dataframe(pd.DataFrame({"metric": list(scalars), "value": [str(v) for v in scalars.values()]}),
                   hide_index=True, width="stretch")
    left.caption("Highest-paying markets")
    left.dataframe(pd.DataFrame(m["top_3_markets"]), hide_index=True, width="stretch")
    left.caption("Lowest-paying markets")
    left.dataframe(pd.DataFrame(m["lowest_3_markets"]), hide_index=True, width="stretch")
    right.subheader("AI note")
    if result["status"] == "ok":
        right.success(result["text"].replace("\n", "  \n"))  # keep the note's line breaks
        right.caption(f"{result['meta']['model']} · {result['meta']['seconds']} s · every number checked")
    elif result["status"] == "failed_number_check":
        right.warning(result["text"])
        right.caption(f"Numbers not found in the metrics: {result['untraceable']}")
    else:
        right.info(result["text"])


@st.cache_data(ttl=3600, show_spinner=False)
def q_latest_date():
    try:
        return latest_date()
    except Exception:
        return date.today()


PAGES = {"Prices": prices_page, "Markets": markets_page, "Data quality": quality_page, "Advisory": advisory_page}
st.sidebar.title("Mandi Price Tracker")
st.sidebar.caption("Daily wholesale prices from data.gov.in (Agmarknet), ₹ per quintal")
start = st.query_params.get("page", "Prices")  # deep links, e.g. ?page=Markets
page = st.sidebar.radio("Page", list(PAGES), index=list(PAGES).index(start) if start in PAGES else 0)
PAGES[page]()
