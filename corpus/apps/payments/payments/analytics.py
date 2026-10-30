"""Revenue counters fed from payment events."""


class Revenue:
    def __init__(self):
        self.total_cents = 0
        self.charges = 0

    def on_charge(self, capture):
        self.total_cents += capture.amount_cents
        self.charges += 1


def install(bus, revenue):
    bus.subscribe("charge.succeeded", revenue.on_charge)
