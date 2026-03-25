"""On-demand product enrichment via GPT-4o-mini."""
from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import bigquery
from openai import OpenAI

from config import OPENAI_API_KEY, GPT_MODEL, TABLE_CLEAN, TABLE_CLUSTERED, TABLE_ENRICHED
from models.schemas import EnrichResponse


def enrich_product(bq: bigquery.Client, product_id: int) -> EnrichResponse:
    # Fetch product + cluster info
    sql = f"""
    SELECT
      c.product_id, c.name, c.brand, c.category, c.department,
      cl.cluster_label
    FROM `{TABLE_CLEAN}` c
    LEFT JOIN `{TABLE_CLUSTERED}` cl USING (product_id)
    WHERE c.product_id = {product_id}
    LIMIT 1
    """
    rows = list(bq.query(sql).result())
    if not rows:
        raise ValueError(f"Product {product_id} not found")

    r = rows[0]
    cluster_info = f"Cluster: {r.cluster_label}." if r.cluster_label else ""
    prompt = (
        "You are a luxury retail copywriter. Write exactly 50 words describing this product "
        "in an aspirational, luxury_retail tone. No bullet points. No markdown. Just flowing prose.\n\n"
        f"Product: {r.name}\nBrand: {r.brand}\nCategory: {r.category} / {r.department}\n{cluster_info}"
    )

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.7,
    )
    description = response.choices[0].message.content.strip()
    in_tok = response.usage.prompt_tokens
    out_tok = response.usage.completion_tokens
    cost = in_tok * 0.00000015 + out_tok * 0.00000060

    now = datetime.now(timezone.utc).isoformat()
    row = {
        "product_id": product_id,
        "cluster_id": None,
        "cluster_label": r.cluster_label,
        "description_enriched": description,
        "description_model": GPT_MODEL,
        "description_tone": "luxury_retail",
        "description_tokens_input": in_tok,
        "description_tokens_output": out_tok,
        "description_cost_usd": cost,
        "description_created_at": now,
    }
    bq.insert_rows_json(TABLE_ENRICHED, [row])

    return EnrichResponse(
        product_id=product_id,
        description_enriched=description,
        description_model=GPT_MODEL,
        description_tokens_input=in_tok,
        description_tokens_output=out_tok,
    )
