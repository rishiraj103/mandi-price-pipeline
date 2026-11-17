-- Duplicate natural keys in the fact (one report per date x market x commodity/variety/grade) and dims (expect 0 rows)
SELECT 'fact_price_report' AS tbl, arrival_date || '|' || market_key || '|' || commodity_key AS natural_key, count(*) AS n
FROM mandi.fact_price_report
GROUP BY 1, 2 HAVING count(*) > 1
UNION ALL
SELECT 'dim_market', state || '|' || district || '|' || market, count(*)
FROM mandi.dim_market GROUP BY 1, 2 HAVING count(*) > 1
UNION ALL
SELECT 'dim_commodity', commodity || '|' || variety || '|' || grade, count(*)
FROM mandi.dim_commodity GROUP BY 1, 2 HAVING count(*) > 1;
