from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


def test_charge_captures_the_order_amount():
    capture = charge(ORDER, FakeGateway())
    assert capture.amount_cents == 1250
    assert capture.reference == "ord_1"


def test_charge_publishes_a_success_event():
    bus = EventBus()
    seen = []
    bus.subscribe("payment.captured", seen.append)
    capture = charge(ORDER, FakeGateway(), bus)
    assert seen == [capture]
