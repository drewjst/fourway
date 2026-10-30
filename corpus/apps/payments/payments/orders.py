from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    id: str
    customer_id: str
    amount_cents: int
    currency: str = "USD"
