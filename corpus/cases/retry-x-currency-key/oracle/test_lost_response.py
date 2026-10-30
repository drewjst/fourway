from payments.charges import charge
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway


def test_a_lost_response_does_not_charge_twice():
    order = Order(id="ord_9", customer_id="cus_9", amount_cents=4200)
    gateway = FakeGateway(faults={1: "timeout_after"})
    try:
        charge(order, gateway)
    except GatewayTimeout:
        pass
    assert len(gateway.captured("ord_9")) == 1
