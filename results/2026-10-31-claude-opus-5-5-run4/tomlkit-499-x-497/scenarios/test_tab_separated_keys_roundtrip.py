import tomlkit


def test_outer_tabs_around_keys_and_plain_array_append() -> None:
    content = "a\t=\t[1, 2]\n[\tsec\t]\nk\t= 1\n"
    doc = tomlkit.parse(content)
    assert doc.as_string() == content
    assert doc["sec"]["k"] == 1

    doc["a"].append(3)
    expected = "a\t=\t[1, 2, 3]\n[\tsec\t]\nk\t= 1\n"
    assert doc.as_string() == expected
    assert tomlkit.parse(expected) == {"a": [1, 2, 3], "sec": {"k": 1}}


def test_quoted_key_with_tab_still_allowed_and_array_editable() -> None:
    content = '"a\tb" = [1]\n'
    doc = tomlkit.parse(content)
    assert doc.as_string() == content
    doc["a\tb"].append(2)
    rendered = doc.as_string()
    reparsed = tomlkit.parse(rendered)
    assert reparsed == {"a\tb": [1, 2]}
    assert reparsed.as_string() == rendered
