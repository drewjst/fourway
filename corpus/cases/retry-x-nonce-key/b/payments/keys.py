"""Idempotency keys for gateway requests."""

import secrets

from .orders import Order


def idempotency_key(order: Order) -> str:
    """Return a key for one gateway request. Every call returns a new key."""
    return f"charge:{order.id}:{secrets.token_hex(8)}"
