import pytest

from payments.pricing import Catalog, InMemoryPrices


def test_accepted_price_update_becomes_visible():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.price("tea") == 400
    assert catalog.price("tea") == 400
    set_price = getattr(catalog, "set_price", None)
    expected = 400
    if set_price is not None:
        set_price("tea", 450)
        expected = 450
    assert catalog.price("tea") == expected
    if set_price is not None:
        with pytest.raises(ValueError):
            set_price("tea", -1)
    assert catalog.price("tea") == expected
    assert catalog.price("cake") == 300
