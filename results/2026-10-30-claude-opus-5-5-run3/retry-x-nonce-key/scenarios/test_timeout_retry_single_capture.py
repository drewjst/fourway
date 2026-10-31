from payments.charges import charge
from payments.gateway import GatewayTimeout
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


class KeyRecordingGateway(FakeGateway):
    def __init__(self, faults=None):
        super().__init__(faults)
        self.keys = []

    def capture(self, *, key, amount_cents, reference):
        self.keys.append(key)
        return super().capture(key=key, amount_cents=amount_cents, reference=reference)


def test_lost_response_timeout_never_captures_twice():
    gateway = FakeGateway(faults={1: "timeout_after", 2: "timeout_after"})
    try:
        charge(ORDER, gateway)
    except GatewayTimeout:
        pass
    assert len(gateway.captured("ord_1")) == 1


def test_all_requests_in_one_charge_share_one_key():
    gateway = KeyRecordingGateway(faults={1: "timeout_before", 2: "timeout_before"})
    try:
        charge(ORDER, gateway)
    except GatewayTimeout:
        pass
    assert len(gateway.keys) >= 1
    assert len(set(gateway.keys)) == 1
