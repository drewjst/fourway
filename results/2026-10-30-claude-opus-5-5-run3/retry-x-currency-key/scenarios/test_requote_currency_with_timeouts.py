from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

USD = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)
EUR = Order(id="ord_1", customer_id="cus_1", amount_cents=1100, currency="EUR")


def charge_with_caller_retry(order, gateway, bus):
    last = None
    for _ in range(3):
        try:
            return charge(order, gateway, bus)
        except GatewayTimeout as exc:
            last = exc
    raise last


def test_requoted_order_gets_own_capture_despite_timeout():
    gateway = FakeGateway(faults={2: "timeout_after"})
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    first = charge_with_caller_retry(USD, gateway, bus)
    second = charge_with_caller_retry(EUR, gateway, bus)
    assert first.amount_cents == 1250
    assert second.amount_cents == 1100
    assert second.id != first.id
    assert second.key != first.key
    assert len(gateway.captured("ord_1")) == 2
    assert (revenue.total_cents, revenue.charges) == (2350, 2)
