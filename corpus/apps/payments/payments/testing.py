"""In-memory gateway for tests, with a deterministic fault schedule."""

from .gateway import Capture, Declined, GatewayTimeout


class FakeGateway:
    """Records captures and deduplicates them by idempotency key, as the real gateway does.

    ``faults`` maps a 1-based call number to one of:

    - ``"timeout_before"``: raise GatewayTimeout without capturing.
    - ``"timeout_after"``: capture, then raise GatewayTimeout. The response is lost.
    - ``"decline"``: raise Declined without capturing.
    """

    def __init__(self, faults=None):
        self.faults = dict(faults or {})
        self.calls = 0
        self.captures = []
        self._by_key = {}

    def capture(self, *, key, amount_cents, reference):
        self.calls += 1
        fault = self.faults.get(self.calls)
        if fault == "timeout_before":
            raise GatewayTimeout(f"call {self.calls}")
        if fault == "decline":
            raise Declined(f"call {self.calls}")
        if key not in self._by_key:
            capture = Capture(
                id=f"cap_{len(self.captures) + 1}",
                key=key,
                amount_cents=amount_cents,
                reference=reference,
            )
            self.captures.append(capture)
            self._by_key[key] = capture
        if fault == "timeout_after":
            raise GatewayTimeout(f"call {self.calls}")
        return self._by_key[key]

    def captured(self, reference):
        """Return every capture made for ``reference``."""
        return [c for c in self.captures if c.reference == reference]
