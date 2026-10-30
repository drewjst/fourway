import pytest

from payments.charges import charge
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


class RecordingGateway:
    def __init__(self, inner):
        self.inner = inner
        self.keys = []

    def capture(self, *, key, amount_cents, reference):
        self.keys.append(key)
        return self.inner.capture(key=key, amount_cents=amount_cents, reference=reference)


def _charge_quietly(gateway):
    try:
        return charge(ORDER, gateway)
    except GatewayTimeout:
        return None


def test_lost_response_does_not_double_capture():
    gateway = FakeGateway(faults={1: "timeout_after"})
    _charge_quietly(gateway)
    assert len(gateway.captured("ord_1")) <= 1


def test_repeated_lost_responses_capture_at_most_once():
    gateway = FakeGateway(faults={1: "timeout_after", 2: "timeout_after"})
    _charge_quietly(gateway)
    assert len(gateway.captured("ord_1")) <= 1


def test_one_charge_call_uses_one_key_across_attempts():
    gateway = RecordingGateway(FakeGateway(faults={1: "timeout_after"}))
    _charge_quietly(gateway)
    assert len(gateway.keys) >= 1
    assert len(set(gateway.keys)) == 1
