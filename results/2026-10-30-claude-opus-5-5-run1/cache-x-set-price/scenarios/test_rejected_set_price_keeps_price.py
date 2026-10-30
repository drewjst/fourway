import pytest

from payments.pricing import Catalog, InMemoryPrices


def test_rejected_then_accepted_price_change_after_read():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    assert catalog.price("tea") == 400
    with pytest.raises(ValueError):
        catalog.set_price("tea", 0)
    assert catalog.price("tea") == 400
    catalog.set_price("tea", 520)
    assert catalog.price("tea") == 520
