from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


class RecordingBus(EventBus):
    def __init__(self):
        super().__init__()
        self.published = []

    def publish(self, name, payload):
        self.published.append(name)
        super().publish(name, payload)


def test_charge_publishes_payment_captured_only():
    bus = RecordingBus()
    seen = []
    bus.subscribe("payment.captured", seen.append)
    capture = charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert seen == [capture]
    assert bus.published == ["payment.captured"]


def test_revenue_counts_payment_captured():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert (revenue.total_cents, revenue.charges) == (1250, 1)
