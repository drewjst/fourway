from payments.pricing import Catalog, InMemoryPrices


def test_quote_is_right_after_prices_were_already_read():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.price("tea") == 400
    assert catalog.quote(["tea", "tea", "cake"]) == 1100
