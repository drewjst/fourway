from semver import Version


def _install_counter(monkeypatch):
    calls = []
    orig = Version._increment_string

    def counting(string):
        calls.append(string)
        return orig(string)

    monkeypatch.setattr(Version, "_increment_string", staticmethod(counting))
    return calls


def test_bump_build_increments_existing_build_once(monkeypatch):
    v = Version.parse("3.4.5-rc.1+build.9")
    calls = _install_counter(monkeypatch)
    result = v.bump_build()
    assert str(result) == "3.4.5-rc.1+build.10"
    assert calls == ["build.9"]


def test_bump_build_after_prerelease_bump_increments_once(monkeypatch):
    pre = Version.parse("3.4.5").bump_prerelease("dev")
    assert pre.prerelease == "dev.1"
    calls = _install_counter(monkeypatch)
    result = pre.bump_build(None)
    assert str(result) == "3.4.5-dev.1+build.1"
    assert calls == ["build.0"]
