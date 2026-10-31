from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.keys import idempotency_key
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_9", customer_id="cus_9", amount_cents=1100, currency="EUR")


def _setup():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    return bus, revenue, seen


def test_retry_after_lost_response_captures_once_in_other_currency():
    bus, revenue, seen = _setup()
    gateway = FakeGateway(faults={1: "timeout_after"})
    capture = charge(ORDER, gateway, bus)
    assert gateway.calls == 2
    assert gateway.captured("ord_9") == [capture]
    assert capture.key == idempotency_key(ORDER)
    assert capture.amount_cents == 1100
    assert seen == [capture]
    assert (revenue.total_cents, revenue.charges) == (1100, 1)


def test_mixed_timeouts_still_capture_once():
    bus, revenue, seen = _setup()
    gateway = FakeGateway(faults={1: "timeout_after", 2: "timeout_before"})
    capture = charge(ORDER, gateway, bus)
    assert gateway.calls == 3
    assert len(gateway.captures) == 1
    assert gateway.captured("ord_9") == [capture]
    assert capture.key == idempotency_key(ORDER)
    assert seen == [capture]
    assert (revenue.total_cents, revenue.charges) == (1100, 1)
