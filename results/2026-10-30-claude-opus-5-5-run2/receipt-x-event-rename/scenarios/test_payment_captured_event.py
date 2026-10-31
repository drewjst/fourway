from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_charge_publishes_payment_captured():
    bus = EventBus()
    seen = []
    bus.subscribe("payment.captured", seen.append)
    capture = charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert seen == [capture]


def test_revenue_still_counts_after_rename():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    seen = []
    bus.subscribe("payment.captured", seen.append)
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert len(seen) == 1
    assert (revenue.total_cents, revenue.charges) == (1250, 1)
