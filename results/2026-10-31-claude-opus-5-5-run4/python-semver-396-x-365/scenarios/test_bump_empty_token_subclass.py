from semver import Version


class VPrefix(Version):
    @classmethod
    def parse(cls, version, optional_minor_and_patch=False):
        if not version or version[0] not in ('v', 'V'):
            raise ValueError('must start with v')
        return super().parse(version[1:], optional_minor_and_patch)

    def __str__(self):
        return 'v' + super().__str__()


def test_empty_token_prerelease_on_parsed_subclass():
    v = VPrefix.parse('v3.4.5')
    assert type(v) is VPrefix
    bumped = v.bump_prerelease('')
    assert type(bumped) is VPrefix
    assert bumped.prerelease == '1'
    assert str(bumped) == 'v3.4.5-1'
    assert v.bump_prerelease(None).prerelease == 'rc.1'


def test_empty_token_build_on_parsed_subclass():
    v = VPrefix.parse('v3.4.5-rc.1')
    bumped = v.bump_build('')
    assert type(bumped) is VPrefix
    assert bumped.build == '1'
    assert bumped.prerelease == 'rc.1'
    assert str(bumped) == 'v3.4.5-rc.1+1'
    assert v.bump_build(None).build == 'build.1'
    again = bumped.bump_build('')
    assert again.build == '2'
