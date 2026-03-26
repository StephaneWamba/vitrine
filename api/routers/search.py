"""POST /search — semantic product search."""
from fastapi import APIRouter, Depends
from google.cloud import bigquery

from models.schemas import SearchRequest, SearchResponse
from services.bq_client import get_bq_client
from services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_products(
    body: SearchRequest,
    bq: bigquery.Client = Depends(get_bq_client),
) -> SearchResponse:
    return search_service.search(bq, body.query, body.top_k, body.max_price, body.min_price)
