from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.keys import idempotency_key
from payments.orders import Order
from payments.testing import FakeGateway

EUR_ORDER = Order(id="ord_9", customer_id="cus_1", amount_cents=900, currency="EUR")


def test_retry_after_lost_response_reuses_the_capture_for_a_currency_order():
    gateway = FakeGateway(faults={1: "timeout_after"})
    capture = charge(EUR_ORDER, gateway)
    assert gateway.calls == 2
    assert gateway.captured("ord_9") == [capture]
    assert capture.key == idempotency_key(EUR_ORDER)
    assert capture.amount_cents == 900


def test_retry_after_lost_response_counts_revenue_once():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway(faults={1: "timeout_after"})
    capture = charge(EUR_ORDER, gateway, bus)
    assert len(gateway.captures) == 1
    assert seen == [capture]
    assert (revenue.total_cents, revenue.charges) == (900, 1)
