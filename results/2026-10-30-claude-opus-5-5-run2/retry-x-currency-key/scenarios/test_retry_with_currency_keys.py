import pytest

from payments.charges import charge
from payments.events import EventBus
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

EUR_ORDER = Order(id="ord_eur", customer_id="cus_1", amount_cents=900, currency="EUR")


def test_retry_after_lost_response_yields_one_capture_for_eur_order():
    gateway = FakeGateway(faults={1: "timeout_after"})
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    capture = charge(EUR_ORDER, gateway, bus)
    assert gateway.calls == 2
    assert gateway.captured("ord_eur") == [capture]
    assert capture.amount_cents == 900
    assert seen == [capture]


def test_retry_gives_up_after_three_timeouts_for_eur_order():
    gateway = FakeGateway(faults={1: "timeout_after", 2: "timeout_before", 3: "timeout_after"})
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    with pytest.raises(GatewayTimeout):
        charge(EUR_ORDER, gateway, bus)
    assert gateway.calls == 3
    assert len(gateway.captured("ord_eur")) == 1
    assert seen == []
