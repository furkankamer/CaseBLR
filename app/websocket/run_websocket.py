

import time
import websocket
from app.websocket.config import Config
from app.websocket.websocket_handler import WebSocketHandler

def run_websocket():
    """Main entry point for running the WebSocket client."""
    config = Config()
    handler = WebSocketHandler(config)
    
    while True:
        try:
            ws_app = websocket.WebSocketApp(
                config.WS_URL,
                on_message=handler.on_message,
                on_error=handler.on_error,
                on_close=handler.on_close
            )
            ws_app.on_open = handler.on_open
            ws_app.run_forever(
                ping_interval=config.PING_INTERVAL,
                ping_timeout=config.PING_TIMEOUT
            )
        except Exception as e:
            print(f"WebSocket connection error: {e}")
        time.sleep(config.RECONNECT_DELAY)
        print("Attempting to reconnect to WebSocket...")
