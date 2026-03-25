-- Vitrine -- Staging layer
-- Copies raw product data from BigQuery public dataset into vitrine_dataset.products_raw
-- Deduplicates on product_id (keeps lowest cost record when duplicated).
-- Filters out rows missing mandatory fields (product_id, name, category).
--
-- Source schema: id, cost, category, name, brand, retail_price, department, sku, distribution_center_id
-- No created_at column in the public dataset.

CREATE OR REPLACE TABLE `vitrine-wamba-2026.vitrine_dataset.products_raw` AS

WITH source AS (
  SELECT
    CAST(id           AS INT64)   AS product_id,
    CAST(name         AS STRING)  AS name,
    CAST(brand        AS STRING)  AS brand,
    CAST(category     AS STRING)  AS category,
    CAST(department   AS STRING)  AS department,
    CAST(retail_price AS FLOAT64) AS retail_price,
    CAST(cost         AS FLOAT64) AS cost,
    CAST(NULL AS TIMESTAMP)       AS created_at   -- not available in source
  FROM `bigquery-public-data.thelook_ecommerce.products`
  WHERE id       IS NOT NULL
    AND name     IS NOT NULL
    AND name     != ''
    AND category IS NOT NULL
    AND category != ''
),

deduped AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY product_id
      ORDER BY cost ASC NULLS LAST
    ) AS _rn
  FROM source
)

SELECT
  product_id,
  name,
  brand,
  category,
  department,
  retail_price,
  cost,
  created_at,
  CURRENT_DATE() AS ingestion_date
FROM deduped
WHERE _rn = 1
ORDER BY product_id;

-- Verification
SELECT
  COUNT(*)                                      AS total_rows,
  COUNTIF(product_id IS NULL)                   AS null_product_ids,
  COUNTIF(name       IS NULL OR name = '')      AS null_names,
  COUNTIF(category   IS NULL OR category = '')  AS null_categories,
  COUNT(DISTINCT product_id)                    AS distinct_product_ids
FROM `vitrine-wamba-2026.vitrine_dataset.products_raw`;
