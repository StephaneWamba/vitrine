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


def search(bq: bigquery.Client, query: str, top_k: int) -> SearchResponse:
    vector = _embed_query(query)
    vector_json = json.dumps(vector)

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
        top_k => {top_k},
        distance_type => 'COSINE'
      ) vs
    JOIN `{TABLE_CLEAN}`     c  ON vs.base.product_id = c.product_id
    LEFT JOIN `{TABLE_CLUSTERED}` cl ON c.product_id = cl.product_id
    LEFT JOIN `{TABLE_ENRICHED}`  en ON c.product_id = en.product_id
    ORDER BY distance ASC
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
