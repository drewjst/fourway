from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.money import format_amount
from payments.orders import Order
from payments.testing import FakeGateway


def test_formatted_yen_revenue_from_events():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(Order(id="ord_jp", customer_id="cus_jp", amount_cents=80, currency="JPY"), FakeGateway(), bus)
    assert format_amount(revenue.total_cents, "JPY") == "80 JPY"


def test_receipt_amount_formats_from_event_payload():
    bus = EventBus()
    receipts = []
    bus.subscribe("charge.succeeded", lambda cap: receipts.append(format_amount(cap.amount_cents, "JPY")))
    charge(Order(id="ord_jp", customer_id="cus_jp", amount_cents=99, currency="JPY"), FakeGateway(), bus)
    assert receipts == ["99 JPY"]
