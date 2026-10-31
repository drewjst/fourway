import pytest

from payments.charges import charge
from payments.gateway import Capture, Declined
from payments.orders import Order

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


class RememberingGateway:
    """Remembers the outcome of every key, declines included. Declines the first request."""

    def __init__(self):
        self.calls = 0
        self.outcomes = {}
        self.captures = []

    def capture(self, *, key, amount_cents, reference):
        self.calls += 1
        if key in self.outcomes:
            outcome = self.outcomes[key]
            if isinstance(outcome, Declined):
                raise outcome
            return outcome
        if self.calls == 1:
            err = Declined("card declined")
            self.outcomes[key] = err
            raise err
        cap = Capture(id=f"cap_{len(self.captures) + 1}", key=key, amount_cents=amount_cents, reference=reference)
        self.captures.append(cap)
        self.outcomes[key] = cap
        return cap


def test_charge_after_decline_is_a_new_request():
    gateway = RememberingGateway()
    with pytest.raises(Declined):
        charge(ORDER, gateway)
    capture = charge(ORDER, gateway)
    assert capture.amount_cents == 1250
    assert gateway.captures == [capture]
    assert gateway.calls == 2
