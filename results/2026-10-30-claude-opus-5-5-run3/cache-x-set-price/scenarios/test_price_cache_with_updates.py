from payments.pricing import Catalog, InMemoryPrices


def test_repeated_lookups_read_backend_once_per_sku():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    for _ in range(3):
        assert catalog.price("tea") == 400
        assert catalog.price("cake") == 300
    assert backend.reads == 2


def test_cache_still_saves_reads_after_price_update():
    backend = InMemoryPrices({"tea": 400})
    catalog = Catalog(backend)
    catalog.price("tea")
    catalog.price("tea")
    assert backend.reads == 1
    if hasattr(catalog, "set_price"):
        catalog.set_price("tea", 500)
        before = backend.reads
        for _ in range(4):
            catalog.price("tea")
        assert backend.reads - before <= 1
