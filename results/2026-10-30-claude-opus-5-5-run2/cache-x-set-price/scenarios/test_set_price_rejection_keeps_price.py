import pytest

from payments.pricing import Catalog, InMemoryPrices


def test_rejected_price_leaves_previously_read_price_unchanged():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    assert catalog.price("tea") == 400
    with pytest.raises(ValueError):
        catalog.set_price("tea", 0)
    with pytest.raises(ValueError):
        catalog.set_price("tea", -5)
    assert catalog.price("tea") == 400


def test_set_price_on_unread_sku_is_visible():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    catalog.set_price("tea", 450)
    assert catalog.price("tea") == 450
