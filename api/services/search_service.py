"""Semantic search via BigQuery VECTOR_SEARCH."""
from __future__ import annotations

import json
from google.cloud import bigquery
from openai import OpenAI

from config import OPENAI_API_KEY, EMBEDDING_MODEL, TABLE_EMBEDDED, TABLE_CLEAN, TABLE_ENRICHED, TABLE_CLUSTERED
from models.schemas import ProductResult, SearchResponse


def _embed_query(query: str) -> list[float]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=query)
    return response.data[0].embedding


def search(
    bq: bigquery.Client,
    query: str,
    top_k: int,
    max_price: float | None = None,
    min_price: float | None = None,
) -> SearchResponse:
    vector = _embed_query(query)
    vector_json = json.dumps(vector)

    # When a price filter is active, oversample so we still return top_k after filtering
    candidate_k = top_k * 5 if (max_price is not None or min_price is not None) else top_k

    price_clauses = []
    if max_price is not None:
        price_clauses.append(f"c.retail_price <= {max_price}")
    if min_price is not None:
        price_clauses.append(f"c.retail_price >= {min_price}")
    where_clause = f"WHERE {' AND '.join(price_clauses)}" if price_clauses else ""

    sql = f"""
    SELECT
      base.product_id,
      c.name,
      c.brand,
      c.category,
      c.department,
      c.retail_price,
      cl.cluster_label,
      en.description_enriched,
      distance
    FROM
      VECTOR_SEARCH(
        TABLE `{TABLE_EMBEDDED}`,
        'embedding',
        (SELECT {vector_json} AS embedding),
        top_k => {candidate_k},
        distance_type => 'COSINE'
      ) vs
    JOIN `{TABLE_CLEAN}`      c  ON vs.base.product_id = c.product_id
    LEFT JOIN `{TABLE_CLUSTERED}` cl ON c.product_id = cl.product_id
    LEFT JOIN `{TABLE_ENRICHED}`  en ON c.product_id = en.product_id
    {where_clause}
    ORDER BY distance ASC
    LIMIT {top_k}
    """

    rows = list(bq.query(sql).result())
    results = [
        ProductResult(
            product_id=r.product_id,
            name=r.name,
            brand=r.brand,
            category=r.category,
            department=r.department,
            retail_price=float(r.retail_price),
            cluster_label=r.cluster_label,
            description_enriched=r.description_enriched,
            distance=float(r.distance),
        )
        for r in rows
    ]
    return SearchResponse(query=query, results=results)
