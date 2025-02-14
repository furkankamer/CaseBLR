
import threading
import logging
import uvicorn

from fastapi import FastAPI
from app.api.endpoints import health, metrics, prometheus
from app.websocket.run_websocket import run_websocket
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(prometheus.router)

# Create database tables on startup (if they don’t exist)
from app.core.db import engine, Base
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def startup_event():
    ws_thread = threading.Thread(target=run_websocket, daemon=True)
    ws_thread.start()
    logger.info("WebSocket ingestion thread started.")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
