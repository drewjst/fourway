from payments.pricing import Catalog, InMemoryPrices


def test_lookups_match_backend_values():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    for _ in range(3):
        assert catalog.price("tea") == 400
        assert catalog.price("cake") == 300
    assert catalog.skus() == ["cake", "tea"]
    assert 2 <= backend.reads <= 6
