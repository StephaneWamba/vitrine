-- Vitrine — Looker Studio views
-- Six materialised views that power the six Looker Studio charts.
-- Each view is named looker_* for easy identification in the BQ console.

-- ─────────────────────────────────────────────────────────────────────
-- Chart 1: Cluster distribution (treemap)
--   Dimensions: cluster_label
--   Metric:     product_count
-- ─────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW `vitrine-wamba-2026.vitrine_dataset.looker_cluster_distribution` AS
SELECT
  cl.cluster_id,
  cl.cluster_label,
  COUNT(DISTINCT cl.product_id)            AS product_count,
  ROUND(AVG(c.retail_price), 2)            AS avg_price
FROM `vitrine-wamba-2026.vitrine_dataset.products_clustered` cl
JOIN `vitrine-wamba-2026.vitrine_dataset.products_clean`     c
  USING (product_id)
WHERE cl.cluster_id != -1
GROUP BY cl.cluster_id, cl.cluster_label
ORDER BY product_count DESC;

-- ─────────────────────────────────────────────────────────────────────
-- Chart 2: Top brands per cluster (bar chart)
--   Dimensions: cluster_label, brand
--   Metric:     product_count
-- ─────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW `vitrine-wamba-2026.vitrine_dataset.looker_brands_per_cluster` AS
SELECT
  cl.cluster_label,
  c.brand,
  COUNT(DISTINCT c.product_id) AS product_count
FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`     c
JOIN `vitrine-wamba-2026.vitrine_dataset.products_clustered` cl
  USING (product_id)
WHERE cl.cluster_id != -1
GROUP BY cl.cluster_label, c.brand
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY cl.cluster_label
  ORDER BY COUNT(DISTINCT c.product_id) DESC
) <= 10
ORDER BY cl.cluster_label, product_count DESC;

-- ─────────────────────────────────────────────────────────────────────
-- Chart 3: Average price per cluster (bar chart)
--   Dimensions: cluster_label
--   Metrics:    avg_price, price_min, price_max
-- ─────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW `vitrine-wamba-2026.vitrine_dataset.looker_pricing_per_cluster` AS
SELECT
  cl.cluster_label,
  COUNT(DISTINCT c.product_id)   AS product_count,
  ROUND(AVG(c.retail_price), 2)  AS avg_price,
  MIN(c.retail_price)            AS price_min,
  MAX(c.retail_price)            AS price_max,
  ROUND(STDDEV(c.retail_price), 2) AS price_stddev
FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`     c
JOIN `vitrine-wamba-2026.vitrine_dataset.products_clustered` cl
  USING (product_id)
WHERE cl.cluster_id != -1
GROUP BY cl.cluster_label
ORDER BY avg_price DESC;

-- ─────────────────────────────────────────────────────────────────────
-- Chart 4: Data completeness gauge
--   Metrics: completeness_pct, total_records, valid_records
-- ─────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW `vitrine-wamba-2026.vitrine_dataset.looker_data_quality` AS
SELECT
  report_timestamp,
  total_records,
  valid_records,
  completeness_pct,
  field_name_completeness,
  field_brand_completeness,
  field_cat_completeness,
  field_price_completeness,
  price_mean,
  price_min,
  price_max
FROM `vitrine-wamba-2026.vitrine_dataset.quality_report`
ORDER BY report_timestamp DESC
LIMIT 1;

-- ─────────────────────────────────────────────────────────────────────
-- Chart 5: Sales volume per cluster over time (time series)
--   Dimensions: sale_date, cluster_label
--   Metric:     sales_count, sales_revenue
-- ─────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW `vitrine-wamba-2026.vitrine_dataset.looker_sales_timeline` AS
SELECT
  DATE(oi.created_at)          AS sale_date,
  cl.cluster_label,
  COUNT(DISTINCT oi.order_id)  AS sales_count,
  SUM(CAST(oi.sale_price AS FLOAT64)) AS sales_revenue
FROM `bigquery-public-data.thelook_ecommerce.order_items`    oi
JOIN `vitrine-wamba-2026.vitrine_dataset.products_clean`     c
  ON oi.product_id = c.product_id
JOIN `vitrine-wamba-2026.vitrine_dataset.products_clustered` cl
  ON c.product_id = cl.product_id
WHERE oi.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 180 DAY)
  AND cl.cluster_id != -1
GROUP BY sale_date, cl.cluster_label
ORDER BY sale_date DESC, sales_count DESC;

-- ─────────────────────────────────────────────────────────────────────
-- Chart 6: Category × Department heatmap
--   Dimensions: category (rows), department (columns)
--   Metric:     product_count, avg_price
-- ─────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW `vitrine-wamba-2026.vitrine_dataset.looker_heatmap_cat_dept` AS
SELECT
  category,
  department,
  COUNT(DISTINCT product_id)    AS product_count,
  ROUND(AVG(retail_price), 2)   AS avg_price
FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
GROUP BY category, department
ORDER BY category, department;
