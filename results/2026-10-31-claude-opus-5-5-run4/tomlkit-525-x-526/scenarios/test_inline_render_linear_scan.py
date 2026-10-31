import tomlkit
from tomlkit import parse


class _SliceCountingList(list):
    def __init__(self, it, counter):
        super().__init__(it)
        self.counter = counter

    def __getitem__(self, key):
        if isinstance(key, slice):
            self.counter[0] += 1
        return super().__getitem__(key)


def _instrument(inline):
    counter = [0]
    inline.value._body = _SliceCountingList(inline.value._body, counter)
    return counter


def test_inline_render_without_tail_rescans_after_dotted_replacement():
    n = 60
    pairs = ", ".join(f"k{i} = {i}" for i in range(n))
    src = "c.d = {" + pairs + "}\na.b = 1\n"
    doc = parse(src)
    # replace the dotted key with a real table (path touched by change B)
    doc["a"] = {"x": 9}
    inline = doc["c"]["d"]
    del inline["k10"]
    del inline["k59"]
    counter = _instrument(inline)

    out = doc.as_string()

    assert counter[0] == 0
    expected = {f"k{i}": i for i in range(n) if i not in (10, 59)}
    reparsed = parse(out)
    assert reparsed["c"]["d"] == expected
    assert reparsed.as_string() == out
    assert ",," not in out and ", ," not in out


def test_large_inline_table_render_is_single_pass():
    n = 80
    pairs = ", ".join(f"k{i} = {i}" for i in range(n))
    doc = parse("t = {" + pairs + "}\n")
    t = doc["t"]
    for i in (0, 40, 79):
        del t[f"k{i}"]
    counter = _instrument(t)

    out = doc.as_string()

    assert counter[0] == 0
    expected = {f"k{i}": i for i in range(n) if i not in (0, 40, 79)}
    assert parse(out)["t"] == expected
    assert parse(out).as_string() == out
