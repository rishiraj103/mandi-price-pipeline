-- NULL, zero/negative or out-of-order prices in the fact (expect 0 rows)
SELECT arrival_date, market_key, commodity_key, min_price, modal_price, max_price
FROM mandi.fact_price_report
WHERE min_price IS NULL OR modal_price IS NULL OR max_price IS NULL
   OR min_price <= 0 OR NOT (min_price <= modal_price AND modal_price <= max_price);
