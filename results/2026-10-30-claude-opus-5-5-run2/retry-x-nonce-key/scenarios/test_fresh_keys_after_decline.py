import itertools
import secrets

import pytest

from payments.charges import charge
from payments.gateway import Capture, Declined
from payments.orders import Order

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


@pytest.fixture(autouse=True)
def deterministic_tokens(monkeypatch):
    counter = itertools.count(1)
    monkeypatch.setattr(secrets, "token_hex", lambda n=None: f"{next(counter):016x}")


class RememberingGateway:
    """Remembers each key's outcome, declines included. The first key ever seen is declined."""

    def __init__(self):
        self.outcomes = {}
        self.keys = []

    def capture(self, *, key, amount_cents, reference):
        self.keys.append(key)
        if key not in self.outcomes:
            if not self.outcomes:
                self.outcomes[key] = Declined("card declined")
            else:
                self.outcomes[key] = Capture(
                    id=f"cap_{len(self.outcomes)}", key=key, amount_cents=amount_cents, reference=reference
                )
        outcome = self.outcomes[key]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_charge_after_decline_succeeds():
    gateway = RememberingGateway()
    with pytest.raises(Declined):
        charge(ORDER, gateway)
    capture = charge(ORDER, gateway)
    assert capture.amount_cents == 1250
    assert capture.reference == "ord_1"


def test_separate_charges_send_distinct_keys_naming_the_order():
    gateway = RememberingGateway()
    with pytest.raises(Declined):
        charge(ORDER, gateway)
    charge(ORDER, gateway)
    assert len(gateway.keys) == 2
    assert gateway.keys[0] != gateway.keys[1]
    assert all(k.startswith("charge:ord_1:") for k in gateway.keys)
