from payments import analytics
from payments.charges import charge
from payments.events import EventBus
from payments.orders import Order
from payments.testing import FakeGateway


def test_revenue_counts_each_charge():
    bus = EventBus()
    revenue = analytics.Revenue()
    analytics.install(bus, revenue)
    charge(Order(id="ord_1", customer_id="cus_1", amount_cents=1250), FakeGateway(), bus)
    charge(Order(id="ord_2", customer_id="cus_1", amount_cents=750), FakeGateway(), bus)
    assert (revenue.total_cents, revenue.charges) == (2000, 2)
