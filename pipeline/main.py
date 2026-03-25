"""
Vitrine pipeline entrypoint — Cloud Run Job.

Execution order:
  1. Register pipeline run (idempotency guard).
  2. Embeddings (incremental — skips already embedded products).
  3. Clustering (full re-fit every run).
  4. Enrichment (incremental — skips already enriched products).
  5. Mark run as COMPLETE.

Idempotency: a new run_id (UUID) is generated each invocation.
Existing embeddings and descriptions are never re-generated.
"""
from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime, timezone

from google.cloud import bigquery

import embeddings
import clustering
import enrichment
from bq_client import get_client
from config import TABLE_RUNS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("pipeline.main")


def _start_run(bq: bigquery.Client, run_id: str) -> None:
    row = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "status": "IN_PROGRESS",
        "products_processed": None,
        "clusters_created": None,
        "error_message": None,
    }
    errors = bq.insert_rows_json(TABLE_RUNS, [row])
    if errors:
        raise RuntimeError(f"Failed to register pipeline run: {errors}")
    log.info("Run %s started", run_id)


def _finish_run(bq: bigquery.Client, run_id: str, stats: dict) -> None:
    sql = f"""
    UPDATE `{TABLE_RUNS}`
    SET
      status             = 'COMPLETE',
      completed_at       = CURRENT_TIMESTAMP(),
      products_processed = {stats.get('embedded', 0)},
      clusters_created   = {stats.get('clusters', 0)}
    WHERE run_id = '{run_id}'
    """
    bq.query(sql).result()
    log.info("Run %s marked COMPLETE", run_id)


def _fail_run(bq: bigquery.Client, run_id: str, error: str) -> None:
    safe = error.replace("'", "\\'")[:500]
    sql = f"""
    UPDATE `{TABLE_RUNS}`
    SET
      status        = 'FAILED',
      completed_at  = CURRENT_TIMESTAMP(),
      error_message = '{safe}'
    WHERE run_id = '{run_id}'
    """
    try:
        bq.query(sql).result()
    except Exception as e:
        log.error("Could not mark run as FAILED: %s", e)
    log.error("Run %s FAILED: %s", run_id, error)


def main() -> None:
    run_id = str(uuid.uuid4())
    bq = get_client()
    stats: dict = {}

    _start_run(bq, run_id)

    try:
        log.info("=== Step 1/3: Embeddings ===")
        embed_stats = embeddings.run(bq)
        stats.update(embed_stats)

        log.info("=== Step 2/3: Clustering ===")
        cluster_stats = clustering.run(bq)
        stats.update(cluster_stats)

        log.info("=== Step 3/3: Enrichment ===")
        enrich_stats = enrichment.run(bq)
        stats.update(enrich_stats)

        _finish_run(bq, run_id, stats)
        log.info("Pipeline complete. Stats: %s", stats)

    except Exception as exc:
        _fail_run(bq, run_id, str(exc))
        raise


if __name__ == "__main__":
    main()
