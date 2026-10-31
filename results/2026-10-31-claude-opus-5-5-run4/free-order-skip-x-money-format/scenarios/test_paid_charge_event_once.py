from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_paid_usd_charge_event_reaches_consumers_once():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway()
    capture = charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), gateway, bus)
    assert seen == [capture]
    assert len(gateway.captured("ord_1")) == 1
    assert (revenue.total_cents, revenue.charges) == (1250, 1)


def test_paid_jpy_charge_event_reaches_consumers_once():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway()
    order = Order(id="ord_jp", customer_id="cus_jp", amount_cents=1250, currency="JPY")
    capture = charge(order, gateway, bus)
    assert seen == [capture]
    assert capture.amount_cents == 1250
    assert len(gateway.captured("ord_jp")) == 1
