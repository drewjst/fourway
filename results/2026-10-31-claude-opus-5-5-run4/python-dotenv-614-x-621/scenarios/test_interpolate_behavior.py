import io
import os
from unittest import mock

from dotenv import dotenv_values, load_dotenv


def test_dotenv_values_interpolate_flag():
    with mock.patch.dict(os.environ, {"B_SCEN": "c"}, clear=True):
        raw = dotenv_values(stream=io.StringIO("A_SCEN=${B_SCEN}"), interpolate=False)
        expanded = dotenv_values(stream=io.StringIO("A_SCEN=${B_SCEN}"), interpolate=True)
    assert raw == {"A_SCEN": "${B_SCEN}"}
    assert expanded == {"A_SCEN": "c"}


def test_load_dotenv_interpolate_false_keeps_raw():
    with mock.patch.dict(os.environ, {"B_SCEN": "c"}, clear=True):
        ok = load_dotenv(stream=io.StringIO("A_SCEN=${B_SCEN}"), interpolate=False)
        assert ok is True
        assert os.environ["A_SCEN"] == "${B_SCEN}"
