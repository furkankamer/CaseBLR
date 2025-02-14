# FastAPI Websocket Ingestion App

This project is a FastAPI application that ingests orderbook data from Binance via a websocket, calculates technical indicators (SMA and WAP), logs trading signals in JSON format, and stores price ticks, orders, and signals in a PostgreSQL database. It also exposes several endpoints for monitoring system health, performance metrics, and Prometheus metrics.

## Table of Contents

- Features
- Folder Structure
- Requirements
- Setup and Running
  - Docker Compose
  - Running Tests
- API Endpoints
  - Health Check
  - Metrics
  - Prometheus Metrics
- Metrics Details
- Technical Details
- License

## Features

- **Websocket Ingestion:**  
  Connects to Binance’s orderbook websocket (`wss://stream.binance.com:9443/ws/btcusdt@depth`), computes weighted average price (WAP), and stores price ticks in a PostgreSQL database.

- **Technical Indicators:**  
  Uses a Numba-accelerated function to compute the last two Simple Moving Averages (SMA) and detects SMA crossovers for trading signals.

- **Trading Signals Logging & Storage:**  
  Logs every trading signal (open or close) in JSON format and saves them in a separate database table (`trading_signals`).

- **Performance Metrics:**  
  Uses Redis to count messages, latency, errors, and data loss. Prometheus-compatible metrics are exposed for scraping.

- **API Endpoints:**  
  Exposes endpoints for health checks, JSON metrics, and Prometheus metrics.


## Requirements

- Docker & Docker Compose
- Python 3.9+
- PostgreSQL (via Docker)
- Redis (via Docker)

## Setup and Running

### Docker Compose

Build and start all services (PostgreSQL, Redis, and the FastAPI web app) by running:

```bash
docker-compose up --build
```
The web app will be available on localhost port 8000.

### Running Tests

To run the test suite (using `pytest`) inside the web container, run:

```bash
docker-compose run --rm web pytest
```

## API Endpoints

### Health Check

- **URL:** `/health`
- **Method:** GET
- **Response Example:**
  ```json
  {
    "status": "OK",
    "timestamp": "2025-02-10T14:32:00.123456"
  }
  ```

### Metrics

- **URL:** `/metrics`
- **Method:** GET
- **Response Example:**
  ```json
  {
    "average_latency": 0.0123,
    "cpu_usage_percent": 15.2,
    "memory_usage_percent": 42.7,
    "error_count": 0,
    "data_loss_count": 1,
    "message_count": 500
  }
  ```

### Prometheus Metrics

- **URL:** `/prometheus`
- **Method:** GET
- **Description:**  
  Exposes Prometheus-compatible metrics for scraping.

## Metrics Details

- **average_latency:** Average processing latency per operation (in seconds).
- **cpu_usage_percent:** CPU usage percentage.
- **memory_usage_percent:** Memory usage percentage.
- **error_count:** Total number of errors encountered.
- **data_loss_count:** Number of messages with missing bid/ask data.
- **message_count:** Total number of websocket messages processed.

## Technical Details

- **Websocket Ingestion:**  
  A background thread (started on application startup) connects to Binance’s websocket. It calculates the weighted average price (WAP) from orderbook data and computes SMA crossovers to generate trading signals.

- **Trading Signals:**  
  When a crossover is detected:
  - A JSON-formatted log entry is created and written to the application logs.
  - A new record is inserted into the `trading_signals` database table.

- **Database:**  
  PostgreSQL is used for persisting price ticks, orders, and trading signals. SQLAlchemy is used for ORM functionality.

- **Caching and Metrics Storage:**  
  Redis is used to store counters and latency measurements. Prometheus metrics are exposed using a custom registry.

## License

This project is licensed under the MIT License.

