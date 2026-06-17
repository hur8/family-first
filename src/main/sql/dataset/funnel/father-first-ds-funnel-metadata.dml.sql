# Studio > father-first > Datasets > funnel
# https://console.cloud.google.com/bigquery?hl=en&project=father-first&ws=!1m5!1m4!3m2!1sfather-first!2sfunnel!23sRESOURCE_LIST
# count of tables
SELECT COUNT(DISTINCT(table_name)) AS num_tables FROM `father-first.funnel.INFORMATION_SCHEMA.COLUMNS`;
# table names
SELECT DISTINCT(table_name) FROM `father-first.funnel.INFORMATION_SCHEMA.COLUMNS` ORDER BY table_name ;

# tables with name "paid"
SELECT DISTINCT(table_name) FROM `father-first.funnel.INFORMATION_SCHEMA.COLUMNS` WHERE table_name LIKE '%paid%' ORDER BY table_name ;

# schema for all tables
SELECT table_name, column_name, ordinal_position, data_type, is_nullable FROM `father-first.funnel.INFORMATION_SCHEMA.COLUMNS` ORDER by table_name, ordinal_position;
SELECT
  table_name,
  COUNT(column_name) AS column_count
FROM
  `father-first.funnel.INFORMATION_SCHEMA.COLUMNS`
GROUP BY
  table_name
ORDER BY
  table_name;



