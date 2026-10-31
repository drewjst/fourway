from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_small_yen_charge_publishes_success_event():
    order = Order(id="ord_jpy", customer_id="cus_1", amount_cents=50, currency="JPY")
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    capture = charge(order, FakeGateway(), bus)
    assert capture.amount_cents == 50
    assert seen == [capture]


def test_small_yen_charge_counts_as_revenue():
    order = Order(id="ord_jpy_rev", customer_id="cus_1", amount_cents=50, currency="JPY")
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(order, FakeGateway(), bus)
    assert (revenue.total_cents, revenue.charges) == (50, 1)
