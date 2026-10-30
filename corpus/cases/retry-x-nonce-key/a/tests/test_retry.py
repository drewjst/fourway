import pytest

from payments.charges import charge
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


def test_charge_retries_after_a_timeout():
    gateway = FakeGateway(faults={1: "timeout_before"})
    capture = charge(ORDER, gateway)
    assert gateway.calls == 2
    assert gateway.captured("ord_1") == [capture]


def test_charge_gives_up_after_three_timeouts():
    gateway = FakeGateway(faults={1: "timeout_before", 2: "timeout_before", 3: "timeout_before"})
    with pytest.raises(GatewayTimeout):
        charge(ORDER, gateway)
    assert gateway.calls == 3
