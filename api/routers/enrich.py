"""POST /enrich — on-demand product enrichment."""
from fastapi import APIRouter, Depends, HTTPException
from google.cloud import bigquery

from models.schemas import EnrichRequest, EnrichResponse
from services.bq_client import get_bq_client
from services import enrich_service

router = APIRouter(prefix="/enrich", tags=["enrich"])


@router.post("", response_model=EnrichResponse)
def enrich_product(
    body: EnrichRequest,
    bq: bigquery.Client = Depends(get_bq_client),
) -> EnrichResponse:
    try:
        return enrich_service.enrich_product(bq, body.product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
