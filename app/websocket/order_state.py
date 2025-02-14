

from threading import Lock
from typing import Optional

class OrderState:
    """Thread-safe management of the current order ID."""
    def __init__(self):
        self._current_order_id: Optional[int] = None
        self._lock = Lock()
    
    @property
    def current_order_id(self) -> Optional[int]:
        with self._lock:
            return self._current_order_id
    
    @current_order_id.setter
    def current_order_id(self, value: Optional[int]):
        with self._lock:
            self._current_order_id = value
