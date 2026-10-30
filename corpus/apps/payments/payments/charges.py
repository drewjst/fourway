"""Charge an order through the payment gateway."""

from .events import EventBus
from .gateway import Capture, Gateway
from .keys import idempotency_key
from .orders import Order


def charge(order: Order, gateway: Gateway, bus: EventBus | None = None) -> Capture:
    capture = gateway.capture(
        key=idempotency_key(order),
        amount_cents=order.amount_cents,
        reference=order.id,
    )
    if bus is not None:
        bus.publish("charge.succeeded", capture)
    return capture
