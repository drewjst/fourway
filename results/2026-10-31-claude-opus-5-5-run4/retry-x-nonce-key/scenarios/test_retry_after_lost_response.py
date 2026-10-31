from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


def test_retry_after_lost_response_returns_the_single_capture():
    gateway = FakeGateway(faults={1: "timeout_after"})
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    capture = charge(ORDER, gateway, bus)
    assert gateway.calls == 2
    assert gateway.captured("ord_1") == [capture]
    assert seen == [capture]


def test_revenue_matches_money_actually_captured_after_retry():
    gateway = FakeGateway(faults={1: "timeout_after"})
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(ORDER, gateway, bus)
    captured_total = sum(c.amount_cents for c in gateway.captured("ord_1"))
    assert (revenue.total_cents, revenue.charges) == (1250, 1)
    assert captured_total == revenue.total_cents
