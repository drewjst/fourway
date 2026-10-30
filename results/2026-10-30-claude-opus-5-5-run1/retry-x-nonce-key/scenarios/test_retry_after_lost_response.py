from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


def test_charge_recovers_from_a_lost_response_with_one_capture():
    gateway = FakeGateway(faults={1: "timeout_after"})
    capture = charge(ORDER, gateway)
    assert gateway.calls == 2
    assert gateway.captured("ord_1") == [capture]


def test_revenue_matches_gateway_after_retry():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    gateway = FakeGateway(faults={1: "timeout_after"})
    charge(ORDER, gateway, bus)
    captured_total = sum(c.amount_cents for c in gateway.captured("ord_1"))
    assert (revenue.total_cents, revenue.charges) == (1250, 1)
    assert captured_total == revenue.total_cents
