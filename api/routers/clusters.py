"""GET /clusters and GET /clusters/{cluster_id}/products."""
from fastapi import APIRouter, Depends, HTTPException
from google.cloud import bigquery

from models.schemas import ClustersResponse, ClusterProductsResponse
from services.bq_client import get_bq_client
from services import cluster_service

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=ClustersResponse)
def list_clusters(bq: bigquery.Client = Depends(get_bq_client)) -> ClustersResponse:
    return cluster_service.get_clusters(bq)


@router.get("/{cluster_id}/products", response_model=ClusterProductsResponse)
def get_cluster_products(
    cluster_id: int,
    bq: bigquery.Client = Depends(get_bq_client),
) -> ClusterProductsResponse:
    result = cluster_service.get_cluster_products(bq, cluster_id)
    if not result.products:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found or empty")
    return result
