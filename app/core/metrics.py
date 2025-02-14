
from prometheus_client import CollectorRegistry, Counter, Histogram

registry = CollectorRegistry()

prom_message_count = Counter(
    "ws_message_count", 
    "Number of websocket messages processed", 
    registry=registry
)
prom_latency = Histogram(
    "ws_message_latency_seconds", 
    "Latency for processing each message", 
    registry=registry
)
prom_error_count = Counter(
    "ws_error_count", 
    "Number of errors encountered", 
    registry=registry
)
