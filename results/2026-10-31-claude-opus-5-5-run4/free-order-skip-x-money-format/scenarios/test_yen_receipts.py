from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.money import format_amount
from payments.orders import Order
from payments.testing import FakeGateway


def _receipt_bus(currency):
    bus = EventBus()
    receipts = []
    bus.subscribe("charge.succeeded", lambda cap: receipts.append(format_amount(cap.amount_cents, currency)))
    return bus, receipts


def test_small_yen_charge_sends_receipt():
    order = Order(id="ord_jp", customer_id="cus_jp", amount_cents=50, currency="JPY")
    bus, receipts = _receipt_bus(order.currency)
    gateway = FakeGateway()
    charge(order, gateway, bus)
    assert len(gateway.captured("ord_jp")) == 1
    assert receipts == ["50 JPY"]


def test_small_yen_charge_counts_as_revenue():
    order = Order(id="ord_jp2", customer_id="cus_jp", amount_cents=99, currency="JPY")
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(order, FakeGateway(), bus)
    assert format_amount(revenue.total_cents, "JPY") == "99 JPY"
    assert revenue.charges == 1
