from payments.pricing import Catalog, InMemoryPrices


def test_quote_counts_repeats_with_warm_cache():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    assert catalog.price("tea") == 400
    assert catalog.quote(["tea", "tea", "cake", "tea"]) == 1500
