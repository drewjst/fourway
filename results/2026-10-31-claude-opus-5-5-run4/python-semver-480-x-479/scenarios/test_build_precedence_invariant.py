from semver import Version


def test_bump_build_preserves_precedence_against_collection_forms():
    for s in ("1.2.3+alpha", "1.2.3-rc.1+exp.sha", "1.2.3+build.9", "1.2.3"):
        v = Version.parse(s)
        bumped = v.bump_build()
        assert bumped == v
        assert bumped == v.to_tuple()
        assert bumped == list(v.to_tuple())
        assert bumped == v.to_dict()
        assert v.to_tuple() == bumped
        assert not (bumped < v.to_dict())
        assert not (bumped > list(v))
        assert hash(bumped) == hash(v)


def test_bump_build_does_not_mutate_original_and_orders_consistently():
    v = Version.parse("2.0.0-beta+alpha")
    bumped = v.bump_build()
    assert v.build == "alpha"
    assert str(v) == "2.0.0-beta+alpha"
    assert bumped < (2, 0, 0)
    assert bumped > (1, 9, 9)
    assert bumped <= {"major": 2, "minor": 0, "patch": 0, "prerelease": "beta"}
    assert bumped >= [2, 0, 0, "beta", "zzz"]
