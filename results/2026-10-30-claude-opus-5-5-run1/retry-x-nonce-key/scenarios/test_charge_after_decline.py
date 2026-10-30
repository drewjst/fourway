import pytest

from payments.charges import charge
from payments.gateway import Declined
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


class StickyGateway:
    """Remembers the outcome of every key, declines included, like the real gateway."""

    def __init__(self):
        self.declining = True
        self.outcomes = {}
        self.inner = FakeGateway()

    def capture(self, *, key, amount_cents, reference):
        if key in self.outcomes:
            outcome = self.outcomes[key]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome
        if self.declining:
            err = Declined(key)
            self.outcomes[key] = err
            raise err
        cap = self.inner.capture(key=key, amount_cents=amount_cents, reference=reference)
        self.outcomes[key] = cap
        return cap


def test_charge_succeeds_after_card_is_fixed():
    gateway = StickyGateway()
    with pytest.raises(Declined):
        charge(ORDER, gateway)
    gateway.declining = False
    capture = charge(ORDER, gateway)
    assert capture.amount_cents == 1250
    assert capture.reference == "ord_1"
    assert gateway.inner.captured("ord_1") == [capture]
