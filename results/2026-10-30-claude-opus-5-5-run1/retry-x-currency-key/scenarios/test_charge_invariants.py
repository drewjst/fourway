import pytest

from payments.charges import charge
from payments.events import EventBus
from payments.gateway import Declined, GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_5", customer_id="cus_2", amount_cents=700, currency="GBP")


def test_charging_the_same_order_twice_captures_once():
    gateway = FakeGateway()
    a = charge(ORDER, gateway)
    b = charge(ORDER, gateway)
    assert a == b
    assert len(gateway.captured("ord_5")) == 1


@pytest.mark.parametrize("fault", ["timeout_after", "timeout_before"])
def test_timeout_never_double_captures_or_double_publishes(fault):
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway(faults={1: fault})
    raised = False
    result = None
    try:
        result = charge(ORDER, gateway, bus)
    except GatewayTimeout:
        raised = True
    assert len(gateway.captured("ord_5")) <= 1
    assert len(seen) <= 1
    if raised:
        assert seen == []
    else:
        assert seen == [result]
        assert gateway.captured("ord_5") == [result]


def test_decline_is_not_retried_or_published():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway(faults={1: "decline"})
    with pytest.raises(Declined):
        charge(ORDER, gateway, bus)
    assert gateway.calls == 1
    assert gateway.captures == []
    assert seen == []
