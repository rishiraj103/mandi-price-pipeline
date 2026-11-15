-- Q2: top 5 cheapest and costliest markets per commodity in each state over the last 7 days
WITH market_avg AS (
  SELECT c.commodity, m.state, m.district, m.market,
         avg(f.modal_price) AS avg_modal_price,
         count(*)           AS reports
  FROM mandi.fact_price_report f
  JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
  JOIN mandi.dim_market    m ON m.market_key    = f.market_key
  WHERE f.arrival_date >= cast(current_date - INTERVAL '7' DAY AS varchar)
    AND NOT f.is_outlier
  GROUP BY 1, 2, 3, 4
),
ranked AS (
  SELECT *,
         DENSE_RANK() OVER (PARTITION BY commodity, state ORDER BY avg_modal_price ASC)  AS cheap_rank,
         DENSE_RANK() OVER (PARTITION BY commodity, state ORDER BY avg_modal_price DESC) AS costly_rank
  FROM market_avg
)
SELECT commodity, state, district, market, round(avg_modal_price) AS avg_modal_price, reports,
       cheap_rank, costly_rank
FROM ranked
WHERE cheap_rank <= 5 OR costly_rank <= 5
ORDER BY commodity, state, avg_modal_price;
