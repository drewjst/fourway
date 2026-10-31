from tomlkit import dumps
from tomlkit import parse


def test_subtable_merges_into_last_of_several_aot_elements() -> None:
    content = (
        "[[fruit]]\n"
        'name = "a"\n'
        "\n"
        "[[fruit]]\n"
        'name = "b"\n'
        "\n"
        "[potato]\n"
        "\n"
        "[fruit.extra]\n"
        "x = 1\n"
    )
    doc = parse(content)
    assert len(doc["fruit"]) == 2
    assert doc["fruit"][0]["name"] == "a"
    assert "extra" not in doc["fruit"][0]
    assert doc["fruit"][1]["name"] == "b"
    assert doc["fruit"][1]["extra"]["x"] == 1
    assert doc["potato"] == {}


def test_sub_aot_headers_after_unrelated_table_extend_last_element() -> None:
    content = (
        "[[fruit]]\n"
        'name = "a"\n'
        "\n"
        "[potato]\n"
        "\n"
        "[[fruit.seeds]]\n"
        "size = 1\n"
        "\n"
        "[[fruit.seeds]]\n"
        "size = 2\n"
    )
    doc = parse(content)
    seeds = doc["fruit"][0]["seeds"]
    assert [s["size"] for s in seeds] == [1, 2]
    assert doc["potato"] == {}


def test_out_of_order_aot_subtable_redump_is_stable() -> None:
    content = (
        "[[fruit]]\n"
        'apple.color = "red"\n'
        "\n"
        "[potato]\n"
        "\n"
        "[fruit.apple.texture]\n"
        "smooth = true\n"
    )
    doc = parse(content)
    expected = {
        "fruit": [{"apple": {"color": "red", "texture": {"smooth": True}}}],
        "potato": {},
    }
    assert doc.unwrap() == expected
    rendered = dumps(doc)
    reparsed = parse(rendered)
    assert reparsed.unwrap() == expected
    assert parse(dumps(reparsed)).unwrap() == expected
