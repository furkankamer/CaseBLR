
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.metrics import registry

router = APIRouter()

@router.get("/prometheus", tags=["Prometheus"])
def prometheus_metrics():
    """
    Expose Prometheus-formatted metrics.
    This endpoint can be scraped by Prometheus.
    """
    metrics_data = generate_latest(registry)
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
