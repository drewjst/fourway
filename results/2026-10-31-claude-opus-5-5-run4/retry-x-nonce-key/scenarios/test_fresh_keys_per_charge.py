import pytest

from payments.charges import charge
from payments.gateway import Declined
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


class RecordingGateway(FakeGateway):
    def __init__(self, faults=None):
        super().__init__(faults)
        self.keys = []

    def capture(self, *, key, amount_cents, reference):
        self.keys.append(key)
        return super().capture(key=key, amount_cents=amount_cents, reference=reference)


def test_charge_after_decline_sends_a_new_key():
    gateway = RecordingGateway(faults={1: "decline"})
    with pytest.raises(Declined):
        charge(ORDER, gateway)
    charge(ORDER, gateway)
    assert len(gateway.keys) == 2
    assert gateway.keys[0] != gateway.keys[1]
    assert all(k.startswith("charge:ord_1:") for k in gateway.keys)


def test_separate_charge_calls_are_new_requests():
    gateway = RecordingGateway()
    first = charge(ORDER, gateway)
    second = charge(ORDER, gateway)
    assert first.key != second.key
    assert first.id != second.id
