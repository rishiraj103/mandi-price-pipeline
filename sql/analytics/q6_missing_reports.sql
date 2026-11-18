-- Q6: data completeness — weekdays in the last 14 days on which an active market sent no report at all
WITH spine AS (
  SELECT date_key, full_date
  FROM mandi.dim_date
  WHERE full_date BETWEEN current_date - INTERVAL '14' DAY AND current_date - INTERVAL '1' DAY
    AND NOT is_weekend
),
active_markets AS (  -- markets that reported at least once in the window
  SELECT DISTINCT market_key
  FROM mandi.fact_price_report
  WHERE arrival_date >= cast(cast(current_date - INTERVAL '14' DAY AS date) AS varchar)
),
reported AS (
  SELECT DISTINCT date_key, market_key
  FROM mandi.fact_price_report
  WHERE arrival_date >= cast(cast(current_date - INTERVAL '14' DAY AS date) AS varchar)
),
missing AS (
  SELECT s.full_date, a.market_key
  FROM spine s
  CROSS JOIN active_markets a
  LEFT JOIN reported r ON r.date_key = s.date_key AND r.market_key = a.market_key
  WHERE r.market_key IS NULL
)
SELECT m.state, m.district, m.market, count(*) AS missed_weekdays,
       min(x.full_date) AS first_missed, max(x.full_date) AS last_missed
FROM missing x
JOIN mandi.dim_market m ON m.market_key = x.market_key
GROUP BY 1, 2, 3
ORDER BY missed_weekdays DESC, state, market;
