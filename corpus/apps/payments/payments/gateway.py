"""Payment gateway client interface and errors."""

from dataclasses import dataclass
from typing import Protocol


class GatewayTimeout(Exception):
    """The gateway did not answer in time. The capture may or may not have happened."""


class Declined(Exception):
    """The gateway refused the capture."""


@dataclass(frozen=True)
class Capture:
    id: str
    key: str
    amount_cents: int
    reference: str


class Gateway(Protocol):
    def capture(self, *, key: str, amount_cents: int, reference: str) -> Capture: ...
