from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway

try:
    from payments import receipts
except ImportError:
    receipts = None


class RecordingBus(EventBus):
    def __init__(self):
        super().__init__()
        self.subscribed = set()
        self.published = []

    def subscribe(self, name, handler):
        self.subscribed.add(name)
        super().subscribe(name, handler)

    def publish(self, name, payload):
        self.published.append(name)
        super().publish(name, payload)


def _install_all(bus):
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    outbox = None
    if receipts is not None:
        outbox = []
        receipts.install(bus, outbox)
    return revenue, outbox


def test_every_subscribed_event_is_published_by_charge():
    bus = RecordingBus()
    _install_all(bus)
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert bus.subscribed <= set(bus.published), (bus.subscribed, bus.published)


def test_each_consumer_handles_a_charge_exactly_once():
    bus = EventBus()
    revenue, outbox = _install_all(bus)
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    charge(Order(id="ord_2", customer_id="cus_1", amount_cents=500), FakeGateway(), bus)
    assert (revenue.total_cents, revenue.charges) == (1750, 2)
    if outbox is not None:
        assert len(outbox) == 2
