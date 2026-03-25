-- Vitrine — VECTOR_SEARCH index
-- Creates a SCANN approximate-nearest-neighbour index on products_embedded.embedding.
-- Run AFTER the pipeline has populated products_embedded with 1536-dim vectors.
-- BigQuery requires the table to have at least 5,000 rows before creating a vector index.

-- Drop existing index if schema changed and you need to rebuild
-- DROP VECTOR INDEX IF EXISTS `vitrine-wamba-2026.vitrine_dataset.products_embedded`.idx_embedding;

CREATE VECTOR INDEX IF NOT EXISTS idx_embedding
ON `vitrine-wamba-2026.vitrine_dataset.products_embedded`(embedding)
OPTIONS (
  index_type      = 'IVF',         -- Inverted File index (GCP recommends IVF for > 5k rows)
  distance_type   = 'COSINE',      -- Cosine similarity for normalised embedding spaces
  ivf_options     = '{"numLists": 100}'  -- 100 centroids; tune upward for > 1M rows
);

-- ── Verify the index was created ─────────────────────────────────────
SELECT
  index_name,
  table_name,
  index_status,
  coverage_percentage
FROM `vitrine-wamba-2026.vitrine_dataset.INFORMATION_SCHEMA.VECTOR_INDEXES`
WHERE table_name = 'products_embedded';
