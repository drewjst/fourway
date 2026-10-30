from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_a_small_paid_order_still_publishes_its_success_event():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    charge(Order(id="ord_6", customer_id="cus_6", amount_cents=50), FakeGateway(), bus)
    assert len(seen) == 1
