from payments.pricing import Catalog, InMemoryPrices


def test_quote_counts_repeats_after_cache_is_warm():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.price("tea") == 400
    assert catalog.quote(["tea", "tea", "cake"]) == 1100


def test_repeated_quotes_give_the_same_total():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    first = catalog.quote(["tea", "cake", "tea", "tea"])
    second = catalog.quote(["tea", "cake", "tea", "tea"])
    assert first == second == 1500
