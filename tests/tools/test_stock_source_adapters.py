import sys
import types

import pytest

from tools.video.stock_sources import SearchFilters, all_sources, get_source
from tools.video.stock_sources.unsplash import _build_download_url, _orientation_for_unsplash
from tools.video.stock_sources.wikimedia import (
    _build_search_queries,
    _headers,
    _kind_from_mime,
    _large_thumb_url,
    _meta_value,
    _page_to_candidate,
)


def test_stock_source_autodiscovery_includes_new_sources():
    names = {source.name for source in all_sources()}
    assert "wikimedia" in names
    assert "unsplash" in names


def test_wikimedia_search_query_respects_kind():
    # The cascade's first ("full") query should always carry the
    # filetype filter for video/image kinds. "any" drops the prefix.
    video_cascade = _build_search_queries("rain city", "video")
    assert video_cascade[0][0] == "full"
    assert video_cascade[0][1].startswith("filetype:video")

    image_cascade = _build_search_queries("rain city", "image")
    assert image_cascade[0][0] == "full"
    assert image_cascade[0][1].startswith("filetype:image")

    any_cascade = _build_search_queries("rain city", "any")
    assert any_cascade[0][0] == "full"
    assert any_cascade[0][1] == "rain city"


def test_wikimedia_cascade_falls_back_on_multi_word():
    # Multi-word query should produce a 3-stage cascade: full, top2_or,
    # single_best. Tokens are picked by length, so "television" beats
    # "family" and "watching".
    cascade = _build_search_queries(
        "1950s family watching television", "video"
    )
    labels = [label for label, _ in cascade]
    assert labels == ["full", "top2_or", "single_best"]
    assert cascade[1][1] == "filetype:video television watching"
    assert cascade[2][1] == "filetype:video television"


def test_wikimedia_cascade_strips_source_hints_and_years():
    # "prelinger" is a source hint (redundant on Commons) and "1955" is
    # a year — both are excluded from distinctive-token picks.
    cascade = _build_search_queries(
        "Prelinger 1955 housewife kitchen", "video"
    )
    # Full query keeps the source hint + year (first attempt is strict).
    assert cascade[0][1] == "filetype:video Prelinger 1955 housewife kitchen"
    # Distinctive picks do NOT include prelinger or 1955.
    joined = " ".join(sq for _, sq in cascade[1:])
    assert "housewife" in joined
    assert "kitchen" in joined
    assert "prelinger" not in joined.lower()
    assert "1955" not in joined


def test_wikimedia_kind_and_metadata_helpers():
    assert _kind_from_mime("video/webm", "File:foo.webm") == "video"
    assert _kind_from_mime("image/jpeg", "File:foo.jpg") == "image"
    assert _meta_value({"Artist": {"value": "<a href='/wiki/User:Test'>Test User</a>"}}, "Artist") == "Test User"


def test_wikimedia_user_agent_carries_contact_and_token_only_on_api(monkeypatch):
    monkeypatch.delenv("WIKIMEDIA_CONTACT", raising=False)
    monkeypatch.delenv("WIKIMEDIA_ACCESS_TOKEN", raising=False)
    assert "@" not in _headers("https://commons.wikimedia.org/w/api.php")["User-Agent"]

    monkeypatch.setenv("WIKIMEDIA_CONTACT", "me@example.com")
    monkeypatch.setenv("WIKIMEDIA_ACCESS_TOKEN", "tok")
    api = _headers("https://commons.wikimedia.org/w/api.php")
    assert api["User-Agent"].endswith("; me@example.com)")
    assert api["Authorization"] == "Bearer tok"
    assert "Authorization" not in _headers("https://upload.wikimedia.org/wikipedia/commons/a/ab/X.jpg")


def test_wikimedia_drops_a_rejected_token_and_retries(monkeypatch):
    from tools.video.stock_sources import wikimedia

    class Resp:
        def __init__(self, status):
            self.status_code = status

    sent = []

    def fake_get(url, headers=None, **_kw):
        sent.append("Authorization" in headers)
        return Resp(401 if "Authorization" in headers else 200)

    requests_stub = types.ModuleType("requests")
    requests_stub.get = fake_get
    monkeypatch.setitem(sys.modules, "requests", requests_stub)
    monkeypatch.setattr(wikimedia, "_token_rejected", [False])
    monkeypatch.setattr(wikimedia, "_MIN_INTERVAL", 0.0)
    monkeypatch.setenv("WIKIMEDIA_ACCESS_TOKEN", "not-a-jwt")

    with pytest.warns(UserWarning, match="rejected"):
        assert wikimedia._get(wikimedia._API_URL).status_code == 200
    assert sent == [True, False]


def test_wikimedia_large_images_download_a_standard_thumb():
    base = "https://upload.wikimedia.org/wikipedia/commons"
    assert _large_thumb_url(f"{base}/thumb/a/ab/X.jpg/640px-X.jpg", 1920) == f"{base}/thumb/a/ab/X.jpg/1920px-X.jpg"
    assert (_large_thumb_url(f"{base}/thumb/a/ab/X.tif/lossy-page1-640px-X.tif.jpg", 1920)
            == f"{base}/thumb/a/ab/X.tif/lossy-page1-1920px-X.tif.jpg")
    assert _large_thumb_url(f"{base}/a/ab/X.jpg", 1920) == ""

    def page(width):
        return {"title": "File:X.tif", "pageid": 7, "imageinfo": [{
            "mime": "image/tiff", "width": width, "height": 3000,
            "url": f"{base}/a/ab/X.tif",
            "thumburl": f"{base}/thumb/a/ab/X.tif/lossy-page1-640px-X.tif.jpg",
        }]}

    big = _page_to_candidate(page(6000), SearchFilters(kind="image"))
    assert big.download_url.endswith("lossy-page1-1920px-X.tif.jpg")
    assert big.extra["original_url"] == f"{base}/a/ab/X.tif"
    small = _page_to_candidate(page(1200), SearchFilters(kind="image"))
    assert small.download_url == f"{base}/a/ab/X.tif"


