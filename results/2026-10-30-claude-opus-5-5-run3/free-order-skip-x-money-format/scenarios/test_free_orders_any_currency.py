from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_free_yen_order_publishes_no_event():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway()
    order = Order(id="ord_free_jp", customer_id="cus_1", amount_cents=0, currency="JPY")
    capture = charge(order, gateway, bus)
    assert capture.amount_cents == 0
    assert len(gateway.captured("ord_free_jp")) == 1
    assert seen == []


def test_free_usd_order_not_counted_as_revenue():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(Order(id="ord_free", customer_id="cus_1", amount_cents=0), FakeGateway(), bus)
    charge(Order(id="ord_paid", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert (revenue.total_cents, revenue.charges) == (1250, 1)
