from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_free_order_is_captured_but_not_counted_as_revenue():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway()
    capture = charge(Order(id="ord_free", customer_id="cus_1", amount_cents=0), gateway, bus)
    assert capture.amount_cents == 0
    assert len(gateway.captured("ord_free")) == 1
    assert seen == []
    assert (revenue.total_cents, revenue.charges) == (0, 0)


def test_paid_order_after_free_order_still_counted():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    gateway = FakeGateway()
    charge(Order(id="ord_free", customer_id="cus_1", amount_cents=0), gateway, bus)
    charge(Order(id="ord_paid", customer_id="cus_1", amount_cents=1250), gateway, bus)
    assert (revenue.total_cents, revenue.charges) == (1250, 1)
