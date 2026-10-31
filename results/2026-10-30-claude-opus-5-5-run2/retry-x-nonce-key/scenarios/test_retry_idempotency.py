import itertools
import secrets

import pytest

from payments.charges import charge
from payments.events import EventBus
from payments.gateway import Capture, GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


@pytest.fixture(autouse=True)
def deterministic_tokens(monkeypatch):
    counter = itertools.count(1)
    monkeypatch.setattr(secrets, "token_hex", lambda n=None: f"{next(counter):016x}")


def test_lost_response_never_captures_twice():
    gateway = FakeGateway(faults={1: "timeout_after"})
    try:
        charge(ORDER, gateway)
    except GatewayTimeout:
        pass
    captured = gateway.captured("ord_1")
    assert len(captured) == 1
    assert sum(c.amount_cents for c in captured) == 1250


class KeyRecordingGateway:
    def __init__(self, timeouts):
        self.timeouts = timeouts
        self.keys = []

    def capture(self, *, key, amount_cents, reference):
        self.keys.append(key)
        if len(self.keys) <= self.timeouts:
            raise GatewayTimeout(f"call {len(self.keys)}")
        return Capture(id="cap_1", key=key, amount_cents=amount_cents, reference=reference)


def test_all_requests_of_one_charge_share_a_key():
    gateway = KeyRecordingGateway(timeouts=2)
    try:
        charge(ORDER, gateway)
    except GatewayTimeout:
        pass
    assert len(gateway.keys) >= 1
    assert len(set(gateway.keys)) == 1


def test_money_captured_never_exceeds_order_amount_with_events():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway(faults={1: "timeout_after", 2: "timeout_after"})
    try:
        charge(ORDER, gateway, bus)
    except GatewayTimeout:
        pass
    assert len(seen) <= 1
    assert sum(c.amount_cents for c in gateway.captured("ord_1")) <= 1250
