from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway

USD = Order(id="ord_1", customer_id="cus_1", amount_cents=1250, currency="USD")
EUR = Order(id="ord_1", customer_id="cus_1", amount_cents=1150, currency="EUR")


def test_requote_in_new_currency_gets_its_own_capture():
    gateway = FakeGateway()
    first = charge(USD, gateway)
    second = charge(EUR, gateway)
    assert first != second
    assert first.key != second.key
    assert second.amount_cents == 1150
    assert gateway.captured("ord_1") == [first, second]


def test_requote_revenue_counts_both_currencies():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    gateway = FakeGateway()
    charge(USD, gateway, bus)
    charge(EUR, gateway, bus)
    assert (revenue.total_cents, revenue.charges) == (2400, 2)
