from payments.pricing import Catalog, InMemoryPrices


def test_interleaved_lookups_read_each_sku_once():
    backend = InMemoryPrices({"tea": 400, "cake": 300, "bun": 150})
    catalog = Catalog(backend)
    seen = [catalog.price(s) for s in ["tea", "cake", "tea", "bun", "cake", "tea", "bun"]]
    assert seen == [400, 300, 400, 150, 300, 400, 150]
    assert backend.reads == 3
