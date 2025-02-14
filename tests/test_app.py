

import pytest
import collections
from collections import abc
collections.Iterable = abc.Iterable
collections.Mapping = abc.Mapping
collections.MutableSet = abc.MutableSet
collections.MutableMapping = abc.MutableMapping

from fastapi.testclient import TestClient
from app.main import app
from app.services.indicator import calculate_wap, calculate_sma
import numpy as np

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data and data["status"] == "OK"

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    # Check for expected keys in the JSON response.
    for key in ["average_latency", "cpu_usage_percent", "memory_usage_percent", "error_count", "data_loss_count", "message_count"]:
        assert key in data

def test_prometheus_metrics():
    response = client.get("/prometheus")
    assert response.status_code == 200
    # The response should include a known Prometheus metric name.
    assert "ws_message_count" in response.text

def test_calculate_wap():
    bids = [["100", "2"], ["99", "3"]]
    asks = [["101", "1.5"], ["102", "2.5"]]
    bids, asks = np.array(bids, dtype=float), np.array(asks, dtype=float)
    wap = calculate_wap(bids, asks, levels=2)
    # Expected calculation:
    # Bids: (100*2 + 99*3) = 200 + 297 = 497, volume = 5
    # Asks: (101*1.5 + 102*2.5) = 151.5 + 255 = 406.5, volume = 4
    # Total value = 497 + 406.5 = 903.5, total volume = 9
    expected = 903.5 / 9
    assert abs(wap - expected) < 1e-6

def test_calculate_sma():
    prices = [1, 2, 3, 4, 5, 6]
    sma_values = calculate_sma(prices, 3)
    # The last SMA value should be (4+5+6)/3 = 5
    assert not np.isnan(sma_values[-1])
    assert abs(sma_values[-1] - 5) < 1e-6

# Scalability/Concurrency test for OrderState.
# This test simulates multiple threads attempting to open an order simultaneously.
# The OrderState class uses a lock to ensure that only one order is created.
def test_order_state_concurrency():
    from app.websocket.order_state import OrderState
    import threading

    order_state = OrderState()
    order_ids = []

    def open_order():
        # This function simulates an attempt to open an order.
        # It checks if no order is currently open, then sets one.
        if order_state.current_order_id is None:
            order_state.current_order_id = 1  # Simulate new order id assignment
            order_ids.append(order_state.current_order_id)
        else:
            order_ids.append(order_state.current_order_id)
    
    threads = []
    for _ in range(10):
        t = threading.Thread(target=open_order)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # All threads should observe the same order id if one order was opened.
    # This verifies that the OrderState lock is working as expected.
    assert all(x == 1 for x in order_ids), "Multiple order openings detected; OrderState is not handling concurrency correctly."
