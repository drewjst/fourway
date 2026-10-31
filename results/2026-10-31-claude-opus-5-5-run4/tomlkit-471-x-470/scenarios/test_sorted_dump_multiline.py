import tomlkit


def test_sorted_dump_of_parsed_doc_with_multiline_basic_string() -> None:
    text = 'zzz = """\nline1\nline2"""\naaa = 1\n'
    doc = tomlkit.loads(text)
    out = tomlkit.dumps(doc, sort_keys=True)
    assert out == 'aaa = 1\nzzz = """\nline1\nline2"""\n'
    assert tomlkit.loads(out) == {"aaa": 1, "zzz": "line1\nline2"}


def test_sorted_dump_of_parsed_doc_with_multiline_literal_string() -> None:
    text = "c = '''x\ny'''\nb = \"two\"\na = 1\n"
    doc = tomlkit.loads(text)
    out = tomlkit.dumps(doc, sort_keys=True)
    assert out == "a = 1\nb = \"two\"\nc = '''x\ny'''\n"
    assert tomlkit.loads(out) == {"a": 1, "b": "two", "c": "x\ny"}
