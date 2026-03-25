"""Pydantic schemas for API request / response bodies."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── /search ──────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=100)


class ProductResult(BaseModel):
    product_id: int
    name: str
    brand: str
    category: str
    department: str
    retail_price: float
    cluster_label: Optional[str]
    description_enriched: Optional[str]
    distance: float


class SearchResponse(BaseModel):
    query: str
    results: list[ProductResult]


# ── /clusters ────────────────────────────────────────────────────────────

class ClusterSummary(BaseModel):
    cluster_id: int
    cluster_label: str
    product_count: int
    avg_price: float


class ClustersResponse(BaseModel):
    clusters: list[ClusterSummary]


# ── /clusters/{id}/products ──────────────────────────────────────────────

class ClusterProduct(BaseModel):
    product_id: int
    name: str
    brand: str
    retail_price: float
    description_enriched: Optional[str]


class ClusterProductsResponse(BaseModel):
    cluster_id: int
    cluster_label: str
    products: list[ClusterProduct]


# ── /enrich ──────────────────────────────────────────────────────────────

class EnrichRequest(BaseModel):
    product_id: int


class EnrichResponse(BaseModel):
    product_id: int
    description_enriched: str
    description_model: str
    description_tokens_input: int
    description_tokens_output: int


# ── /quality ─────────────────────────────────────────────────────────────

class QualityReport(BaseModel):
    report_timestamp: str
    total_records: int
    valid_records: int
    completeness_pct: float
    field_name_completeness: Optional[int]
    field_brand_completeness: Optional[int]
    field_cat_completeness: Optional[int]
    field_price_completeness: Optional[int]
    price_mean: Optional[float]
    price_min: Optional[float]
    price_max: Optional[float]
