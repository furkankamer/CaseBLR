
import redis
from app.config import REDIS_HOST, REDIS_PORT

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# Initialize counters if they are not already set
for key in ['message_count', 'latency_sum', 'error_count', 'data_loss_count']:
    if redis_client.get(key) is None:
        redis_client.set(key, 0)
