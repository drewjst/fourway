import importlib

import tomlkit


def test_wrap_method_no_longer_exported() -> None:
    types_mod = importlib.import_module("tomlkit._types")
    assert "wrap_method" not in types_mod.__all__
    assert not hasattr(types_mod, "wrap_method")


def test_items_still_work_without_wrap_method() -> None:
    items_mod = importlib.import_module("tomlkit.items")
    i = items_mod.item(34)
    i += 1
    assert i.as_string() == "35"
    s = tomlkit.string("a\nb", multiline=True)
    assert str(s) == "a\nb"