def test_unsplash_helpers_preserve_query_params():
    assert _orientation_for_unsplash("square") == "squarish"
    url = _build_download_url("https://images.unsplash.com/photo-123?ixid=abc", 1920)
    assert "ixid=abc" in url
    assert "w=1920" in url
    assert "fm=jpg" in url


# ---------------------------------------------------------------------
# Transport-error contract (issue #511)
#
# `base.StockSource.search` states the rule: "Network errors should be
# raised — the corpus builder catches and logs per-source so one flaky
# API doesn't poison the whole run." An adapter that swallows the error
# and returns `[]` is indistinguishable from a source that genuinely has
# nothing to offer, so `direct_clip_search` reports `success: True,
# clips_downloaded: 0, errors: []` on a run where every request failed.
#
# The two tests below pin both halves of the contract across *every*
# registered adapter, so a new source cannot quietly reintroduce the bug.
# ---------------------------------------------------------------------

# Adapters that gate on a key before they reach the network. Without
# these the key-gated sources would return early and the test would
# assert nothing.
_SOURCE_CREDENTIALS = {
    "COVERR_API_KEY": "test-coverr",
    "NARA_API_KEY": "test-nara",
    "NASA_API_KEY": "test-nasa",
    "PEXELS_API_KEY": "test-pexels",
    "PIXABAY_API_KEY": "test-pixabay",
    "POND5_API_KEY": "test-pond5",
    "UNSPLASH_ACCESS_KEY": "test-unsplash",
    "VIDEVO_API_KEY": "test-videvo",
}

# Adapters that still swallow transport failures, recorded as known
# defects rather than encoded as expected behavior. `strict=True` means
# the suite fails the moment one of them is fixed and left in this map.
_STILL_SWALLOWS_TRANSPORT_ERRORS = {
    "archive_org": "#511 follow-up: query cascade continues past a failed strategy",
    "wikimedia": "#511 follow-up: query cascade continues past a failed strategy",
    "pond5_pd": "#511 follow-up: API failure falls through to the web fallback",
}


class TransportError(Exception):
    """Distinct failure type so the assertion cannot pass by accident."""


class _EmptyOkResponse:
    """A genuine 200 that simply carries no results."""

    status_code = 200
    text = "<html><body></body></html>"
    content = b""

    def raise_for_status(self):
        return None

    def json(self):
        return {}

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class _EmptySoup:
    """Stand-in for `BeautifulSoup`: parses anything, finds nothing."""

    def __init__(self, *_args, **_kwargs):
        pass

    def select(self, *_args, **_kwargs):
        return []

    def select_one(self, *_args, **_kwargs):
        return None

    def find_all(self, *_args, **_kwargs):
        return []

    def find(self, *_args, **_kwargs):
        return None


def _install_fake_transport(monkeypatch, fake_get):
    """Point every adapter's lazy `import requests` at `fake_get`.

    `bs4` is stubbed alongside it: it is an optional dependency (the
    scraping adapters report `is_available() is False` without it), and
    they import it at the top of `search()`. Left alone, those adapters
    would fail on the import rather than on the request, and the test
    would pass for the wrong reason wherever bs4 is not installed.
    """
    requests_stub = types.ModuleType("requests")
    requests_stub.get = fake_get
    monkeypatch.setitem(sys.modules, "requests", requests_stub)

    bs4_stub = types.ModuleType("bs4")
    bs4_stub.BeautifulSoup = _EmptySoup
    monkeypatch.setitem(sys.modules, "bs4", bs4_stub)

    for var, value in _SOURCE_CREDENTIALS.items():
        monkeypatch.setenv(var, value)


def _adapter_names():
    return [source.name for source in all_sources()]


def _transport_error_params():
    params = []
    for name in _adapter_names():
        reason = _STILL_SWALLOWS_TRANSPORT_ERRORS.get(name)
        marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
        params.append(pytest.param(name, marks=marks, id=name))
    return params


@pytest.mark.parametrize("source_name", _transport_error_params())
def test_search_propagates_transport_errors(source_name, monkeypatch):
    def boom(*_args, **_kwargs):
        raise TransportError("simulated connection reset")

    _install_fake_transport(monkeypatch, boom)

    with pytest.raises(TransportError):
        get_source(source_name).search(
            "ocean waves", SearchFilters(kind="any", per_page=5)
        )


@pytest.mark.parametrize("source_name", _adapter_names(), ids=_adapter_names())
def test_search_returns_empty_when_the_source_has_no_results(
    source_name, monkeypatch
):
    # The other half of the contract: `[]` still has to mean "nothing
    # matched". A 200 with an empty payload must not raise.
    _install_fake_transport(monkeypatch, lambda *_a, **_k: _EmptyOkResponse())

    assert (
        get_source(source_name).search(
            "ocean waves", SearchFilters(kind="any", per_page=5)
        )
        == []
    )
