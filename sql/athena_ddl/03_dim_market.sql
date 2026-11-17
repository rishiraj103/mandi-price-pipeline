CREATE EXTERNAL TABLE IF NOT EXISTS mandi.dim_market (
  state      string,
  district   string,
  market     string,
  market_key string,
  region     string
)
STORED AS PARQUET
LOCATION 's3://BUCKET/model/dim_market/';
