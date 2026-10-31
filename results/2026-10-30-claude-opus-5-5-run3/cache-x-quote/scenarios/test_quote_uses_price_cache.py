from payments.pricing import Catalog, InMemoryPrices


def _basket_total(catalog, skus):
    quote = getattr(catalog, "quote", None)
    if quote is not None:
        return quote(skus)
    return sum(catalog.price(sku) for sku in skus)


def test_basket_with_repeated_sku_reads_backend_once_per_distinct_sku():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    assert _basket_total(catalog, ["tea", "tea", "cake"]) == 1100
    assert backend.reads == 2


def test_repeated_baskets_do_not_reread_backend():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    _basket_total(catalog, ["tea", "cake"])
    assert _basket_total(catalog, ["cake", "tea", "tea"]) == 1100
    assert backend.reads == 2
