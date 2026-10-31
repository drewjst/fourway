from payments.pricing import Catalog, InMemoryPrices

PRICES = {"tea": 400, "cake": 300, "scone": 250}


def _basket_total(catalog, skus):
    if hasattr(catalog, "quote"):
        return catalog.quote(skus)
    return sum(catalog.price(s) for s in skus)


def test_basket_total_matches_sum_of_prices():
    catalog = Catalog(InMemoryPrices(PRICES))
    basket = ["scone", "tea", "scone", "cake", "scone"]
    expected = sum(PRICES[s] for s in basket)
    assert _basket_total(catalog, basket) == expected
    assert sum(catalog.price(s) for s in basket) == expected


def test_prices_match_backend_and_skus_unchanged():
    catalog = Catalog(InMemoryPrices(PRICES))
    for sku in ["tea", "cake", "tea", "scone", "cake"]:
        assert catalog.price(sku) == PRICES[sku]
    assert catalog.skus() == ["cake", "scone", "tea"]
