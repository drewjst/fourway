from payments.money import format_amount


def test_dollars_have_two_decimals():
    assert format_amount(1250, "USD") == "12.50 USD"


def test_yen_have_no_decimals():
    assert format_amount(1250, "JPY") == "1250 JPY"
