import pytest

from payments.charges import charge
from payments.events import EventBus
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway


@pytest.mark.parametrize("currency", ["USD", "EUR"])
@pytest.mark.parametrize(
    "faults",
    [
        {1: "timeout_after"},
        {1: "timeout_after", 2: "timeout_after"},
        {1: "timeout_before", 2: "timeout_after"},
    ],
)
def test_lost_responses_never_double_capture(currency, faults):
    order = Order(id="ord_x", customer_id="cus_1", amount_cents=500, currency=currency)
    gateway = FakeGateway(faults=faults)
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    try:
        charge(order, gateway, bus)
    except GatewayTimeout:
        pass
    caps = gateway.captured("ord_x")
    assert len(caps) <= 1
    assert len(seen) <= 1
    for event in seen:
        assert event in caps


def test_charging_same_order_twice_captures_once():
    order = Order(id="ord_y", customer_id="cus_1", amount_cents=700, currency="EUR")
    gateway = FakeGateway()
    first = charge(order, gateway)
    second = charge(order, gateway)
    assert first == second
    assert gateway.captured("ord_y") == [first]
