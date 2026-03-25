"""
HDBSCAN clustering on products_embedded vectors.

Steps:
  1. Load all 1536-dim embeddings from products_embedded.
  2. Reduce to 50 dims via UMAP (cosine metric) for faster clustering.
  3. Fit HDBSCAN (min_cluster_size=15, min_samples=10, metric='euclidean' on UMAP output).
  4. Label each cluster with GPT-4o-mini (2-5 words, luxury retail style).
  5. Write cluster assignments to products_clustered.
"""
from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import hdbscan
import umap
from google.cloud import bigquery
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import (
    OPENAI_API_KEY,
    GPT_MODEL,
    HDBSCAN_MIN_CLUSTER_SIZE,
    HDBSCAN_MIN_SAMPLES,
    TABLE_EMBEDDED,
    TABLE_CLEAN,
    TABLE_CLUSTERED,
)
from bq_client import get_client

log = logging.getLogger(__name__)

UMAP_N_COMPONENTS = 50
UMAP_N_NEIGHBORS = 30
UMAP_MIN_DIST = 0.0


@dataclass
class EmbeddingRow:
    product_id: int
    embedding: list[float]


def _fetch_embeddings(bq: bigquery.Client) -> list[EmbeddingRow]:
    sql = f"SELECT product_id, embedding FROM `{TABLE_EMBEDDED}` WHERE embedding IS NOT NULL ORDER BY product_id"
    rows = list(bq.query(sql).result())
    log.info("Loaded %d embeddings from BQ", len(rows))
    return [EmbeddingRow(product_id=r.product_id, embedding=list(r.embedding)) for r in rows]


def _fetch_cluster_products(bq: bigquery.Client, cluster_ids: list[int], product_ids: list[int]) -> dict[int, list[str]]:
    """Return {cluster_id: [product names]} for label generation."""
    if not product_ids:
        return {}
    ids_str = ", ".join(str(pid) for pid in product_ids)
    sql = f"""
    SELECT c.product_id, c.name, c.category
    FROM `{TABLE_CLEAN}` c
    WHERE c.product_id IN ({ids_str})
    """
    rows = list(bq.query(sql).result())
    pid_to_info = {r.product_id: f"{r.name} ({r.category})" for r in rows}
    result: dict[int, list[str]] = {}
    for cid, pid in zip(cluster_ids, product_ids):
        if cid not in result:
            result[cid] = []
        if pid in pid_to_info:
            result[cid].append(pid_to_info[pid])
    return result


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _label_cluster(openai_client: OpenAI, product_samples: list[str]) -> str:
    sample_text = "\n".join(f"- {p}" for p in product_samples[:15])
    prompt = (
        "You are a luxury retail brand strategist. "
        "Given these product names, generate a 2-5 word cluster label "
        "that captures their common luxury retail theme. "
        "Reply with ONLY the label, no explanation.\n\n"
        f"Products:\n{sample_text}"
    )
    response = openai_client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=0.3,
    )
    label = response.choices[0].message.content.strip().strip('"').strip("'")
    return label[:100]  # safety cap


def _reduce_dimensions(matrix: np.ndarray) -> np.ndarray:
    log.info("UMAP reduction %s -> %d dims...", matrix.shape, UMAP_N_COMPONENTS)
    reducer = umap.UMAP(
        n_components=UMAP_N_COMPONENTS,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric="cosine",
        random_state=42,
        low_memory=True,
    )
    reduced = reducer.fit_transform(matrix)
    log.info("UMAP done: %s", reduced.shape)
    return reduced


def _cluster_embeddings(reduced: np.ndarray) -> hdbscan.HDBSCAN:
    log.info("Fitting HDBSCAN (min_cluster_size=%d)...", HDBSCAN_MIN_CLUSTER_SIZE)
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    clusterer.fit(reduced)
    unique = set(clusterer.labels_) - {-1}
    noise = (clusterer.labels_ == -1).sum()
    log.info("Clusters found: %d real + %d noise points", len(unique), noise)
    return clusterer


