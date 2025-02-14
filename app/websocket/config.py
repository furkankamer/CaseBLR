

from dataclasses import dataclass

@dataclass
class Config:
    """Configuration settings for WebSocket ingestion."""
    WS_URL: str = "wss://stream.binance.com:9443/ws/btcusdt@depth"
    RECONNECT_DELAY: int = 5         # Seconds to wait before reconnecting
    PING_INTERVAL: int = 20          # Ping interval for the WebSocket
    PING_TIMEOUT: int = 10           # Ping timeout
    SHORT_WINDOW: int = 50           # SMA short window length
    LONG_WINDOW: int = 200           # SMA long window length
    WAP_LEVELS: int = 5              # Number of orderbook levels for WAP calculation
    PRICE_HISTORY_MAX_LEN: int = 201 # Maximum length of price history (deque)
