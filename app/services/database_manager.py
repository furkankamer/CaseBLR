

import json
import backoff
from contextlib import contextmanager
from app.core.db import SessionLocal
from app.models.models import Price, TradingSignal

class DatabaseManager:
    """Handles database operations with retry/backoff logic."""
    
    @staticmethod
    @contextmanager
    def get_session():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def save_price_tick(session, wap_price: float):
        session.add(Price(wap=wap_price))

    @staticmethod
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def save_trading_signal(session, signal_type: str, price: float, details: dict):
        session.add(TradingSignal(signal_type=signal_type, price=price, details=json.dumps(details)))
