"""Wikimedia Commons stock media adapter.

Provides image and video search over Wikimedia Commons using the
MediaWiki API. Commons is a uniquely useful documentary source because
it mixes public-domain historical imagery, recent CC-licensed videos,
and educational media under one searchable catalogue.
"""
from __future__ import annotations

import html
import os
import re
import time
import warnings
from pathlib import Path
from typing import Any

from .base import Candidate, SearchFilters


_API_URL = "https://commons.wikimedia.org/w/api.php"
_USER_AGENT = "OpenMontageBot/0.2 (https://github.com/calesthio/OpenMontage)"
# Commons rate-limits by client identity
# (https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits). A User-Agent
# without a contact counts as "IP only" (10 req/min, shared by everyone on
# a cloud IP); adding WIKIMEDIA_CONTACT moves us to the identified tier, and
# an optional WIKIMEDIA_ACCESS_TOKEN (OAuth 2.0 owner-only) goes higher.
_MIN_INTERVAL = 0.35  # seconds between requests, under the identified tier
_MAX_429_RETRIES = 4
# Images are always fetched as a standard-step Commons thumbnail, never the
# original: originals of museum scans are often 100+ MB TIFFs, and
# upload.wikimedia.org rate-limits original downloads hard (429 with a
# 10-minute Retry-After) while serving thumbnails freely. 1920 px is plenty
# for a 1080p crop.
_IMAGE_DOWNLOAD_WIDTH = 1920
_THUMB_STEPS = (1920, 1280, 960, 500, 330, 250)
_MAX_RETRY_AFTER = 60  # a longer Retry-After fails fast instead of stalling the corpus
_THUMB_WIDTH_RE = re.compile(r"(/(?:[a-z]+-)?(?:page\d+-)?)\d+px-(?=[^/]*$)")
_last_request = [0.0]
_token_rejected = [False]
_COMMONS_LICENSE = "Wikimedia Commons (verify per-file license)"
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# Commons extmetadata can embed <style>/<script> blocks (e.g. the file-information
# table CSS); drop them whole so their contents never reach source_tags.
_HTML_BLOCK_RE = re.compile(r"<(style|script)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)

# Stop words stripped from multi-term queries before the cascade runs.
# Commons' CirrusSearch defaults to AND semantics across multi-word
# queries, so each extra common token shrinks the result set fast.
_STOP_WORDS = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "into",
    "its", "their", "about", "over", "under", "while", "during",
    "your", "you", "our", "are", "was", "were", "have", "has",
})

# Tokens that refer to other stock archives — useless on Commons and
# will poison the cascade if they end up in top2_or because Commons
# file names don't reference Prelinger or other archives. Keeps the
# cascade parallel to ``archive_org.py``'s own source-hint stripping.
_SOURCE_HINT_TOKENS = frozenset({
    "prelinger", "archive", "archives", "stock", "footage",
})


def _user_agent() -> str:
    contact = os.environ.get("WIKIMEDIA_CONTACT", "").strip()
    if not contact:
        return _USER_AGENT
    return _USER_AGENT.replace(")", f"; {contact})", 1)


def _headers(url: str) -> dict[str, str]:
    headers = {"User-Agent": _user_agent()}
    token = os.environ.get("WIKIMEDIA_ACCESS_TOKEN", "").strip()
    if token and not _token_rejected[0] and url.startswith(_API_URL):
        headers["Authorization"] = f"Bearer {token}"  # API only, never the upload CDN
    return headers


def _get(url: str, **kwargs):
    """Paced GET that honours Retry-After on 429. Other errors propagate."""
    import requests  # lazy

    resp = None
    for _ in range(_MAX_429_RETRIES + 1):
        time.sleep(max(0.0, _last_request[0] + _MIN_INTERVAL - time.time()))
        _last_request[0] = time.time()
        headers = _headers(url)
        resp = requests.get(url, headers=headers, **kwargs)
        status = getattr(resp, "status_code", 200)
        if status == 401 and "Authorization" in headers:
            # A client secret pasted in place of the owner-only access token
            # (a JWT) makes every API call fail. Drop it and stay identified.
            _token_rejected[0] = True
            warnings.warn("WIKIMEDIA_ACCESS_TOKEN was rejected by Commons (401); "
                          "continuing without it. It must be an OAuth 2.0 owner-only access token.")
            continue
        if status != 429:
            return resp
        resp_headers = getattr(resp, "headers", None) or {}
        try:
            wait = float(resp_headers.get("retry-after") or 15)
        except (TypeError, ValueError):
            wait = 15.0
        if wait > _MAX_RETRY_AFTER:
            return resp  # caller's raise_for_status() fails this item; move on
        if kwargs.get("stream"):
            resp.close()
        time.sleep(wait + 1)
    return resp


