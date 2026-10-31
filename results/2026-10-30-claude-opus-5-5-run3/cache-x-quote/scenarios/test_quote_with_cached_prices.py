from payments.pricing import Catalog, InMemoryPrices


def test_quote_counts_repeats_when_price_already_cached():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.price("tea") == 400
    assert catalog.quote(["tea", "tea", "cake"]) == 1100


def test_quote_is_stable_across_calls():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    first = catalog.quote(["tea", "tea", "cake", "cake"])
    second = catalog.quote(["tea", "tea", "cake", "cake"])
    assert first == second == 1400
    assert catalog.quote([]) == 0
