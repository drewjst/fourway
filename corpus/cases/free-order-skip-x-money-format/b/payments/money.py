"""Formatting for amounts stored in minor units."""

_DECIMALS = {"USD": 2, "EUR": 2, "JPY": 0}


def format_amount(amount_minor: int, currency: str) -> str:
    decimals = _DECIMALS[currency]
    return f"{amount_minor / 10**decimals:.{decimals}f} {currency}"
