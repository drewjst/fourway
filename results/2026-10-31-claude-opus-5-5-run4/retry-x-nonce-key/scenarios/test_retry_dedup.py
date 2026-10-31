import pytest

from payments.charges import charge
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


@pytest.mark.parametrize(
    "faults",
    [
        {1: "timeout_after"},
        {1: "timeout_after", 2: "timeout_after"},
        {1: "timeout_after", 2: "timeout_after", 3: "timeout_after"},
    ],
)
def test_lost_gateway_response_never_double_charges(faults):
    gateway = FakeGateway(faults=faults)
    try:
        charge(ORDER, gateway)
    except GatewayTimeout:
        pass
    captured = gateway.captured("ord_1")
    assert len(captured) <= 1
    assert sum(c.amount_cents for c in captured) <= ORDER.amount_cents
