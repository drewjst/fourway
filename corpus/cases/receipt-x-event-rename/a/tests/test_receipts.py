from payments import receipts
from payments.events import EventBus
from payments.gateway import Capture

CAPTURE = Capture(id="cap_1", key="charge:ord_1", amount_cents=1250, reference="ord_1")


def test_receipt_text():
    assert receipts.receipt_text(CAPTURE) == "Payment received: $12.50 for order ord_1"


def test_a_receipt_is_sent_for_each_successful_charge():
    bus = EventBus()
    outbox = []
    receipts.install(bus, outbox)
    bus.publish("charge.succeeded", CAPTURE)
    assert outbox == ["Payment received: $12.50 for order ord_1"]
