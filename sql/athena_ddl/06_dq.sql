-- One small JSON summary per day; unpartitioned because each file already holds its arrival_date
CREATE EXTERNAL TABLE IF NOT EXISTS mandi.dq (
  arrival_date     string,
  rows_read        int,
  rows_passed      int,
  rows_rejected    int,
  by_reason        map<string, int>,
  outliers_flagged int
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://BUCKET/dq/';
