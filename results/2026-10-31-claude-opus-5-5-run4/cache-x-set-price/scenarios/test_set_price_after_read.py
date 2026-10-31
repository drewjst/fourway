from payments.pricing import Catalog, InMemoryPrices


def test_set_price_is_visible_after_the_sku_was_already_read():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    assert catalog.price("tea") == 400
    catalog.set_price("tea", 500)
    assert catalog.price("tea") == 500


def test_set_price_updates_only_the_edited_sku_after_reads():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.price("tea") == 400
    assert catalog.price("cake") == 300
    catalog.set_price("cake", 350)
    assert catalog.price("cake") == 350
    assert catalog.price("tea") == 400
