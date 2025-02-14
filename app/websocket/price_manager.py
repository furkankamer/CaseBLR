

from collections import deque
import numpy as np
from app.services.indicator import calculate_sma
import logging
from app.core.redis_client import redis_client


logger = logging.getLogger(__name__)
class PriceManager:
    """Maintains a history of price values and computes SMAs."""
    def __init__(self, max_len: int):
        self.price_history = deque(maxlen=max_len)
    
    def add_price(self, price: float) -> None:
        if price is None or price <= 0 or not np.isfinite(price) \
            or np.isnan(price):
            logger.error("Invalid price value: %s", price)
            redis_client.incr('data_loss_count')
            return
        self.price_history.append(price)
    
    def calculate_smas(self, short_window: int, long_window: int) -> (np.ndarray, np.ndarray):
        # Returns tuple: (sma_short, sma_long)
        return (
            calculate_sma(self.price_history, short_window),
            calculate_sma(self.price_history, long_window)
        )
