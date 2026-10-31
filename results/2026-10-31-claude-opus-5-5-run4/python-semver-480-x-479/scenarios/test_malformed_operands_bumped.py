import operator

import pytest

from semver import Version


def test_bumped_digitless_build_equality_with_malformed_collections_is_false():
    bumped = Version.parse("1.2.3+alpha").bump_build()
    for other in ([], (), {}, {"build": bumped.build}, (1, "x"), ["bogus"]):
        assert (bumped == other) is False
        assert bumped != other
        assert (other == bumped) is False


def test_bumped_digitless_build_ordering_with_malformed_collection_raises_std_typeerror():
    bumped = Version.parse("1.2.3-rc.1+alpha").bump_build().bump_build()
    with pytest.raises(TypeError) as excinfo:
        operator.lt(bumped, {"build": "alpha.1"})
    msg = str(excinfo.value)
    assert "not supported between" in msg
    assert "__init__" not in msg
    with pytest.raises(TypeError) as excinfo2:
        operator.ge(bumped, ["a"])
    assert "not supported between" in str(excinfo2.value)
