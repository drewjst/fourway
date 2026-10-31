from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway

EUR_ORDER = Order(id="ord_9", customer_id="cus_1", amount_cents=1100, currency="EUR")


class KeyRecorder:
    def __init__(self, inner):
        self.inner = inner
        self.keys = []

    def capture(self, *, key, amount_cents, reference):
        self.keys.append(key)
        return self.inner.capture(key=key, amount_cents=amount_cents, reference=reference)


def test_retry_after_lost_response_captures_once_for_eur_order():
    fake = FakeGateway(faults={1: "timeout_after"})
    gateway = KeyRecorder(fake)
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    capture = charge(EUR_ORDER, gateway, bus)
    assert fake.calls == 2
    assert fake.captured("ord_9") == [capture]
    assert capture.amount_cents == 1100
    assert seen == [capture]
    assert len(gateway.keys) == 2
    assert len(set(gateway.keys)) == 1


def test_retry_after_timeout_before_for_eur_order():
    fake = FakeGateway(faults={1: "timeout_before", 2: "timeout_before"})
    capture = charge(EUR_ORDER, fake)
    assert fake.calls == 3
    assert fake.captured("ord_9") == [capture]
