from payments.pricing import Catalog, InMemoryPrices


def test_a_price_change_reaches_a_catalog_that_already_read_the_price():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    assert catalog.price("tea") == 400
    catalog.set_price("tea", 500)
    assert catalog.price("tea") == 500
