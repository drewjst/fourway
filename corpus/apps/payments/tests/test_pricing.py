from payments.pricing import Catalog, InMemoryPrices


def test_price_reads_the_backend():
    catalog = Catalog(InMemoryPrices({"tea": 400}))
    assert catalog.price("tea") == 400


def test_skus_are_sorted():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300}))
    assert catalog.skus() == ["cake", "tea"]
