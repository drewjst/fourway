from payments.pricing import Catalog, InMemoryPrices


def test_quote_counts_repeated_skus():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.quote(["tea", "tea", "cake"]) == 1100
