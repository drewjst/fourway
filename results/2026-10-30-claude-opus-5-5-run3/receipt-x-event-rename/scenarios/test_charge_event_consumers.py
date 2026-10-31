import importlib

from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def _optional_module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            return None
        raise


def test_every_installed_charge_consumer_receives_each_charge_once():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    receipts = _optional_module("payments.receipts")
    outbox = []
    if receipts is not None:
        receipts.install(bus, outbox)

    gateway = FakeGateway()
    capture = charge(Order(id="ord_9", customer_id="cus_2", amount_cents=500), gateway, bus)

    assert gateway.captured("ord_9") == [capture]
    assert (revenue.total_cents, revenue.charges) == (500, 1)
    if receipts is not None:
        assert len(outbox) == 1
        assert "ord_9" in outbox[0]
