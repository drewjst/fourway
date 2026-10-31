from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway


def _attempt(order, faults):
    gateway = FakeGateway(faults=faults)
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    try:
        result = charge(order, gateway, bus)
    except GatewayTimeout:
        result = None
    return gateway, seen, revenue, result


def test_lost_response_never_double_captures():
    order = Order(id="ord_5", customer_id="cus_2", amount_cents=900, currency="GBP")
    gateway, seen, revenue, result = _attempt(order, {1: "timeout_after"})
    assert len(gateway.captured("ord_5")) == 1
    assert len(seen) <= 1
    if result is not None:
        assert seen == [result]
        assert gateway.captured("ord_5") == [result]
    assert revenue.total_cents == sum(c.amount_cents for c in seen)


def test_repeated_lost_responses_capture_once():
    order = Order(id="ord_6", customer_id="cus_2", amount_cents=500)
    gateway, seen, revenue, result = _attempt(order, {1: "timeout_after", 2: "timeout_after"})
    assert len(gateway.captured("ord_6")) == 1
    assert len(seen) <= 1
    assert revenue.charges == len(seen)
