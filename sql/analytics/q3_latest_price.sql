-- Q3: latest available price in each market for each commodity (markets don't report every day; last 30 days)
WITH ranked AS (
  SELECT c.commodity, m.state, m.district, m.market, d.full_date AS price_date,
         f.modal_price, f.min_price, f.max_price, c.variety, c.grade,
         ROW_NUMBER() OVER (PARTITION BY c.commodity, f.market_key
                            ORDER BY f.date_key DESC, f.modal_price) AS rn
  FROM mandi.fact_price_report f
  JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
  JOIN mandi.dim_market    m ON m.market_key    = f.market_key
  JOIN mandi.dim_date      d ON d.date_key      = f.date_key
  WHERE f.arrival_date >= cast(cast(current_date - INTERVAL '30' DAY AS date) AS varchar)
    AND NOT f.is_outlier
)
SELECT commodity, state, district, market, price_date, modal_price, min_price, max_price, variety, grade
FROM ranked
WHERE rn = 1
ORDER BY commodity, state, market;