def _large_thumb_url(thumb_url: str, width: int) -> str:
    """Rewrite a Commons thumb URL (``.../640px-Name.jpg``) to another width."""
    if not thumb_url or "/thumb/" not in thumb_url:
        return ""
    new, n = _THUMB_WIDTH_RE.subn(lambda m: f"{m.group(1)}{width}px-", thumb_url, count=1)
    return new if n else ""


class WikimediaSource:
    """Adapter for Wikimedia Commons media search."""

    name = "wikimedia"
    display_name = "Wikimedia Commons"
    provider = "wikimedia"
    priority = 25
    install_instructions = (
        "No setup required. Wikimedia Commons media search works without API keys. "
        "Set WIKIMEDIA_CONTACT (an email or user page) to leave the shared "
        "10 req/min IP-only rate-limit tier."
    )
    supports = {"video": True, "image": True}

    def is_available(self) -> bool:
        return True

    def search(self, query: str, filters: SearchFilters) -> list[Candidate]:
        """Search Commons via CirrusSearch, cascading from precise to broad.

        Commons' search defaults to AND across multi-word queries, so
        our first diagnostic pass against the P2 query set returned 0
        video results for 10/10 queries — every query was too specific
        to intersect Commons' relatively sparse video holdings.

        The cascade (see ``_build_search_queries``) tries strict first,
        then narrows to 2 distinctive tokens, then to 1 — returning the
        first non-empty video result set.
        """
        for _label, search_text in _build_search_queries(query, filters.kind):
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": search_text,
                "gsrnamespace": 6,
                "gsrlimit": max(1, min(filters.per_page, 50)),
                "gsroffset": max(0, (max(filters.page, 1) - 1) * max(1, min(filters.per_page, 50))),
                "prop": "imageinfo|info",
                "iiprop": "url|size|mime|extmetadata|mediatype",
                "iiurlwidth": 640,
                "inprop": "url",
            }

            try:
                r = _get(_API_URL, params=params, timeout=30)
                r.raise_for_status()
                data = r.json()
            except Exception:
                continue
            pages = list(((data.get("query") or {}).get("pages") or {}).values())
            if not pages:
                continue
            pages.sort(key=lambda page: int(page.get("index", 0)))

            out: list[Candidate] = []
            for page in pages:
                cand = _page_to_candidate(page, filters)
                if cand is not None:
                    out.append(cand)
            if out:
                return out

        return []

    def download(self, candidate: Candidate, out_path: Path) -> Path:
        if not candidate.download_url:
            raise ValueError(f"Candidate {candidate.clip_id} has no download_url")

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        urls = [candidate.download_url]
        original = (candidate.extra or {}).get("original_url")
        if original and original != candidate.download_url:
            urls.append(original)  # the large thumb 404s on some odd formats
        for i, url in enumerate(urls):
            try:
                with _get(url, stream=True, timeout=300) as r:
                    r.raise_for_status()
                    with open(out_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1 << 16):
                            if chunk:
                                f.write(chunk)
                return out_path
            except Exception:
                if i == len(urls) - 1:
                    raise
        return out_path


def _build_search_queries(query: str, kind: str) -> list[tuple[str, str]]:
    """Return a cascade of search queries to try in preference order.

    Commons' CirrusSearch defaults to AND semantics for multi-word
    queries, so a 4-word descriptive query like
    "1950s family watching television" intersects to 0 video hits.
    We walk from specific to loose:

    1. **full** — ``filetype:video <full query>``. Works when Commons
       has a file whose name/description contains all the tokens
       (e.g. "atomic bomb test civil defense" finds
       "Operation Cue 1955").
    2. **top2_or** — ``filetype:video <token1> <token2>`` using the
       two longest non-year tokens. AND-combines at the query level
       but with only 2 terms, it's loose enough to hit most
       documentary queries.
    3. **single_best** — ``filetype:video <longest_token>``.
       Last-resort single-token search. Noisy but non-empty.

    Year tokens are excluded from the distinctive-token picks — they
    rarely correlate with file name matches on Commons.
    """
    user_query = query.strip()
    kind_l = (kind or "video").lower()

    prefix = "filetype:video" if kind_l == "video" else (
        "filetype:image" if kind_l == "image" else ""
    )

    def _wrap(text: str) -> str:
        return f"{prefix} {text}".strip() if prefix else text

    if not user_query:
        return [("default", _wrap(""))]

    tokens = [
        t for t in user_query.split()
        if len(t) >= 3
        and t.lower() not in _STOP_WORDS
        and t.lower() not in _SOURCE_HINT_TOKENS
    ]
    non_year = [t for t in tokens if not _looks_like_year(t)]

    queries: list[tuple[str, str]] = [("full", _wrap(user_query))]

    if len(non_year) >= 2:
        top2 = sorted(non_year, key=lambda t: -len(t))[:2]
        queries.append(("top2_or", _wrap(f"{top2[0]} {top2[1]}")))

    if non_year:
        best = max(non_year, key=len)
        queries.append(("single_best", _wrap(best)))

    return queries


