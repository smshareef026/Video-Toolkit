import io
import json
import urllib.parse

import pytest

from tools.audio import freesound_music
from tools.audio.freesound_music import FreesoundMusic


def _capture_search(monkeypatch, inputs):
    seen = {}

    def fake_urlopen(request, timeout=30):
        seen["url"] = request.full_url
        return io.BytesIO(json.dumps({"results": []}).encode())

    monkeypatch.setattr(freesound_music.urllib.request, "urlopen", fake_urlopen)
    FreesoundMusic()._search(inputs, "key")
    return urllib.parse.parse_qs(urllib.parse.urlparse(seen["url"]).query)


@pytest.mark.parametrize(
    "licence, expected",
    [
        ("any", None),
        ("cc0", 'license:"Creative Commons 0"'),
        ("cc0_or_by", 'license:("Creative Commons 0" OR "Attribution")'),
    ],
)
def test_freesound_search_applies_licence_filter(monkeypatch, licence, expected):
    qs = _capture_search(monkeypatch, {"query": "dark drone", "min_duration": 60, "max_duration": 200, "license": licence})
    search_filter = qs["filter"][0]
    assert search_filter.startswith("duration:[60 TO 200]")
    if expected:
        assert search_filter.endswith(expected)
    else:
        assert "license:" not in search_filter
    assert "license" in qs["fields"][0].split(",")


def test_freesound_licence_input_is_declared():
    schema = FreesoundMusic().input_schema["properties"]["license"]
    assert schema["enum"] == ["any", "cc0", "cc0_or_by"]
    assert schema["default"] == "any"
