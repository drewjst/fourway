from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def _bus():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    return bus, seen


def test_free_orders_in_any_currency_publish_nothing():
    for currency in ("USD", "EUR", "JPY"):
        bus, seen = _bus()
        gateway = FakeGateway()
        order = Order(id=f"ord_free_{currency}", customer_id="cus_1", amount_cents=0, currency=currency)
        capture = charge(order, gateway, bus)
        assert capture.amount_cents == 0
        assert len(gateway.captured(order.id)) == 1
        assert seen == [], currency


def test_free_orders_do_not_count_as_revenue_next_to_paid_ones():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    gateway = FakeGateway()
    charge(Order(id="ord_free", customer_id="cus_1", amount_cents=0, currency="JPY"), gateway, bus)
    charge(Order(id="ord_paid", customer_id="cus_1", amount_cents=1250, currency="JPY"), gateway, bus)
    assert (revenue.total_cents, revenue.charges) == (1250, 1)
