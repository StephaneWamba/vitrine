-- Vitrine — Transform layer
-- Reads products_raw and produces products_clean:
--   • Normalises strings (UPPER + TRIM)
--   • Imputes missing brand → "UNBRANDED", department → "GENERAL"
--   • Imputes invalid prices with category-wise median
--   • Caps cost at retail_price if cost > retail_price
--   • Computes margin_pct
--   • Sets is_valid flag + collects validation_errors as JSON array

CREATE OR REPLACE TABLE `vitrine-wamba-2026.vitrine_dataset.products_clean` AS

WITH normalised AS (
  SELECT
    product_id,
    UPPER(TRIM(name))                                      AS name,
    UPPER(TRIM(COALESCE(NULLIF(TRIM(brand), ''), 'UNBRANDED')))       AS brand,
    UPPER(TRIM(category))                                  AS category,
    UPPER(TRIM(COALESCE(NULLIF(TRIM(department), ''), 'GENERAL')))    AS department,
    retail_price,
    cost,
    created_at                                             AS source_created_at
  FROM `vitrine-wamba-2026.vitrine_dataset.products_raw`
),

-- Category-level median price used to impute NULL / invalid retail prices
category_medians AS (
  SELECT
    category,
    APPROX_QUANTILES(retail_price, 2)[OFFSET(1)] AS median_price
  FROM `vitrine-wamba-2026.vitrine_dataset.products_raw`
  WHERE retail_price > 0
    AND retail_price < 100000
  GROUP BY category
),

imputed AS (
  SELECT
    n.product_id,
    n.name,
    n.brand,
    n.category,
    n.department,
    n.source_created_at,

    -- Retail price: use value if valid, else category median
    CASE
      WHEN n.retail_price > 0 AND n.retail_price < 100000
        THEN n.retail_price
      ELSE COALESCE(cm.median_price, 9.99)   -- fallback $9.99 if no median
    END AS retail_price,

    -- Cost: 0 if NULL/negative; cap at retail_price if cost > retail_price
    CASE
      WHEN n.cost IS NULL OR n.cost < 0
        THEN 0.0
      WHEN n.cost > CASE
                      WHEN n.retail_price > 0 AND n.retail_price < 100000
                        THEN n.retail_price
                      ELSE COALESCE(cm.median_price, 9.99)
                    END
        THEN CASE
               WHEN n.retail_price > 0 AND n.retail_price < 100000
                 THEN n.retail_price * 0.5
               ELSE COALESCE(cm.median_price, 9.99) * 0.5
             END
      ELSE n.cost
    END AS cost

  FROM normalised n
  LEFT JOIN category_medians cm USING (category)
),

with_margin AS (
  SELECT
    *,
    CASE
      WHEN retail_price > 0
        THEN ROUND((retail_price - cost) / retail_price * 100, 2)
      ELSE NULL
    END AS margin_pct
  FROM imputed
),

with_validation AS (
  SELECT
    *,
    -- is_valid = TRUE only when all fields satisfy business rules
    (
      name     IS NOT NULL AND name     != ''
      AND brand    IS NOT NULL AND brand    != ''
      AND category IS NOT NULL AND category != ''
      AND department IS NOT NULL AND department != ''
      AND retail_price > 0
      AND retail_price < 100000
      AND cost        >= 0
      AND cost        <= retail_price
    ) AS is_valid,

    -- Collect error codes as JSON array (NULL when clean)
    NULLIF(
      TO_JSON_STRING(
        ARRAY_CONCAT(
          IF(name IS NULL OR name = '',                       ['ERR_MISSING_NAME'],       []),
          IF(retail_price <= 0,                               ['ERR_INVALID_PRICE'],      []),
          IF(retail_price >= 100000,                          ['ERR_PRICE_TOO_HIGH'],     []),
          IF(cost < 0,                                        ['ERR_NEGATIVE_COST'],      []),
          IF(cost > retail_price AND cost IS NOT NULL,        ['ERR_COST_GT_PRICE'],      [])
        )
      ),
      '[]'
    ) AS validation_errors
  FROM with_margin
)

SELECT
  product_id,
  name,
  brand,
  category,
  department,
  retail_price,
  cost,
  margin_pct,
  is_valid,
  validation_errors,
  CURRENT_TIMESTAMP() AS cleaned_at,
  source_created_at
FROM with_validation
ORDER BY product_id;

-- ── Verification ─────────────────────────────────────────────────────
SELECT
  COUNT(*)                                  AS total_rows,
  COUNTIF(is_valid = TRUE)                  AS valid_rows,
  COUNTIF(is_valid = FALSE)                 AS invalid_rows,
  ROUND(100.0 * COUNTIF(is_valid) / COUNT(*), 2) AS validity_pct,
  COUNTIF(brand = 'UNBRANDED')              AS unbranded_count,
  COUNTIF(department = 'GENERAL')           AS general_dept_count,
  MIN(retail_price)                         AS price_min,
  MAX(retail_price)                         AS price_max,
  ROUND(AVG(retail_price), 2)               AS price_avg
FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`;
