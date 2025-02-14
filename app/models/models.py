
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.core.db import Base

class Price(Base):
    __tablename__ = 'prices'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    wap = Column(Float)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(String)  # e.g., "open", "closed"
    side = Column(String)    # e.g., "long" or "short"
    price = Column(Float)    # Execution price (or signal price)
    details = Column(String) # Any additional details

class TradingSignal(Base):
    __tablename__ = 'trading_signals'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    signal_type = Column(String)  # e.g., "open", "close"
    price = Column(Float)
    details = Column(String)      # A JSON string with additional signal info
