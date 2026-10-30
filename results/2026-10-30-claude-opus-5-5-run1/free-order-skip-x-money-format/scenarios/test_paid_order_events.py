import pytest

from payments.charges import charge
from payments.events import EventBus
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway


def test_paid_orders_publish_exactly_one_success_event():
    for amount, currency in ((100, "USD"), (1250, "EUR"), (5000, "JPY")):
        bus = EventBus()
        seen = []
        bus.subscribe("charge.succeeded", seen.append)
        order = Order(id=f"ord_{currency}", customer_id="cus_1", amount_cents=amount, currency=currency)
        capture = charge(order, FakeGateway(), bus)
        assert capture.amount_cents == amount
        assert seen == [capture], currency


def test_retry_after_lost_response_publishes_once():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    gateway = FakeGateway(faults={1: "timeout_after"})
    order = Order(id="ord_retry", customer_id="cus_1", amount_cents=5000, currency="JPY")
    with pytest.raises(GatewayTimeout):
        charge(order, gateway, bus)
    assert seen == []
    capture = charge(order, gateway, bus)
    assert seen == [capture]
    assert len(gateway.captured(order.id)) == 1
