from payments.charges import charge
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

USD = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)
EUR = Order(id="ord_1", customer_id="cus_1", amount_cents=1100, currency="EUR")


def _charge_with_caller_retry(order, gateway, tries=3):
    last = None
    for _ in range(tries):
        try:
            return charge(order, gateway)
        except GatewayTimeout as exc:
            last = exc
    raise last


def test_each_currency_gets_its_own_capture():
    gateway = FakeGateway()
    first = charge(USD, gateway)
    second = charge(EUR, gateway)
    assert first.key != second.key
    assert sorted(c.amount_cents for c in gateway.captured("ord_1")) == [1100, 1250]
    assert second.amount_cents == 1100


def test_requote_with_lost_response_captures_once_per_currency():
    gateway = FakeGateway(faults={2: "timeout_after"})
    first = _charge_with_caller_retry(USD, gateway)
    second = _charge_with_caller_retry(EUR, gateway)
    assert first.amount_cents == 1250
    assert second.amount_cents == 1100
    captures = gateway.captured("ord_1")
    assert len(captures) == 2
    assert sorted(c.amount_cents for c in captures) == [1100, 1250]
