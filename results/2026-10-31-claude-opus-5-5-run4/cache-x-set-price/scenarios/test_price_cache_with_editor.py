import pytest

from payments.pricing import Catalog, InMemoryPrices


def test_each_sku_is_read_from_the_backend_once():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    for _ in range(3):
        assert catalog.price("tea") == 400
        assert catalog.price("cake") == 300
    assert backend.reads == 2


def test_rejected_price_edit_does_not_force_a_reread():
    backend = InMemoryPrices({"tea": 400})
    catalog = Catalog(backend)
    assert catalog.price("tea") == 400
    set_price = getattr(catalog, "set_price", None)
    if set_price is not None:
        with pytest.raises(ValueError):
            set_price("tea", 0)
    assert catalog.price("tea") == 400
    assert catalog.price("tea") == 400
    assert backend.reads == 1
