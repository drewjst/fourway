from tomlkit import dumps, loads, parse


def test_edited_document_with_esc_and_signed_float_round_trips():
    doc = parse('name = "a\\eb"\nx = +2.5\ny = -1.5\n')
    doc["x"] *= 2
    doc["y"] *= -1
    doc["name"] += "\x1bz"
    out = doc.as_string()
    back = parse(out)
    assert back["name"] == "a\x1bb\x1bz"
    assert back["x"] == 5.0
    assert back["y"] == 1.5
    assert "x = +5.0" in out
    assert "y = +1.5" in out
    assert parse(out).as_string() == out


def test_dumped_dict_with_esc_and_floats_round_trips():
    d = {"e\x1bk": "v\x1b", "f": -2.25, "g": 0.0}
    back = loads(dumps(d))
    assert back == d
