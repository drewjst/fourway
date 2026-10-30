import pytest

from payments.pricing import Catalog, InMemoryPrices


def test_set_price_changes_the_price():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    catalog.set_price("tea", 500)
    assert catalog.price("tea") == 500


def test_set_price_rejects_prices_of_zero_or_less():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    with pytest.raises(ValueError):
        catalog.set_price("tea", 0)
