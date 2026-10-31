from payments.pricing import Catalog, InMemoryPrices


def test_quote_counts_repeated_skus_after_prices_were_looked_up():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    assert catalog.price("tea") == 400
    assert catalog.price("cake") == 300
    assert catalog.quote(["tea", "tea", "cake"]) == 1100
    assert catalog.quote(["cake", "tea", "cake", "tea"]) == 1400


def test_repeated_quotes_give_the_same_total():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    first = catalog.quote(["tea", "tea", "cake"])
    second = catalog.quote(["tea", "tea", "cake"])
    assert first == second == 1100
    assert catalog.quote([]) == 0
