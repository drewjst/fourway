from payments.pricing import Catalog, InMemoryPrices


def test_repeated_lookups_read_the_backend_once():
    backend = InMemoryPrices({"tea": 400})
    catalog = Catalog(backend)
    assert [catalog.price("tea"), catalog.price("tea")] == [400, 400]
    assert backend.reads == 1
