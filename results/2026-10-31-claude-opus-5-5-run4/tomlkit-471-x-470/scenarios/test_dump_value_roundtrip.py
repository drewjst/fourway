import tomlkit


TEXT = (
    'zeta = """\nfirst\nsecond"""\n'
    "alpha = '''raw\nlines'''\n"
    'mid = "plain"\n'
)


def test_plain_dump_roundtrips_exactly() -> None:
    doc = tomlkit.loads(TEXT)
    assert tomlkit.dumps(doc) == TEXT
    assert tomlkit.dumps(doc, sort_keys=False) == TEXT


def test_sorted_dump_preserves_values() -> None:
    doc = tomlkit.loads(TEXT)
    expected = {"zeta": "first\nsecond", "alpha": "raw\nlines", "mid": "plain"}
    assert doc == expected
    out = tomlkit.dumps(doc, sort_keys=True)
    assert tomlkit.loads(out) == expected
