import pytest

from tomlkit import parse
from tomlkit.exceptions import InvalidUnicodeValueError


@pytest.mark.parametrize(
    "content",
    [
        r'"\U0000D800" = 1',
        r'   "\U0000DFFF"   =   1',
        '[tbl]\n' + r'  "\U0000DC00"   = 2' + '\n',
        r'["\U0000D800"]' + '\nx = 1\n',
        r'a."\U0000D800".b = 1',
        'n = 1_000\n' + r'"\U0000DBFF"  = 3' + '\n',
    ],
)
def test_big_u_surrogate_rejected_in_keys(content: str) -> None:
    with pytest.raises(InvalidUnicodeValueError):
        parse(content)


@pytest.mark.parametrize(
    "content",
    [
        r'   a   =   "\U0000D800"   # c',
        r't = { k = "\U0000DC00" }',
        r'arr = [ 1, "\U0000DFFF" ]',
        'm = """\n' + r'\U0000D800' + '"""\n',
        'd = 1979-05-27\n' + r's = "\U0000D800"' + '\n',
        'dt = 1979-05-27 07:32:00Z\n' + r'  s  =  "\U0000DFFF"' + '\n',
    ],
)
def test_big_u_surrogate_rejected_in_values(content: str) -> None:
    with pytest.raises(InvalidUnicodeValueError):
        parse(content)


def test_big_u_surrogate_error_reports_correct_line() -> None:
    content = (
        "a = 1\n"
        "   b   =   2_000   # comment\n"
        "[tbl]\n"
        + r'  key  =  "ok \U0000DC00"'
        + "\n"
    )
    with pytest.raises(InvalidUnicodeValueError) as e:
        parse(content)
    assert e.value.line == 4
