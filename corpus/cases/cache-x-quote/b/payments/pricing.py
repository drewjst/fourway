"""Product prices by SKU, read from the pricing backend."""


class InMemoryPrices:
    """Pricing backend for tests and local runs. Counts reads so tests can see backend load."""

    def __init__(self, prices):
        self._prices = dict(prices)
        self.reads = 0

    def read(self, sku):
        self.reads += 1
        return self._prices[sku]

    def write(self, sku, cents):
        self._prices[sku] = cents

    def skus(self):
        return sorted(self._prices)


class Catalog:
    """Prices by SKU, in cents."""

    def __init__(self, backend):
        self._backend = backend

    def price(self, sku: str) -> int:
        """Return the current price of a SKU."""
        return self._backend.read(sku)

    def skus(self) -> list[str]:
        """Return every SKU the backend knows, sorted."""
        return self._backend.skus()

    def quote(self, skus: list[str]) -> int:
        """Return the total price of a basket. A SKU listed twice counts twice."""
        return sum(self.price(sku) for sku in skus)
