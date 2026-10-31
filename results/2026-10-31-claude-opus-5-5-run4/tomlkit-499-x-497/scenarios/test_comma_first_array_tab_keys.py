import tomlkit


def test_append_comma_first_array_under_tab_separated_keys() -> None:
    content = (
        "[\ttbl\t]\n"
        "arr\t=\t[\n"
        "      1 # one\n"
        "     ,2\n"
        "    ]\n"
    )
    doc = tomlkit.parse(content)
    assert doc.as_string() == content
    doc["tbl"]["arr"].append(99)

    rendered = doc.as_string()
    reparsed = tomlkit.parse(rendered)
    assert reparsed["tbl"]["arr"] == [1, 2, 99]
    assert reparsed.as_string() == rendered
    assert ",\n     ," not in rendered


def test_insert_middle_comma_first_array_under_dotted_tab_key() -> None:
    content = (
        "x.y\t= [\n"
        "      1 # one\n"
        "     ,2\n"
        "    ]\n"
    )
    doc = tomlkit.parse(content)
    assert doc.as_string() == content
    doc["x"]["y"].insert(1, 99)

    rendered = doc.as_string()
    reparsed = tomlkit.parse(rendered)
    assert reparsed["x"]["y"] == [1, 99, 2]
    assert reparsed.as_string() == rendered
