

import json
import logging
from datetime import datetime
from app.services.database_manager import DatabaseManager
from app.models.models import Order
import numpy as np
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

class SignalProcessor:
    """Detects and processes trading signals based on SMA crossover."""
    def __init__(self, config, price_manager, order_state):
        self.config = config
        self.price_manager = price_manager
        self.order_state = order_state
    
    def process_signal(self, wap_price: float, sma_short, sma_long) -> None:
        if not self._valid_sma_values(sma_short, sma_long):
            return

        if wap_price is None or wap_price <= 0 or not np.isfinite(wap_price) \
            or np.isnan(wap_price):
            logger.error("Invalid price value: %s", wap_price)
            redis_client.incr('data_loss_count')
            return
        
        with DatabaseManager.get_session() as session:
            if self._is_open_signal(sma_short, sma_long):
                self._handle_open_signal(session, wap_price, sma_short, sma_long)
            elif self._is_close_signal(sma_short, sma_long):
                self._handle_close_signal(session, wap_price, sma_short, sma_long)

    def _valid_sma_values(self, sma_short, sma_long) -> bool:
        # Expect each SMA array to have at least two values
        return (len(sma_short) >= 2 and len(sma_long) >= 2 and 
                np.isfinite(sma_short).all() and 
                np.isfinite(sma_long).all() and 
                not np.isnan(sma_short).any() and
                not np.isnan(sma_long).any() and 
                (sma_long > 0).all() and (sma_short > 0).all())

    def _is_open_signal(self, sma_short, sma_long) -> bool:
        return sma_short[-1] > sma_long[-1] and sma_short[-2] <= sma_long[-2]

    def _is_close_signal(self, sma_short, sma_long) -> bool:
        return sma_short[-1] < sma_long[-1] and sma_short[-2] >= sma_long[-2]

    def _handle_open_signal(self, session, wap_price: float, sma_short: np.ndarray, sma_long: np.ndarray) -> None:
        # Check in the shared database if an open order already exists.
        # This query is executed within the same transaction so that concurrent attempts
        # are serialized by the database.
        existing_order = session.query(Order).filter(Order.status == "open").first()
        if existing_order is not None:
            # An open order exists, so we do not open another one.
            return
        # No open order exists, so proceed to create one.
        signal_data = self._create_signal_data("open", wap_price, sma_short, sma_long)
        DatabaseManager.save_trading_signal(session, "open", wap_price, signal_data)
        new_order = Order(status="open", side="long", price=wap_price, details="Opened on SMA crossover")
        session.add(new_order)
        session.flush()  # flush to assign new_order.id from the DB
        self.order_state.current_order_id = new_order.id
        logger.info("Signal JSON: %s", json.dumps(signal_data))

    def _handle_close_signal(self, session, wap_price: float, sma_short: np.ndarray, sma_long: np.ndarray) -> None:
        # Fetch the currently open order within the same transaction to ensure atomicity
        open_order = session.query(Order).filter(Order.status == "open").with_for_update(skip_locked=True).first()
    
        if open_order is None:
            # No open order to close, avoid duplicate close actions across instances
            print('No open order to close, avoid duplicate close actions across instances')
            return
    
        # Proceed with closing the order
        signal_data = self._create_signal_data("close", wap_price, sma_short, sma_long)
        DatabaseManager.save_trading_signal(session, "close", wap_price, signal_data)
        
        open_order.status = "closed"
        open_order.close_price = wap_price
        open_order.closed_at = datetime.utcnow()
        
        session.flush()  # Ensure changes are written before releasing the lock
        self.order_state.current_order_id = None
        logger.info("Closed order ID %s at price %s", open_order.id, wap_price)

    def _create_signal_data(self, signal_type: str, price: float, sma_short, sma_long) -> dict:
        return {
            "signal": signal_type,
            "price": price,
            "sma_short": float(sma_short[-1]),
            "sma_long": float(sma_long[-1]),
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"{signal_type.capitalize()}d on SMA crossover"
        }
