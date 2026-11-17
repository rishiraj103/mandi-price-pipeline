CREATE EXTERNAL TABLE IF NOT EXISTS mandi.dim_commodity (
  commodity       string,
  variety         string,
  grade           string,
  commodity_code  int,
  commodity_key   string,
  commodity_group string
)
STORED AS PARQUET
LOCATION 's3://BUCKET/model/dim_commodity/';
