"""
GPT-4o-mini product description enrichment.

For every product in products_clean (not yet in products_enriched):
  - Build a prompt using name, brand, category, cluster_label.
  - Generate a 50-word luxury retail description.
  - Write to products_enriched.
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from google.cloud import bigquery
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import (
    OPENAI_API_KEY,
    GPT_MODEL,
    GPT_CLUSTER_LABEL_TONE,
    GPT_DESCRIPTION_WORDS,
    TABLE_CLEAN,
    TABLE_CLUSTERED,
    TABLE_ENRICHED,
)

log = logging.getLogger(__name__)

ENRICHMENT_COST_IN_PER_TOKEN = 0.00000015   # $0.15 / 1M input tokens
ENRICHMENT_COST_OUT_PER_TOKEN = 0.00000060  # $0.60 / 1M output tokens
BATCH_SIZE = 20  # GPT calls per second upper bound


@dataclass
class ProductToEnrich:
    product_id: int
    name: str
    brand: str
    category: str
    department: str
    cluster_id: Optional[int]
    cluster_label: Optional[str]


def _fetch_unenriched(bq: bigquery.Client) -> list[ProductToEnrich]:
    sql = f"""
    SELECT
      c.product_id,
      c.name,
      c.brand,
      c.category,
      c.department,
      cl.cluster_id,
      cl.cluster_label
    FROM `{TABLE_CLEAN}` c
    LEFT JOIN `{TABLE_CLUSTERED}` cl USING (product_id)
    LEFT JOIN `{TABLE_ENRICHED}` en USING (product_id)
    WHERE en.product_id IS NULL
    ORDER BY c.product_id
    """
    rows = list(bq.query(sql).result())
    log.info("Products pending enrichment: %d", len(rows))
    return [ProductToEnrich(**dict(r.items())) for r in rows]


def _build_prompt(p: ProductToEnrich) -> str:
    cluster_info = f"Cluster: {p.cluster_label}." if p.cluster_label else ""
    return (
        f"You are a luxury retail copywriter. Write exactly {GPT_DESCRIPTION_WORDS} words "
        f"describing this product in an aspirational, {GPT_CLUSTER_LABEL_TONE} tone. "
        f"No bullet points. No markdown. Just flowing prose.\n\n"
        f"Product: {p.name}\n"
        f"Brand: {p.brand}\n"
        f"Category: {p.category} / {p.department}\n"
        f"{cluster_info}"
    )


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _call_gpt(openai_client: OpenAI, prompt: str) -> tuple[str, int, int]:
    """Returns (description, input_tokens, output_tokens)."""
    response = openai_client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.7,
    )
    text = response.choices[0].message.content.strip()
    return text, response.usage.prompt_tokens, response.usage.completion_tokens


def _insert_rows(bq: bigquery.Client, rows: list[dict]) -> None:
    errors = bq.insert_rows_json(TABLE_ENRICHED, rows)
    if errors:
        raise RuntimeError(f"BQ insert errors: {errors}")


def run(bq: bigquery.Client) -> dict:
    """Enrich all un-enriched products. Returns stats dict."""
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    products = _fetch_unenriched(bq)

    if not products:
        log.info("No products to enrich — skipping.")
        return {"enriched": 0, "total_cost_usd": 0.0}

    enriched = 0
    total_cost = 0.0
    buffer: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()

    for p in products:
        prompt = _build_prompt(p)
        description, in_tok, out_tok = _call_gpt(openai_client, prompt)
        cost = in_tok * ENRICHMENT_COST_IN_PER_TOKEN + out_tok * ENRICHMENT_COST_OUT_PER_TOKEN

        buffer.append({
            "product_id": p.product_id,
            "cluster_id": p.cluster_id,
            "cluster_label": p.cluster_label,
            "description_enriched": description,
            "description_model": GPT_MODEL,
            "description_tone": GPT_CLUSTER_LABEL_TONE,
            "description_tokens_input": in_tok,
            "description_tokens_output": out_tok,
            "description_cost_usd": cost,
            "description_created_at": now,
        })
        total_cost += cost
        enriched += 1

        if len(buffer) >= BATCH_SIZE:
            _insert_rows(bq, buffer)
            buffer.clear()
            log.info("Enriched %d/%d products", enriched, len(products))
            time.sleep(0.5)

    if buffer:
        _insert_rows(bq, buffer)

    stats = {"enriched": enriched, "total_cost_usd": round(total_cost, 4)}
    log.info("Enrichment complete: %s", stats)
    return stats
