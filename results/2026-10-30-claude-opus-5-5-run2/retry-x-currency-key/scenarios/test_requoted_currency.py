from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_requoted_order_gets_a_capture_per_currency():
    gateway = FakeGateway()
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    usd = Order(id="ord_9", customer_id="cus_1", amount_cents=1000, currency="USD")
    eur = Order(id="ord_9", customer_id="cus_1", amount_cents=920, currency="EUR")
    first = charge(usd, gateway, bus)
    second = charge(eur, gateway, bus)
    caps = gateway.captured("ord_9")
    assert len(caps) == 2
    assert first.key != second.key
    assert first.amount_cents == 1000
    assert second.amount_cents == 920
    assert (revenue.total_cents, revenue.charges) == (1920, 2)
