from payments.keys import idempotency_key
from payments.orders import Order

ORDER = Order(id="ord_1", customer_id="cus_1", amount_cents=1250)


def test_key_names_the_order():
    assert idempotency_key(ORDER).startswith("charge:ord_1")


def test_key_is_stable_for_an_order():
    assert idempotency_key(ORDER) == idempotency_key(ORDER)
