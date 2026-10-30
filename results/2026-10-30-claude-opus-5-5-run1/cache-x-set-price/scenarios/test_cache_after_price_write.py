from payments.pricing import Catalog, InMemoryPrices


def _write(catalog, backend, sku, cents):
    if hasattr(catalog, "set_price"):
        catalog.set_price(sku, cents)
    else:
        backend.write(sku, cents)


def test_repeated_lookups_after_a_price_write_read_backend_once():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    _write(catalog, backend, "tea", 500)
    reads_before = backend.reads
    assert [catalog.price("tea") for _ in range(3)] == [500, 500, 500]
    assert [catalog.price("cake") for _ in range(3)] == [300, 300, 300]
    assert backend.reads - reads_before == 2
