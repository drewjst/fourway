"""Customer receipts, sent when a charge succeeds."""


def receipt_text(capture):
    return f"Payment received: ${capture.amount_cents / 100:.2f} for order {capture.reference}"


def install(bus, outbox):
    """Append a receipt to ``outbox`` for every successful charge."""
    bus.subscribe("charge.succeeded", lambda capture: outbox.append(receipt_text(capture)))
