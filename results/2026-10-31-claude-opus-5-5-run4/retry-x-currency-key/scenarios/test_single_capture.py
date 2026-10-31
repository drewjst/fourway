import pytest

from payments.charges import charge
from payments.events import EventBus
from payments.gateway import Declined, GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_5", customer_id="cus_5", amount_cents=900, currency="GBP")


def test_caller_retry_after_lost_response_captures_once():
    gateway = FakeGateway(faults={1: "timeout_after"})
    capture = None
    for _ in range(3):
        try:
            capture = charge(ORDER, gateway)
            break
        except GatewayTimeout:
            continue
    assert capture is not None
    assert gateway.captured("ord_5") == [capture]
    assert capture.amount_cents == 900


def test_charging_same_order_twice_captures_once():
    gateway = FakeGateway()
    first = charge(ORDER, gateway)
    second = charge(ORDER, gateway)
    assert first == second
    assert len(gateway.captured("ord_5")) == 1


def test_decline_captures_nothing_and_publishes_nothing():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway(faults={1: "decline"})
    with pytest.raises(Declined):
        charge(ORDER, gateway, bus)
    assert gateway.calls == 1
    assert gateway.captured("ord_5") == []
    assert seen == []
