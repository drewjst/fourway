from payments.pricing import Catalog, InMemoryPrices


def test_price_read_before_set_price_reflects_the_new_price():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.price("tea") == 400
    catalog.set_price("tea", 500)
    assert catalog.price("tea") == 500
    assert catalog.price("cake") == 300


def test_successive_price_changes_are_each_visible():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    assert catalog.price("tea") == 400
    catalog.set_price("tea", 500)
    assert catalog.price("tea") == 500
    catalog.set_price("tea", 650)
    assert catalog.price("tea") == 650
