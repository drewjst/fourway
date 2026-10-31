from payments.pricing import Catalog, InMemoryPrices


def test_price_read_before_set_price_reflects_new_price():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    assert catalog.price("tea") == 400
    catalog.set_price("tea", 500)
    assert catalog.price("tea") == 500


def test_only_the_updated_sku_changes_after_reads():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.price("tea") == 400
    assert catalog.price("cake") == 300
    catalog.set_price("tea", 650)
    assert catalog.price("tea") == 650
    assert catalog.price("cake") == 300
