from payments import receipts
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_charge_sends_a_receipt():
    bus = EventBus()
    outbox = []
    receipts.install(bus, outbox)
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert outbox == ["Payment received: $12.50 for order ord_1"]


def test_each_charge_sends_exactly_one_receipt_alongside_analytics():
    from payments import analytics

    bus = EventBus()
    outbox = []
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    receipts.install(bus, outbox)
    gateway = FakeGateway()
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), gateway, bus)
    charge(Order(id="ord_2", customer_id="cus_2", amount_cents=750), gateway, bus)
    assert outbox == [
        "Payment received: $12.50 for order ord_1",
        "Payment received: $7.50 for order ord_2",
    ]
    assert (revenue.total_cents, revenue.charges) == (2000, 2)
