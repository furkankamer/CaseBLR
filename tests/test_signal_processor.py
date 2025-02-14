import json
import pytest
from datetime import datetime
from app.websocket.config import Config
from app.websocket.order_state import OrderState
from app.websocket.price_manager import PriceManager
from app.services.signal_processor import SignalProcessor
from app.services.database_manager import DatabaseManager
from app.models.models import Order, TradingSignal
import numpy as np

class DummySession:
    _shared_data = {
        'orders': [],
        'signals': []
    }

    def add(self, item):
        """Add an item to the appropriate collection."""
        if isinstance(item, TradingSignal):
            self._shared_data['signals'].append(item)
        elif isinstance(item, Order):
            # Simulate auto-increment ID
            if not hasattr(item, 'id') or item.id is None:
                item.id = len(self._shared_data['orders']) + 1
            self._shared_data['orders'].append(item)

    def query(self, model):
        """Return a query object for the appropriate model."""
        data = self._shared_data['orders'] if model == Order else self._shared_data['signals']
        return DummyQuery(data)

    def flush(self):
        """Simulate the flush operation."""
        pass

    def commit(self):
        """Simulate commit operation."""
        pass

    def rollback(self):
        """Simulate rollback operation."""
        pass

    def close(self):
        """Simulate close operation."""
        pass

class DummyQuery:
    def __init__(self, items):
        self.items = items

    def filter(self, condition):
        """Simple filter implementation focusing on Order.status."""
        filtered = []
        status_check = str(condition)
        for item in self.items:
            if "status" in status_check:
                if getattr(item, 'status', None) == "open":
                    filtered.append(item)
        print(str(status_check) + "-" * 20)
        return DummyQuery(filtered)

    def with_for_update(self, skip_locked=False):
        """Simulate row-level locking."""
        return self

    def first(self):
        """Return the first item or None."""
        return self.items[0] if self.items else None

class DummySessionManager:
    def __init__(self):
        self.session = DummySession()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()

@pytest.fixture(autouse=True)
def clear_shared_data():
    """Clear shared data before each test."""
    DummySession._shared_data = {'orders': [], 'signals': []}

@pytest.fixture
def mock_db(monkeypatch):
    """Set up mock database."""
    def get_session():
        return DummySessionManager()
    monkeypatch.setattr(DatabaseManager, "get_session", get_session)
    return DummySession._shared_data

@pytest.fixture
def config():
    return Config()

@pytest.fixture
def order_state():
    return OrderState()

@pytest.fixture
def price_manager(config):
    return PriceManager(config.PRICE_HISTORY_MAX_LEN)

@pytest.fixture
def signal_processor(config, price_manager, order_state):
    return SignalProcessor(config, price_manager, order_state)

def test_signal_processor_open(signal_processor, order_state, mock_db):
    """Test open signal processing."""
    # Setup crossing SMAs for open signal
    sma_short = np.array([100.0, 105.0])
    sma_long = np.array([100.0, 100.0])
    wap_price = 110.0

    # Process signal
    signal_processor.process_signal(wap_price, sma_short, sma_long)

    # Verify order creation
    assert len(mock_db['orders']) == 1, "Order was not created"
    created_order = mock_db['orders'][0]
    assert created_order.status == "open", "Order status is not open"
    assert created_order.price == wap_price, "Order price does not match WAP"
    assert created_order.id is not None, "Order ID was not assigned"

    # Verify order state
    assert order_state.current_order_id == created_order.id, "Order state not updated"

    # Verify signal
    assert len(mock_db['signals']) == 1, "Signal was not created"
    assert mock_db['signals'][0].signal_type == "open", "Wrong signal type"

def test_signal_processor_close(signal_processor, order_state, mock_db):
    """Test close signal processing."""
    test_signal_processor_open(signal_processor, order_state, mock_db)

    # Setup crossing SMAs for close signal
    sma_short = np.array([110.0, 90.0])
    sma_long = np.array([100.0, 100.0])
    wap_price = 95.0

    assert mock_db['orders'][0].status == "open", "Order was not opened"

    # Process signal
    signal_processor.process_signal(wap_price, sma_short, sma_long)

    # Verify order closure
    assert mock_db['orders'][0].status == "closed", "Order was not closed"
    assert mock_db['orders'][0].close_price == wap_price, "Wrong closing price"

    # Verify order state reset
    assert order_state.current_order_id is None, "Order state not reset"

    # Verify signal
    assert len(mock_db['signals']) == 2, "Signal was not created"
    assert mock_db['signals'][1].signal_type == "close", "Wrong signal type"

def test_signal_processor_invalid_sma(signal_processor, order_state):
    """Test invalid SMA handling."""
    signal_processor.process_signal(100.0, np.array([]), np.array([]))
    assert order_state.current_order_id is None, "Order state changed with invalid SMAs"

    signal_processor.process_signal(100.0, np.array([100.0]), np.array([100.0]))
    assert order_state.current_order_id is None, "Order state changed with invalid SMAs"

def test_signal_processor_duplicate_open(signal_processor, order_state, mock_db):
    """Test duplicate open signal handling."""
    # Create pre-existing open order
    existing_order = Order(
        status="open",
        side="long",
        price=100.0,
        details="Existing order"
    )
    with DatabaseManager.get_session() as session:
        session.add(existing_order)
    
    order_state.current_order_id = existing_order.id
    initial_count = len(mock_db['orders'])

    # Try to create another open position
    sma_short = np.array([100.0, 105.0])
    sma_long = np.array([100.0, 100.0])
    signal_processor.process_signal(110.0, sma_short, sma_long)

    assert len(mock_db['orders']) == initial_count, "Duplicate order was created"


