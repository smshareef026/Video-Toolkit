"""Search and download public-domain / CC artwork from Wikimedia Commons.

Commons rate-limits shared cloud IPs hard (HTTP 429 with retry-after); this
client sleeps and retries, so a batch of ~15 images can take 10-20 minutes.
Run downloads in the background.

  python wikimedia.py search "Roses of Heliogabalus" "Gerome lion"
  python wikimedia.py download <project_dir> images.json
      images.json = {"key": "File:Exact Commons title.jpg", ...}
      -> assets/images/<key>.jpg + artifacts/image_credits.json (merged, per-file)
"""
import hashlib, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

UA = {"User-Agent": "OpenMontageBot/1.0 (https://github.com/smshareef026/video-toolkit) python-urllib"}


def get(url, tries=10):
    for _ in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("retry-after") or 15) + 2)
                continue
            raise
    raise SystemExit("still rate limited: " + url)


def api(tries=10, **p):
    p["format"] = "json"
    return json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p), tries))


def direct(title, width):
    """Fetch straight from upload.wikimedia.org (by the file name's md5 path) when the API keeps
    answering 429. Returns (bytes, page_url); licence/artist must then be filled in from `search`."""
    name = title.split(":", 1)[1].replace(" ", "_")
    h = hashlib.md5(name.encode()).hexdigest()
    q = urllib.parse.quote(name)
    base = f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{q}"
    thumb = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{width}px-{q}"
    try:
        data = get(thumb, 3)  # fails (4xx) when the original is narrower than `width`
    except urllib.error.HTTPError:
        data = get(base, 3)
    return data, "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))


def search(queries):
    for q in queries:
        d = api(action="query", generator="search", gsrsearch=q, gsrnamespace=6, gsrlimit=6,
                prop="imageinfo", iiprop="size|extmetadata")
        print("##", q, flush=True)
        for p in (d.get("query", {}).get("pages", {}) or {}).values():
            ii = p["imageinfo"][0]
            lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value")
            print(f"  {p['title']} | {ii['width']}x{ii['height']} | {lic}", flush=True)
        time.sleep(3)


def download(project, mapping_file, width=1920):  # 1920 = a standard Commons thumb step
    project = Path(project)
    out = project / "assets" / "images"
    out.mkdir(parents=True, exist_ok=True)
    cred_path = project / "artifacts" / "image_credits.json"
    credits = json.loads(cred_path.read_text()) if cred_path.exists() else {}
    for key, title in json.loads(Path(mapping_file).read_text()).items():
        dest = out / f"{key}.jpg"
        if dest.exists() and dest.stat().st_size > 0 and key in credits:
            continue  # resumable
        try:
            d = api(tries=2, action="query", titles=title, prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=width)
        except SystemExit:  # API still rate-limited: go straight to the upload server
            data, page = direct(title, width)
            dest.write_bytes(data)
            credits[key] = {"title": title, "page": page, "license": None, "artist": None}
        else:
            ii = list(d["query"]["pages"].values())[0]["imageinfo"][0]
            m = ii["extmetadata"]
            time.sleep(2)
            dest.write_bytes(get(ii.get("thumburl") or ii["url"]))
            credits[key] = {
                "title": title, "page": ii["descriptionurl"],
                "license": m.get("LicenseShortName", {}).get("value"),
                "artist": re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "")).strip(),
            }
        cred_path.write_text(json.dumps(credits, indent=1, ensure_ascii=False))  # save after each file
        print(key, credits[key]["license"], flush=True)
        time.sleep(3)


if __name__ == "__main__":
    if sys.argv[1] == "search":
        search(sys.argv[2:])
    else:
        download(sys.argv[2], sys.argv[3])
