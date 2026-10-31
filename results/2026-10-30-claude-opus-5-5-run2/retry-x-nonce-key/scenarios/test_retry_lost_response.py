import itertools
import secrets

import pytest

from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


@pytest.fixture(autouse=True)
def deterministic_tokens(monkeypatch):
    counter = itertools.count(1)
    monkeypatch.setattr(secrets, "token_hex", lambda n=None: f"{next(counter):016x}")


def test_retry_after_lost_response_returns_the_single_capture():
    gateway = FakeGateway(faults={1: "timeout_after"})
    capture = charge(ORDER, gateway)
    assert gateway.calls == 2
    assert gateway.captured("ord_1") == [capture]


def test_retry_after_lost_response_publishes_once_for_one_capture():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway(faults={1: "timeout_after"})
    capture = charge(ORDER, gateway, bus)
    assert seen == [capture]
    assert len(gateway.captures) == 1
