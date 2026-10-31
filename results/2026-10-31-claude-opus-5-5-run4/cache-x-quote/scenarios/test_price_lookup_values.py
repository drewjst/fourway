from payments.pricing import Catalog, InMemoryPrices


def test_interleaved_lookups_return_each_skus_price():
    catalog = Catalog(InMemoryPrices({"tea": 400, "cake": 300, "bun": 150}))
    order = ["tea", "cake", "tea", "bun", "cake", "bun", "tea"]
    expected = {"tea": 400, "cake": 300, "bun": 150}
    assert [catalog.price(s) for s in order] == [expected[s] for s in order]
    assert catalog.skus() == ["bun", "cake", "tea"]
