
from fastapi import APIRouter
import psutil
import redis

from app.core.redis_client import redis_client

router = APIRouter()

@router.get("/metrics", tags=["Metrics"])
def get_metrics():
    """
    Return a JSON with application performance metrics:
      - Average latency per operation
      - CPU and memory usage
      - Error and data loss counts
    """
    try:
        msg_count = float(redis_client.get('message_count') or 0)
        latency_sum = float(redis_client.get('latency_sum') or 0)
        avg_latency = latency_sum / msg_count if msg_count > 0 else 0.0
        error_count = int(redis_client.get('error_count') or 0)
        data_loss_count = int(redis_client.get('data_loss_count') or 0)
    except Exception:
        avg_latency = -1
        error_count = -1
        data_loss_count = -1

    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    memory_usage = mem.percent

    return {
        "average_latency": avg_latency,
        "cpu_usage_percent": cpu_usage,
        "memory_usage_percent": memory_usage,
        "error_count": error_count,
        "data_loss_count": data_loss_count,
        "message_count": msg_count
    }
