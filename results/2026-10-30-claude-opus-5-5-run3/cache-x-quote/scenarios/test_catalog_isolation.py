import pytest

from payments.pricing import Catalog, InMemoryPrices


def test_prices_are_per_sku_and_per_catalog():
    a = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    b = Catalog(InMemoryPrices({"tea": 999}))
    assert a.price("tea") == 400
    assert a.price("cake") == 300
    assert b.price("tea") == 999
    assert a.price("tea") == 400


def test_unknown_sku_keeps_raising():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    with pytest.raises(KeyError):
        catalog.price("cake")
    with pytest.raises(KeyError):
        catalog.price("cake")
    assert catalog.price("tea") == 400
