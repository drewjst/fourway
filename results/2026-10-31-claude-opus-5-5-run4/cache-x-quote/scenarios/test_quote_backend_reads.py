from payments.pricing import Catalog, InMemoryPrices


def test_quote_reads_each_distinct_sku_once():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    assert catalog.quote(["tea", "tea", "cake", "tea"]) == 1500
    assert backend.reads == 2


def test_quote_reuses_prices_read_by_price():
    backend = InMemoryPrices({"tea": 400})
    catalog = Catalog(backend)
    catalog.price("tea")
    assert catalog.quote(["tea", "tea"]) == 800
    assert backend.reads == 1
