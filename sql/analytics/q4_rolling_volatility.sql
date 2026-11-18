-- Q4: national daily average modal price per commodity, its 7-day rolling average and 7-day volatility
WITH daily AS (
  SELECT c.commodity, d.full_date, avg(f.modal_price) AS avg_modal_price, count(*) AS reports
  FROM mandi.fact_price_report f
  JOIN mandi.dim_commodity c ON c.commodity_key = f.commodity_key
  JOIN mandi.dim_date      d ON d.date_key      = f.date_key
  WHERE f.arrival_date >= cast(cast(current_date - INTERVAL '60' DAY AS date) AS varchar)
    AND NOT f.is_outlier
  GROUP BY 1, 2
)
SELECT commodity, full_date, round(avg_modal_price) AS avg_modal_price, reports,
       round(avg(avg_modal_price) OVER (PARTITION BY commodity ORDER BY full_date
                                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)) AS rolling_7d_avg,
       round(stddev_samp(avg_modal_price) OVER (PARTITION BY commodity ORDER BY full_date
                                                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)) AS rolling_7d_stddev
FROM daily
ORDER BY commodity, full_date;
