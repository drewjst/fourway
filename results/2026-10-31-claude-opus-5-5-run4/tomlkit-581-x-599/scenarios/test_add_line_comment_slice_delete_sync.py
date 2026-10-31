from tomlkit import api


def _commented_array():
    a = api.array()
    a.add_line(1, 2, comment="c")
    return a


def test_negative_stop_slice_delete_updates_render_of_commented_array() -> None:
    a = _commented_array()
    del a[:-1]
    assert list(a) == [2]
    s = a.as_string()
    assert "1" not in s
    assert "2" in s
    assert "# c" in s


def test_noop_slice_delete_keeps_render_of_commented_array() -> None:
    a = _commented_array()
    del a[:0]
    assert list(a) == [1, 2]
    s = a.as_string()
    assert "1" in s
    assert "2" in s
    assert "# c" in s
