"""Idempotency keys for gateway requests."""

from .orders import Order


def idempotency_key(order: Order) -> str:
    return f"charge:{order.id}:{order.currency}"
