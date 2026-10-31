from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


class RecordingBus(EventBus):
    def __init__(self):
        super().__init__()
        self.subscribed = set()
        self.published = set()

    def subscribe(self, name, handler):
        self.subscribed.add(name)
        super().subscribe(name, handler)

    def publish(self, name, payload):
        self.published.add(name)
        super().publish(name, payload)


def _install_all(bus):
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    outbox = None
    try:
        from payments import receipts
    except ImportError:
        receipts = None
    if receipts is not None:
        outbox = []
        receipts.install(bus, outbox)
    return revenue, outbox


def test_every_subscribed_event_is_published_by_charge():
    bus = RecordingBus()
    _install_all(bus)
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    assert bus.subscribed <= bus.published, (bus.subscribed, bus.published)


def test_every_installed_consumer_sees_each_charge_once():
    bus = RecordingBus()
    revenue, outbox = _install_all(bus)
    gateway = FakeGateway()
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), gateway, bus)
    charge(Order(id="ord_2", customer_id="cus_2", amount_cents=750), gateway, bus)
    assert revenue.charges == 2
    if outbox is not None:
        assert len(outbox) == 2
