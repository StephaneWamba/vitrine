"""
Generate OpenAI text-embedding-3-small vectors for every product in products_clean
and write results to products_embedded.

Strategy:
  - Fetch products not yet in products_embedded (incremental).
  - Build an embedding_text string per product: "name | brand | category | department".
  - Send requests in batches of EMBEDDING_BATCH_SIZE with exponential back-off.
  - Write results to BQ via streaming insert.
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generator

from google.cloud import bigquery
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    TABLE_CLEAN,
    TABLE_EMBEDDED,
)
from bq_client import get_client

log = logging.getLogger(__name__)

EMBEDDING_COST_PER_TOKEN = 0.00000002  # $0.02 / 1M tokens


@dataclass
class ProductRow:
    product_id: int
    name: str
    brand: str
    category: str
    department: str


def _build_embedding_text(p: ProductRow) -> str:
    return f"{p.name} | {p.brand} | {p.category} | {p.department}"


def _fetch_unembedded(client: bigquery.Client) -> list[ProductRow]:
    sql = f"""
    SELECT
      c.product_id,
      c.name,
      c.brand,
      c.category,
      c.department
    FROM `{TABLE_CLEAN}` c
    LEFT JOIN `{TABLE_EMBEDDED}` e USING (product_id)
    WHERE e.product_id IS NULL
    ORDER BY c.product_id
    """
    rows = list(client.query(sql).result())
    log.info("Products pending embedding: %d", len(rows))
    return [ProductRow(**dict(r.items())) for r in rows]


def _batches(items: list, size: int) -> Generator[list, None, None]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _embed_batch(openai_client: OpenAI, texts: list[str]) -> tuple[list[list[float]], int]:
    """Call OpenAI embeddings API with retry. Returns (vectors, total_tokens)."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    vectors = [item.embedding for item in response.data]
    tokens = response.usage.total_tokens
    return vectors, tokens


def _insert_rows(
    bq: bigquery.Client,
    products: list[ProductRow],
    texts: list[str],
    vectors: list[list[float]],
    tokens_per_item: list[int],
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for product, text, vector, tokens in zip(products, texts, vectors, tokens_per_item):
        cost = tokens * EMBEDDING_COST_PER_TOKEN
        rows.append({
            "product_id": product.product_id,
            "embedding_text": text,
            "embedding": vector,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_tokens": tokens,
            "embedding_cost_usd": cost,
            "embedding_created_at": now,
        })
    errors = bq.insert_rows_json(TABLE_EMBEDDED, rows)
    if errors:
        raise RuntimeError(f"BQ insert errors: {errors}")


def run(bq: bigquery.Client) -> dict:
    """Embed all unembedded products. Returns stats dict."""
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    products = _fetch_unembedded(bq)

    if not products:
        log.info("No products to embed — skipping.")
        return {"embedded": 0, "total_tokens": 0, "total_cost_usd": 0.0}

    total_tokens = 0
    total_cost = 0.0
    embedded = 0

    for batch in _batches(products, EMBEDDING_BATCH_SIZE):
        texts = [_build_embedding_text(p) for p in batch]
        vectors, batch_tokens = _embed_batch(openai_client, texts)

        # Distribute tokens evenly across items in the batch
        tokens_each = [batch_tokens // len(batch)] * len(batch)
        tokens_each[-1] += batch_tokens - sum(tokens_each)

        _insert_rows(bq, batch, texts, vectors, tokens_each)

        total_tokens += batch_tokens
        total_cost += batch_tokens * EMBEDDING_COST_PER_TOKEN
        embedded += len(batch)
        log.info("Embedded %d/%d products (batch tokens: %d)", embedded, len(products), batch_tokens)

        # Polite delay between batches
        time.sleep(0.3)

    stats = {"embedded": embedded, "total_tokens": total_tokens, "total_cost_usd": total_cost}
    log.info("Embedding complete: %s", stats)
    return stats
