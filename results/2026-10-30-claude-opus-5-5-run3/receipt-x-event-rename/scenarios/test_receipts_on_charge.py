from payments import analytics, receipts
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_charging_an_order_sends_exactly_one_receipt():
    bus = EventBus()
    outbox = []
    receipts.install(bus, outbox)
    charge(Order(id="ord_7", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert outbox == ["Payment received: $12.50 for order ord_7"]


def test_receipts_and_revenue_both_follow_real_charges():
    bus = EventBus()
    outbox = []
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    receipts.install(bus, outbox)
    gateway = FakeGateway()
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), gateway, bus)
    charge(Order(id="ord_2", customer_id="cus_1", amount_cents=750), gateway, bus)
    assert (revenue.total_cents, revenue.charges) == (2000, 2)
    assert outbox == [
        "Payment received: $12.50 for order ord_1",
        "Payment received: $7.50 for order ord_2",
    ]
