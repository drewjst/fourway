import tomlkit


def test_package_version_is_0_15_2() -> None:
    assert tomlkit.__version__ == "0.15.2"