def _looks_like_year(token: str) -> bool:
    bare = token.rstrip("s")
    return bare.isdigit() and len(bare) == 4


def _page_to_candidate(page: dict[str, Any], filters: SearchFilters) -> Candidate | None:
    infos = page.get("imageinfo") or []
    if not infos:
        return None
    info = infos[0]
    mime = (info.get("mime") or "").lower()
    kind = _kind_from_mime(mime, page.get("title", ""))

    requested_kind = (filters.kind or "video").lower()
    if requested_kind == "video" and kind != "video":
        return None
    if requested_kind == "image" and kind != "image":
        return None

    width = int(info.get("width") or 0)
    height = int(info.get("height") or 0)
    duration = float(info.get("duration") or 0.0)

    if filters.min_width is not None and width and width < filters.min_width:
        return None
    if filters.min_duration is not None and duration and duration < filters.min_duration:
        return None
    if filters.max_duration is not None and duration and duration > filters.max_duration:
        return None
    if filters.orientation and not _matches_orientation(filters.orientation, width, height):
        return None

    meta = info.get("extmetadata") or {}
    object_name = _meta_value(meta, "ObjectName")
    description = _meta_value(meta, "ImageDescription")
    categories = _meta_value(meta, "Categories")
    creator = _meta_value(meta, "Artist")
    license_name = _meta_value(meta, "LicenseShortName")
    usage_terms = _meta_value(meta, "UsageTerms")
    source_tags = " ".join(part for part in (object_name, description, categories) if part).strip()
    if len(source_tags) > 500:
        source_tags = source_tags[:500]

    title = page.get("title", "")
    page_id = str(page.get("pageid") or title.replace("File:", "", 1))
    source_url = info.get("descriptionurl") or page.get("canonicalurl") or ""
    original_url = info.get("url", "") or ""
    download_url = original_url
    if kind == "image":
        # Largest standard step strictly narrower than the original (Commons
        # won't upscale a thumb); tiny images fall back to the original.
        step = next((w for w in _THUMB_STEPS if w < width), None) if width else _IMAGE_DOWNLOAD_WIDTH
        if step:
            download_url = _large_thumb_url(info.get("thumburl", ""), min(step, _IMAGE_DOWNLOAD_WIDTH)) or original_url

    return Candidate(
        source=WikimediaSource.name,
        source_id=page_id,
        source_url=source_url,
        download_url=download_url,
        kind=kind,
        width=width,
        height=height,
        duration=duration,
        creator=creator,
        license=license_name or usage_terms or _COMMONS_LICENSE,
        source_tags=source_tags,
        thumbnail_url=info.get("thumburl", "") or info.get("url", "") or "",
        extra={
            "mime": mime,
            "title": title,
            "original_url": original_url,
            "mediatype": info.get("mediatype"),
            "descriptionshorturl": info.get("descriptionshorturl"),
        },
    )


def _kind_from_mime(mime: str, title: str) -> str:
    if mime.startswith("video/") or title.lower().endswith((".webm", ".ogv", ".ogg")):
        return "video"
    return "image"


def _matches_orientation(orientation: str, width: int, height: int) -> bool:
    if not width or not height:
        return True
    if orientation == "landscape":
        return width >= height
    if orientation == "portrait":
        return height > width
    if orientation == "square":
        return width == height
    return True


def _meta_value(meta: dict[str, Any], key: str) -> str:
    raw = ((meta.get(key) or {}).get("value")) or ""
    if not raw:
        return ""
    text = _HTML_BLOCK_RE.sub(" ", str(raw))
    text = html.unescape(text)
    text = _HTML_BLOCK_RE.sub(" ", text)
    text = _HTML_TAG_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
