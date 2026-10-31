from payments.pricing import Catalog, InMemoryPrices


def _basket_total(catalog, skus):
    if hasattr(catalog, "quote"):
        return catalog.quote(skus)
    return sum(catalog.price(s) for s in skus)


def test_basket_with_repeats_reads_each_sku_once():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    assert _basket_total(catalog, ["tea", "tea", "cake", "tea"]) == 1500
    assert backend.reads == 2


def test_prices_read_before_a_basket_are_not_read_again():
    backend = InMemoryPrices({"tea": 400, "cake": 300})
    catalog = Catalog(backend)
    catalog.price("tea")
    catalog.price("cake")
    assert backend.reads == 2
    assert _basket_total(catalog, ["tea", "cake", "tea"]) == 1100
    assert backend.reads == 2
