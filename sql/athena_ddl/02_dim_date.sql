CREATE EXTERNAL TABLE IF NOT EXISTS mandi.dim_date (
  date_key   int,
  full_date  date,
  day        int,
  iso_week   int,
  month      int,
  quarter    int,
  year       int,
  weekday    string,
  is_weekend boolean
)
STORED AS PARQUET
LOCATION 's3://BUCKET/model/dim_date/';
