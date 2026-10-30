from payments.pricing import Catalog, InMemoryPrices


def test_set_price_is_visible_after_price_was_already_read():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.price("tea") == 400
    catalog.set_price("tea", 500)
    assert catalog.price("tea") == 500
    assert catalog.price("cake") == 300


def test_successive_set_price_calls_are_each_visible():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    seen = [catalog.price("tea")]
    catalog.set_price("tea", 450)
    seen.append(catalog.price("tea"))
    catalog.set_price("tea", 475)
    seen.append(catalog.price("tea"))
    assert seen == [400, 450, 475]
