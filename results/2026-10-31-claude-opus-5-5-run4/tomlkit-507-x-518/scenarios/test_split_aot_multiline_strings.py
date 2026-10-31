from tomlkit import parse


CONTENT = (
    "[hooks]\n"
    "\n"
    "[[hooks.Stop]]\n"
    'command = """\n'
    "line one\n"
    "\tline two\n"
    '"""\n'
    "\n"
    "[unrelated]\n"
    "x = 1\n"
    "\n"
    "[[hooks.Stop]]\n"
    "command = '''a\tb\n"
    "c \"quoted\" 'single' d'''\n"
    "\n"
    "[hooks.state]\n"
    "y = 2\n"
)


def test_split_aot_with_multiline_values_merges_and_round_trips() -> None:
    doc = parse(CONTENT)
    assert doc.as_string() == CONTENT

    hooks = doc["hooks"]
    assert list(hooks.keys()) == ["Stop", "state"]
    stop = hooks["Stop"]
    assert len(stop) == 2
    assert stop[0]["command"] == "line one\n\tline two\n"
    assert stop[1]["command"] == "a\tb\nc \"quoted\" 'single' d"
    assert hooks["state"]["y"] == 2

    assert doc.unwrap() == {
        "hooks": {
            "Stop": [
                {"command": "line one\n\tline two\n"},
                {"command": "a\tb\nc \"quoted\" 'single' d"},
            ],
            "state": {"y": 2},
        },
        "unrelated": {"x": 1},
    }


CONTENT_CRLF = (
    "[hooks]\n"
    "\n"
    "[[hooks.Stop]]\n"
    'script = """first\r\nsecond\r\n"""\n'
    "\n"
    "[other]\n"
    "z = 0\n"
    "\n"
    "[[hooks.Stop]]\n"
    'script = """fold \\\n    ed\\tx ""\\" end"""\n'
    "\n"
    "[hooks.state]\n"
    "y = 2\n"
)


def test_split_aot_multiline_crlf_escapes_and_write_through() -> None:
    doc = parse(CONTENT_CRLF)
    assert doc.as_string() == CONTENT_CRLF

    stop = doc["hooks"]["Stop"]
    assert len(stop) == 2
    assert stop[0]["script"] == "first\r\nsecond\r\n"
    assert stop[1]["script"] == 'fold ed\tx """ end'

    stop[0]["script"] = "patched"
    rendered = doc.as_string()
    assert 'script = "patched"' in rendered
    # the other fragment's multiline string is rendered untouched
    assert 'script = """fold \\\n    ed\\tx ""\\" end"""' in rendered
    assert doc["hooks"]["Stop"][0]["script"] == "patched"
    assert doc["hooks"]["Stop"][1]["script"] == 'fold ed\tx """ end'

    reparsed = parse(rendered)
    assert reparsed["hooks"]["Stop"][0]["script"] == "patched"
    assert reparsed["hooks"]["Stop"][1]["script"] == 'fold ed\tx """ end'
