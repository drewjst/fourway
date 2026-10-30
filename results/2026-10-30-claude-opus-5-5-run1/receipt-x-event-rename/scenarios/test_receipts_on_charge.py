from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_charging_an_order_sends_a_receipt():
    from payments import receipts

    bus = EventBus()
    outbox = []
    receipts.install(bus, outbox)
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert outbox == ["Payment received: $12.50 for order ord_1"]


def test_receipts_and_revenue_both_see_the_charge():
    from payments import receipts

    bus = EventBus()
    outbox = []
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    receipts.install(bus, outbox)
    charge(Order(id="ord_7", customer_id="cus_2", amount_cents=750), FakeGateway(), bus)
    assert (revenue.total_cents, revenue.charges) == (750, 1)
    assert outbox == ["Payment received: $7.50 for order ord_7"]
