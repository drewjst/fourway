from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_free_usd_order_is_captured_but_not_published():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gw = FakeGateway()
    charge(Order(id="ord_free", customer_id="cus_1", amount_cents=0), gw, bus)
    assert seen == []
    assert len(gw.captured("ord_free")) == 1


def test_free_jpy_order_does_not_count_as_revenue():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    order = Order(id="ord_free_jpy", customer_id="cus_1", amount_cents=0, currency="JPY")
    charge(order, FakeGateway(), bus)
    assert (revenue.total_cents, revenue.charges) == (0, 0)
