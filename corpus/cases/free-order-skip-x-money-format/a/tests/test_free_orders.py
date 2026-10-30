from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_free_orders_publish_no_success_event():
    bus = EventBus()
    seen = []
    bus.subscribe("charge.succeeded", seen.append)
    charge(Order(id="ord_0", customer_id="cus_1", amount_cents=0), FakeGateway(), bus)
    assert seen == []
