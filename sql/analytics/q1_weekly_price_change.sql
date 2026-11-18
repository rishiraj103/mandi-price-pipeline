-- Q1: week-over-week change in average modal price, per commodity and state (last 8 weeks)
WITH weekly AS (
  SELECT c.commodity, m.state,
         date_trunc('week', d.full_date) AS week_start,
         avg(f.modal_price)              AS avg_modal_price,
         count(*)                        AS reports
  FROM mandi.fact_price_report f
  JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
  JOIN mandi.dim_market    m ON m.market_key    = f.market_key
  JOIN mandi.dim_date      d ON d.date_key      = f.date_key
  WHERE f.arrival_date >= cast(cast(current_date - INTERVAL '56' DAY AS date) AS varchar)  -- partition pruning
    AND NOT f.is_outlier
  GROUP BY 1, 2, 3
)
SELECT commodity, state, week_start, round(avg_modal_price) AS avg_modal_price, reports,
       round(100.0 * (avg_modal_price - LAG(avg_modal_price) OVER (PARTITION BY commodity, state ORDER BY week_start))
             / NULLIF(LAG(avg_modal_price) OVER (PARTITION BY commodity, state ORDER BY week_start), 0), 1) AS wow_change_pct
FROM weekly
ORDER BY commodity, state, week_start;
