from payments import receipts
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_charging_an_order_sends_a_receipt():
    bus = EventBus()
    outbox = []
    receipts.install(bus, outbox)
    charge(Order(id="ord_5", customer_id="cus_5", amount_cents=1250), FakeGateway(), bus)
    assert outbox == ["Payment received: $12.50 for order ord_5"]
