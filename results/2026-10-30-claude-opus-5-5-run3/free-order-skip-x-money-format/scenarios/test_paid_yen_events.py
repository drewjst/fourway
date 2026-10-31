from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_paid_yen_order_publishes_success_event():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway()
    order = Order(id="ord_jp", customer_id="cus_jp", amount_cents=80, currency="JPY")
    capture = charge(order, gateway, bus)
    assert capture.amount_cents == 80
    assert len(gateway.captured("ord_jp")) == 1
    assert seen == [capture]


def test_revenue_counts_paid_yen_charge():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(Order(id="ord_jp1", customer_id="cus_jp", amount_cents=80, currency="JPY"), FakeGateway(), bus)
    charge(Order(id="ord_jp2", customer_id="cus_jp", amount_cents=1250, currency="JPY"), FakeGateway(), bus)
    assert (revenue.total_cents, revenue.charges) == (1330, 2)
