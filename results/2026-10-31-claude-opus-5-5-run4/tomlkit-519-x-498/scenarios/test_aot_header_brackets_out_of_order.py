import pytest

from tomlkit import parse
from tomlkit.exceptions import UnexpectedCharError
from tomlkit.exceptions import UnexpectedEofError


def test_malformed_sub_aot_header_after_unrelated_table_is_rejected() -> None:
    content = (
        "[[fruit]]\n"
        'name = "a"\n'
        "\n"
        "[potato]\n"
        "\n"
        "[[fruit.seeds]x\n"
        "size = 1\n"
    )
    with pytest.raises(UnexpectedCharError):
        parse(content)


def test_sub_aot_header_hitting_eof_after_unrelated_table_is_rejected() -> None:
    content = (
        "[[fruit]]\n"
        'name = "a"\n'
        "\n"
        "[potato]\n"
        "\n"
        "[[fruit.seeds]"
    )
    with pytest.raises(UnexpectedEofError):
        parse(content)
