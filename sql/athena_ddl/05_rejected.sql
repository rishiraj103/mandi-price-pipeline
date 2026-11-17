-- Rejected rows keep their original values as text, plus the rule that rejected them
CREATE EXTERNAL TABLE IF NOT EXISTS mandi.rejected (
  reported_date  string,
  state          string,
  district       string,
  market         string,
  commodity      string,
  commodity_code string,
  variety        string,
  grade          string,
  min_price      string,
  max_price      string,
  modal_price    string,
  reject_reason  string
)
PARTITIONED BY (arrival_date string)
STORED AS PARQUET
LOCATION 's3://BUCKET/rejected/'
TBLPROPERTIES (
  'projection.enabled'                 = 'true',
  'projection.arrival_date.type'       = 'date',
  'projection.arrival_date.format'     = 'yyyy-MM-dd',
  'projection.arrival_date.range'      = '2023-01-01,NOW',
  'projection.arrival_date.interval'   = '1',
  'projection.arrival_date.interval.unit' = 'DAYS',
  'storage.location.template'          = 's3://BUCKET/rejected/arrival_date=${arrival_date}/'
);
