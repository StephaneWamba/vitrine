-- Vitrine — Quality checks & assertions
-- Run after each pipeline execution. Enforces 12 data quality rules.
-- Populates quality_report with the latest metrics snapshot.

-- ═══════════════════════════════════════════════════════════════════
-- SECTION A — products_clean assertions
-- ═══════════════════════════════════════════════════════════════════

-- Assert 1: No duplicate product_ids in products_clean
ASSERT NOT EXISTS (
  SELECT product_id
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
  GROUP BY product_id
  HAVING COUNT(*) > 1
) AS 'ASSERT_01: Duplicate product_ids found in products_clean';

-- Assert 2: Mandatory fields are never NULL/empty in products_clean
ASSERT (
  SELECT COUNT(*)
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
  WHERE name       IS NULL OR name       = ''
     OR brand      IS NULL OR brand      = ''
     OR category   IS NULL OR category   = ''
     OR department IS NULL OR department = ''
) = 0 AS 'ASSERT_02: NULL or empty mandatory fields in products_clean';

-- Assert 3: No negative prices
ASSERT NOT EXISTS (
  SELECT product_id
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
  WHERE retail_price < 0 OR cost < 0
) AS 'ASSERT_03: Negative retail_price or cost in products_clean';

-- Assert 4: Cost never exceeds retail_price for valid records
ASSERT NOT EXISTS (
  SELECT product_id
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
  WHERE is_valid = TRUE
    AND cost > retail_price
) AS 'ASSERT_04: Cost exceeds retail_price in valid records';

-- Assert 5: Retail price within plausible range ($0.01 – $99,999)
ASSERT NOT EXISTS (
  SELECT product_id
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
  WHERE retail_price <= 0
     OR retail_price >= 100000
) AS 'ASSERT_05: retail_price outside [0.01, 99999] range';

-- ═══════════════════════════════════════════════════════════════════
-- SECTION B — products_embedded assertions
-- ═══════════════════════════════════════════════════════════════════

-- Assert 6: Embedding coverage ≥ 95% of products_clean
ASSERT (
  SELECT COUNT(*)
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean` c
  LEFT JOIN `vitrine-wamba-2026.vitrine_dataset.products_embedded` e
    ON c.product_id = e.product_id
  WHERE e.product_id IS NULL
) <= (
  SELECT CAST(CEIL(0.05 * COUNT(*)) AS INT64)
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
) AS 'ASSERT_06: Embedding coverage below 95%';

-- Assert 7: All embedding vectors are exactly 1536-dimensional
ASSERT NOT EXISTS (
  SELECT product_id
  FROM `vitrine-wamba-2026.vitrine_dataset.products_embedded`
  WHERE ARRAY_LENGTH(embedding) != 1536
) AS 'ASSERT_07: Embedding vector length != 1536';

-- Assert 8: No NULL embeddings
ASSERT NOT EXISTS (
  SELECT product_id
  FROM `vitrine-wamba-2026.vitrine_dataset.products_embedded`
  WHERE embedding IS NULL
) AS 'ASSERT_08: NULL embedding found in products_embedded';

-- ═══════════════════════════════════════════════════════════════════
-- SECTION C — products_clustered assertions
-- ═══════════════════════════════════════════════════════════════════

-- Assert 9: Clustering coverage ≥ 80% (noise / unclustered allowed ≤ 20%)
ASSERT (
  SELECT COUNT(*)
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean` c
  LEFT JOIN `vitrine-wamba-2026.vitrine_dataset.products_clustered` cl
    ON c.product_id = cl.product_id
  WHERE cl.product_id IS NULL
) <= (
  SELECT CAST(CEIL(0.20 * COUNT(*)) AS INT64)
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
) AS 'ASSERT_09: Clustering coverage below 80%';

-- Assert 10: Every assigned cluster has at least 15 products (HDBSCAN min_cluster_size)
ASSERT NOT EXISTS (
  SELECT cluster_id
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clustered`
  WHERE cluster_id != -1
  GROUP BY cluster_id
  HAVING COUNT(*) < 15
) AS 'ASSERT_10: Cluster smaller than min_cluster_size=15 found';

-- Assert 11: At least 10 real clusters exist (sanity: HDBSCAN didn't collapse)
ASSERT (
  SELECT COUNT(DISTINCT cluster_id)
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clustered`
  WHERE cluster_id != -1
) >= 10 AS 'ASSERT_11: Fewer than 10 clusters — check embedding quality';

-- ═══════════════════════════════════════════════════════════════════
-- SECTION D — products_enriched assertions
-- ═══════════════════════════════════════════════════════════════════

-- Assert 12: Enrichment coverage ≥ 95%
ASSERT (
  SELECT COUNT(*)
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean` c
  LEFT JOIN `vitrine-wamba-2026.vitrine_dataset.products_enriched` en
    ON c.product_id = en.product_id
  WHERE en.product_id IS NULL
) <= (
  SELECT CAST(CEIL(0.05 * COUNT(*)) AS INT64)
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
) AS 'ASSERT_12: Enrichment coverage below 95%';

-- ═══════════════════════════════════════════════════════════════════
-- SECTION E — Populate quality_report snapshot
-- ═══════════════════════════════════════════════════════════════════

INSERT INTO `vitrine-wamba-2026.vitrine_dataset.quality_report`
SELECT
  CURRENT_TIMESTAMP()                                                      AS report_timestamp,
  COUNT(*)                                                                 AS total_records,
  SUM(IF(is_valid, 1, 0))                                                  AS valid_records,
  ROUND(100.0 * SUM(IF(is_valid, 1, 0)) / COUNT(*), 2)                    AS completeness_pct,
  SUM(IF(name     IS NOT NULL AND name     != '', 1, 0))                   AS field_name_completeness,
  SUM(IF(brand    IS NOT NULL AND brand    != '', 1, 0))                   AS field_brand_completeness,
  SUM(IF(category IS NOT NULL AND category != '', 1, 0))                   AS field_cat_completeness,
  SUM(IF(retail_price > 0,                        1, 0))                   AS field_price_completeness,
  ROUND(AVG(retail_price), 2)                                              AS price_mean,
  ROUND(STDDEV(retail_price), 2)                                           AS price_stddev,
  MIN(retail_price)                                                        AS price_min,
  MAX(retail_price)                                                        AS price_max
FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`;

-- ── Pipeline coverage cross-table report ─────────────────────────────
SELECT
  'products_clean'    AS layer, COUNT(*) AS record_count
  FROM `vitrine-wamba-2026.vitrine_dataset.products_clean`
UNION ALL
SELECT 'products_embedded',  COUNT(*) FROM `vitrine-wamba-2026.vitrine_dataset.products_embedded`
UNION ALL
SELECT 'products_clustered', COUNT(*) FROM `vitrine-wamba-2026.vitrine_dataset.products_clustered`
UNION ALL
SELECT 'products_enriched',  COUNT(*) FROM `vitrine-wamba-2026.vitrine_dataset.products_enriched`
ORDER BY layer;