def _write_clusters(
    bq: bigquery.Client,
    product_ids: list[int],
    labels: np.ndarray,
    probabilities: np.ndarray,
    cluster_labels: dict[int, str],
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for pid, cluster_id, prob in zip(product_ids, labels, probabilities):
        cid = int(cluster_id)
        rows.append({
            "product_id": pid,
            "cluster_id": cid,
            "cluster_label": cluster_labels.get(cid) if cid != -1 else None,
            "cluster_probability": float(prob),
            "is_noise": cid == -1,
            "clustering_algorithm": "HDBSCAN",
            "min_cluster_size_param": HDBSCAN_MIN_CLUSTER_SIZE,
            "clustering_created_at": now,
        })

    # Clear existing data then insert
    bq.query(f"DELETE FROM `{TABLE_CLUSTERED}` WHERE TRUE").result()

    # Insert in chunks of 1000
    for i in range(0, len(rows), 1000):
        chunk = rows[i : i + 1000]
        errors = bq.insert_rows_json(TABLE_CLUSTERED, chunk)
        if errors:
            raise RuntimeError(f"BQ insert errors: {errors}")
    log.info("Written %d cluster assignments to BQ", len(rows))


def run(bq: bigquery.Client) -> dict:
    """Cluster all embedded products. Returns stats dict."""
    rows = _fetch_embeddings(bq)
    if len(rows) < HDBSCAN_MIN_CLUSTER_SIZE:
        raise RuntimeError(f"Not enough embeddings to cluster: {len(rows)}")

    product_ids = [r.product_id for r in rows]
    matrix = np.array([r.embedding for r in rows], dtype=np.float32)

    reduced = _reduce_dimensions(matrix)
    clusterer = _cluster_embeddings(reduced)

    labels: np.ndarray = clusterer.labels_
    probabilities: np.ndarray = clusterer.probabilities_

    # Build cluster_id -> list[product_id] mapping (sample for labelling)
    cluster_to_pids: dict[int, list[int]] = {}
    for pid, cid in zip(product_ids, labels):
        cid = int(cid)
        if cid == -1:
            continue
        cluster_to_pids.setdefault(cid, []).append(pid)

    # Fetch product names for labelling
    sample_pids = [pids[:20][0] for pids in cluster_to_pids.values()]
    all_pids_for_names = [pid for pids in cluster_to_pids.values() for pid in pids[:20]]
    cluster_id_for_pid = {}
    for cid, pids in cluster_to_pids.items():
        for pid in pids[:20]:
            cluster_id_for_pid[pid] = cid

    pid_to_info = {}
    if all_pids_for_names:
        ids_str = ", ".join(str(p) for p in all_pids_for_names)
        sql = f"SELECT product_id, name, category FROM `{TABLE_CLEAN}` WHERE product_id IN ({ids_str})"
        for r in bq.query(sql).result():
            pid_to_info[r.product_id] = f"{r.name} ({r.category})"

    cluster_products: dict[int, list[str]] = {}
    for pid, cid in cluster_id_for_pid.items():
        cluster_products.setdefault(cid, []).append(pid_to_info.get(pid, ""))

    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    cluster_labels: dict[int, str] = {}
    for cid, samples in cluster_products.items():
        label = _label_cluster(openai_client, [s for s in samples if s])
        cluster_labels[cid] = label
        log.info("Cluster %d labelled: %s (%d products)", cid, label, len(cluster_to_pids[cid]))

    _write_clusters(bq, product_ids, labels, probabilities, cluster_labels)

    unique_clusters = len(set(labels) - {-1})
    noise_count = int((labels == -1).sum())
    stats = {
        "clusters": unique_clusters,
        "noise_points": noise_count,
        "total_products": len(product_ids),
    }
    log.info("Clustering complete: %s", stats)
    return stats
