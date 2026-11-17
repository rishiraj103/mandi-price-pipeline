-- Q7: commodities with the widest price spread inside markets (max - min on the same report), last 30 days
SELECT c.commodity, c.commodity_group,
       round(avg(f.price_spread))                              AS avg_spread,
       round(100.0 * avg(f.price_spread / f.modal_price), 1)   AS avg_spread_pct_of_modal,
       count(*)                                                AS reports
FROM mandi.fact_price_report f
JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
WHERE f.arrival_date >= cast(current_date - INTERVAL '30' DAY AS varchar)
  AND NOT f.is_outlier
GROUP BY 1, 2
HAVING count(*) >= 100
ORDER BY avg_spread_pct_of_modal DESC;
