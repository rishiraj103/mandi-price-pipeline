-- Q5: how far each state's average modal price is from the national average (last 7 days)
WITH state_avg AS (
  SELECT c.commodity, m.state, avg(f.modal_price) AS state_avg, count(*) AS reports
  FROM mandi.fact_price_report f
  JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
  JOIN mandi.dim_market    m ON m.market_key    = f.market_key
  WHERE f.arrival_date >= cast(current_date - INTERVAL '7' DAY AS varchar)
    AND NOT f.is_outlier
  GROUP BY 1, 2
),
national AS (
  SELECT c.commodity, avg(f.modal_price) AS national_avg
  FROM mandi.fact_price_report f
  JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
  WHERE f.arrival_date >= cast(current_date - INTERVAL '7' DAY AS varchar)
    AND NOT f.is_outlier
  GROUP BY 1
)
SELECT s.commodity, s.state, round(s.state_avg) AS state_avg, round(n.national_avg) AS national_avg,
       round(100.0 * (s.state_avg - n.national_avg) / n.national_avg, 1) AS diff_pct,
       CASE WHEN s.state_avg > n.national_avg * 1.05 THEN 'above'
            WHEN s.state_avg < n.national_avg * 0.95 THEN 'below'
            ELSE 'near' END AS vs_national,
       s.reports
FROM state_avg s
JOIN national n ON n.commodity = s.commodity
ORDER BY s.commodity, diff_pct DESC;
