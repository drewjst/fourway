from payments.pricing import Catalog, InMemoryPrices


def test_quote_reflects_price_change_after_earlier_quote():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    assert catalog.quote(["tea", "cake"]) == 700
    backend.write("tea", 500)
    assert catalog.quote(["tea", "tea"]) == 1000


def test_quote_reflects_price_change_after_single_lookup():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    assert catalog.price("cake") == 300
    backend.write("cake", 350)
    assert catalog.quote(["cake", "tea", "cake"]) == 1100
