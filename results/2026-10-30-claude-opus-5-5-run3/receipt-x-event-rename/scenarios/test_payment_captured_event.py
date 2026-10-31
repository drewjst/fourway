from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_charge_publishes_payment_captured_not_the_old_name():
    bus = EventBus()
    new, old = [], []
    bus.subscribe("payment.captured", new.append)
    bus.subscribe("charge.succeeded", old.append)
    capture = charge(Order(id="ord_3", customer_id="cus_1", amount_cents=900), FakeGateway(), bus)
    assert new == [capture]
    assert old == []


def test_analytics_listens_to_payment_captured():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(Order(id="ord_4", customer_id="cus_1", amount_cents=300), FakeGateway(), bus)
    bus.publish("charge.succeeded", object())
    assert (revenue.total_cents, revenue.charges) == (300, 1)
