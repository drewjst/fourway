from payments.pricing import Catalog, InMemoryPrices


def test_interleaved_lookups_read_each_sku_once():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    seen = [catalog.price(s) for s in ["tea", "cake", "tea", "tea", "cake"]]
    assert seen == [400, 300, 400, 400, 300]
    assert backend.reads == 2
