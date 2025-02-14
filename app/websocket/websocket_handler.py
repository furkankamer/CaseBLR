

import json
import time
import logging
import websocket
import numpy as np
from time import perf_counter

from app.core.redis_client import redis_client
from app.core.metrics import prom_message_count, prom_latency, prom_error_count
from app.websocket.price_manager import PriceManager
from app.websocket.order_state import OrderState
from app.websocket.config import Config
from app.services.signal_processor import SignalProcessor
from app.services.database_manager import DatabaseManager
from app.services.indicator import calculate_wap

logger = logging.getLogger(__name__)

class WebSocketHandler:
    """Handles WebSocket connection and message processing."""
    def __init__(self, config: Config):
        self.config = config
        self.price_manager = PriceManager(config.PRICE_HISTORY_MAX_LEN)
        self.order_state = OrderState()
        self.signal_processor = SignalProcessor(config, self.price_manager, self.order_state)
    
    def on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        start_time = perf_counter()
        try:
            self._process_message(message)
        except Exception as e:
            logger.error("Failed to process websocket message: %s", e)
            redis_client.incr('error_count')
            prom_error_count.inc()
        finally:
            self._update_metrics(start_time)
    
    def _process_message(self, message: str) -> None:
        data = json.loads(message)
        bids = data.get("b", [])
        asks = data.get("a", [])
        
        if not (bids and asks):
            logger.warning("Orderbook data incomplete: no bid/ask available.")
            redis_client.incr('data_loss_count')
            return
        
        wap_price = self._calculate_prices(bids, asks)
        if wap_price is None:
            redis_client.incr('data_loss_count')
            return
        
        with DatabaseManager.get_session() as session:
            DatabaseManager.save_price_tick(session, wap_price)
            self.price_manager.add_price(wap_price)
            sma_short, sma_long = self.price_manager.calculate_smas(
                self.config.SHORT_WINDOW, self.config.LONG_WINDOW
            )
            self.signal_processor.process_signal(wap_price, sma_short, sma_long)
    
    def _calculate_prices(self, bids: list, asks: list) -> float:
        bids, asks = np.array(bids, dtype=float), np.array(asks, dtype=float)
        wap_price = calculate_wap(bids, asks, levels=self.config.WAP_LEVELS)
        return wap_price
    
    def _update_metrics(self, start_time: float) -> None:
        elapsed = perf_counter() - start_time
        redis_client.incr('message_count')
        redis_client.incrbyfloat('latency_sum', elapsed)
        prom_message_count.inc()
        prom_latency.observe(elapsed)
    
    def on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        logger.error("WebSocket error: %s", error)
        redis_client.incr('error_count')
        prom_error_count.inc()
    
    def on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        logger.info("WebSocket connection closed: code=%s, msg=%s", close_status_code, close_msg)
    
    def on_open(self, ws: websocket.WebSocketApp) -> None:
        logger.info("WebSocket connection established.")
