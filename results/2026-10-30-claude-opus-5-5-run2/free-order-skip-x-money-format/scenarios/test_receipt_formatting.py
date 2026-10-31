from payments.charges import charge
from payments.events import EventBus
from payments.money import format_amount
from payments.orders import Order
from payments.testing import FakeGateway


def test_yen_receipt_from_success_event():
    order = Order(id="ord_r", customer_id="cus_1", amount_cents=1250, currency="JPY")
    bus = EventBus()
    receipts = []
    bus.subscribe(
        "charge.succeeded",
        lambda c: receipts.append(format_amount(c.amount_cents, order.currency)),
    )
    charge(order, FakeGateway(), bus)
    assert receipts == ["1250 JPY"]


def test_small_amounts_format_per_currency():
    assert format_amount(50, "JPY") == "50 JPY"
    assert format_amount(50, "USD") == "0.50 USD"
