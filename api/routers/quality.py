"""GET /quality — latest data quality report."""
from fastapi import APIRouter, Depends, HTTPException
from google.cloud import bigquery

from models.schemas import QualityReport
from services.bq_client import get_bq_client
from services import quality_service

router = APIRouter(prefix="/quality", tags=["quality"])


@router.get("", response_model=QualityReport)
def get_quality(bq: bigquery.Client = Depends(get_bq_client)) -> QualityReport:
    try:
        return quality_service.get_quality_report(bq)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
