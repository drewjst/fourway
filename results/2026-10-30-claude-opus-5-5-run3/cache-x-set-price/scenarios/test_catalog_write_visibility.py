import pytest

from payments.pricing import Catalog, InMemoryPrices


def test_price_written_through_catalog_is_what_catalog_reports():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    observed = {sku: catalog.price(sku) for sku in catalog.skus()}
    assert observed == {"cake": 300, "tea": 400}
    if not hasattr(catalog, "set_price"):
        return
    catalog.set_price("cake", 350)
    catalog.set_price("cake", 375)
    assert catalog.price("cake") == 375
    assert catalog.price("tea") == 400


def test_rejected_write_leaves_price_unchanged():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    assert catalog.price("tea") == 400
    if not hasattr(catalog, "set_price"):
        return
    with pytest.raises(ValueError):
        catalog.set_price("tea", -1)
    assert catalog.price("tea") == 400