def test_signal_processor_price_edge_cases(signal_processor, order_state, mock_db):
    """Test edge cases for price values in signal processing."""
    sma_short = np.array([100.0, 105.0])
    sma_long = np.array([100.0, 100.0])

    # Test zero price
    signal_processor.process_signal(0.0, sma_short, sma_long)
    assert len(mock_db['orders']) == 0, "Order created with zero price"

    # Test negative price
    signal_processor.process_signal(-100.0, sma_short, sma_long)
    assert len(mock_db['orders']) == 0, "Order created with negative price"

    # Test extremely large price
    signal_processor.process_signal(np.inf, sma_short, sma_long)
    assert len(mock_db['orders']) == 0, "Order created with extremely large price"

def test_signal_processor_sma_edge_cases(signal_processor, order_state, mock_db):
    """Test edge cases for SMA values."""
    # Test with NaN values
    sma_short = np.array([100.0, np.nan])
    sma_long = np.array([100.0, 100.0])
    signal_processor.process_signal(100.0, sma_short, sma_long)
    assert len(mock_db['orders']) == 0, "Order created with NaN SMA"

    # Test with infinite values
    sma_short = np.array([100.0, np.inf])
    signal_processor.process_signal(100.0, sma_short, sma_long)
    assert len(mock_db['orders']) == 0, "Order created with infinite SMA"

    # Test with identical SMA values (no crossing)
    sma_short = np.array([100.0, 100.0])
    sma_long = np.array([100.0, 100.0])
    signal_processor.process_signal(100.0, sma_short, sma_long)
    assert len(mock_db['orders']) == 0, "Order created without SMA crossing"

def test_signal_processor_rapid_signals(signal_processor, order_state, mock_db):
    """Test rapid succession of signals."""
    # Create multiple crossing patterns rapidly
    prices = [100.0, 110.0, 90.0, 120.0]
    
    for price in prices:
        # Alternate between open and close signals
        sma_short = np.array([100.0, 105.0 if price > 100 else 95.0])
        sma_long = np.array([100.0, 100.0])
        signal_processor.process_signal(price, sma_short, sma_long)

    # Verify we don't have multiple open orders
    open_orders = [order for order in mock_db['orders'] if order.status == 'open']
    assert len(open_orders) <= 1, "Multiple open orders created"

def test_signal_processor_close_without_open(signal_processor, order_state, mock_db):
    """Test close signal without an open position."""
    # Generate close signal without open position
    sma_short = np.array([110.0, 90.0])
    sma_long = np.array([100.0, 100.0])
    signal_processor.process_signal(95.0, sma_short, sma_long)

    # Verify no orders were created
    assert len(mock_db['orders']) == 0, "Order created for close signal without open position"
    assert len(mock_db['signals']) == 0, "Signal created for close without open position"

def test_signal_processor_repeated_signals(signal_processor, order_state, mock_db):
    """Test repeated identical signals."""
    # Generate multiple identical open signals
    sma_short = np.array([100.0, 105.0])
    sma_long = np.array([100.0, 100.0])
    
    # Send same open signal multiple times
    for _ in range(3):
        signal_processor.process_signal(110.0, sma_short, sma_long)

    # Verify only one order was created
    assert len(mock_db['orders']) == 1, "Multiple orders created for identical signals"
    
    # Send same close signal multiple times
    sma_short = np.array([110.0, 90.0])
    for _ in range(3):
        signal_processor.process_signal(90.0, sma_short, sma_long)

    # Verify order was closed only once
    closed_orders = [order for order in mock_db['orders'] if order.status == 'closed']
    assert len(closed_orders) == 1, "Multiple closes for same order"

def test_signal_processor_order_state_consistency(signal_processor, order_state, mock_db):
    """Test order state consistency through multiple operations."""
    # Open position
    sma_short = np.array([100.0, 105.0])
    sma_long = np.array([100.0, 100.0])
    signal_processor.process_signal(110.0, sma_short, sma_long)
    
    initial_order_id = order_state.current_order_id
    assert initial_order_id is not None, "Order ID not set after open"

    # Try another open signal
    signal_processor.process_signal(120.0, sma_short, sma_long)
    assert order_state.current_order_id == initial_order_id, "Order ID changed without close"

    # Close position
    sma_short = np.array([110.0, 90.0])
    signal_processor.process_signal(90.0, sma_short, sma_long)
    assert order_state.current_order_id is None, "Order ID not cleared after close"

def test_signal_processor_signal_details(signal_processor, order_state, mock_db):
    """Test signal details are properly recorded."""
    sma_short = np.array([100.0, 105.0])
    sma_long = np.array([100.0, 100.0])
    price = 110.0

    signal_processor.process_signal(price, sma_short, sma_long)
    
    assert len(mock_db['signals']) == 1, "Signal not created"
    signal = mock_db['signals'][0]
    
    # Parse signal details
    details = json.loads(signal.details)
    
    # Verify signal details
    assert details['signal'] == 'open', "Wrong signal type in details"
    assert details['price'] == price, "Wrong price in details"
    assert details['sma_short'] == float(sma_short[-1]), "Wrong short SMA in details"
    assert details['sma_long'] == float(sma_long[-1]), "Wrong long SMA in details"
    assert 'timestamp' in details, "Missing timestamp in details"