"""Charge an order through the payment gateway."""

from .events import EventBus
from .gateway import Capture, Gateway, GatewayTimeout
from .keys import idempotency_key
from .orders import Order

MAX_ATTEMPTS = 3


def charge(order: Order, gateway: Gateway, bus: EventBus | None = None) -> Capture:
    """Capture the order amount, retrying gateway timeouts up to MAX_ATTEMPTS times."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            capture = gateway.capture(
                key=idempotency_key(order),
                amount_cents=order.amount_cents,
                reference=order.id,
            )
            break
        except GatewayTimeout:
            if attempt == MAX_ATTEMPTS:
                raise
    if bus is not None:
        bus.publish("charge.succeeded", capture)
    return capture
