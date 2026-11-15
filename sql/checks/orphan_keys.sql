-- Fact rows whose market, commodity or date key has no dimension row (expect 0 rows)
SELECT f.arrival_date, f.date_key, f.market_key, f.commodity_key
FROM mandi.fact_price_report f
LEFT JOIN mandi.dim_market    m ON m.market_key    = f.market_key
LEFT JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
LEFT JOIN mandi.dim_date      d ON d.date_key      = f.date_key
WHERE m.market_key IS NULL OR c.commodity_key IS NULL OR d.date_key IS NULL;
