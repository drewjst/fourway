from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_revenue_from_a_yen_charge_formats_without_decimals():
    from payments.money import format_amount

    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    order = Order(id="ord_jpy", customer_id="cus_1", amount_cents=1250, currency="JPY")
    charge(order, FakeGateway(), bus)
    assert format_amount(revenue.total_cents, order.currency) == "1250 JPY"


def test_captured_amounts_format_in_their_currency():
    from payments.money import format_amount

    usd = Order(id="ord_usd", customer_id="cus_1", amount_cents=1250, currency="USD")
    capture = charge(usd, FakeGateway())
    assert format_amount(capture.amount_cents, usd.currency) == "12.50 USD"
    free = Order(id="ord_free", customer_id="cus_1", amount_cents=0, currency="JPY")
    free_capture = charge(free, FakeGateway())
    assert format_amount(free_capture.amount_cents, "JPY") == "0 JPY"
    assert format_amount(0, "USD") == "0.00 USD"
