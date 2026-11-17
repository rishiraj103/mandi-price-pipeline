-- Partition projection: every arrival_date from 2023 is queryable with no crawler or MSCK REPAIR
CREATE EXTERNAL TABLE IF NOT EXISTS mandi.fact_price_report (
  date_key      int,
  market_key    string,
  commodity_key string,
  min_price     double,
  max_price     double,
  modal_price   double,
  price_spread  double,
  is_outlier    boolean,
  load_date     string
)
PARTITIONED BY (arrival_date string)
STORED AS PARQUET
LOCATION 's3://BUCKET/model/fact_price_report/'
TBLPROPERTIES (
  'projection.enabled'                 = 'true',
  'projection.arrival_date.type'       = 'date',
  'projection.arrival_date.format'     = 'yyyy-MM-dd',
  'projection.arrival_date.range'      = '2023-01-01,NOW',
  'projection.arrival_date.interval'   = '1',
  'projection.arrival_date.interval.unit' = 'DAYS',
  'storage.location.template'          = 's3://BUCKET/model/fact_price_report/arrival_date=${arrival_date}/'
);
