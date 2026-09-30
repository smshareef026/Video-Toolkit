"""Turn the clips picked from the documentary-montage corpus into build_short.py inputs.

  python from_corpus.py projects/<id> picks.json

picks.json maps each shot key to a corpus clip_id (from clip_search rank_for_slot):
  {"roses": "wikimedia_12345",
   "legion": {"clip": "archive_org_RomanLegion1959", "in": 12.5, "slot": "slot_04"}}
"in" is the in-point (seconds) for a video clip; "slot" defaults to the key.

Writes, per key:
  image -> assets/images/<key>.jpg            (re-encoded, whatever the source format)
  video -> assets/video/<key>.mp4             (H.264, no audio; build_short trims from "in")
  both  -> assets/previews/<key>.jpg          (800px wide, the crop-coordinate space)
plus artifacts/image_credits.json (credits for UPLOAD.md) and
artifacts/asset_manifest.json (the documentary-montage `assets` stage artifact; narration,
music and SFX entries already in it are kept).
"""
import json
import subprocess
import sys
from pathlib import Path


def sh(*cmd):
    subprocess.run(list(map(str, cmd)), check=True)


def load_corpus(corpus_dir):
    rows = {}
    with open(corpus_dir / "index.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                rows[row["clip_id"]] = row
    return rows


def main(project, picks_file):
    proj = Path(project)
    corpus_dir = proj / "corpus"
    rows = load_corpus(corpus_dir)
    picks = json.loads(Path(picks_file).read_text())
    for sub in ("assets/images", "assets/video", "assets/previews", "artifacts"):
        (proj / sub).mkdir(parents=True, exist_ok=True)

    cred_path = proj / "artifacts" / "image_credits.json"
    man_path = proj / "artifacts" / "asset_manifest.json"
    credits = json.loads(cred_path.read_text()) if cred_path.exists() else {}
    manifest = json.loads(man_path.read_text()) if man_path.exists() else {"version": "1.0", "assets": []}
    manifest.setdefault("metadata", {}).update(pipeline="documentary-montage", corpus_dir=str(corpus_dir))
    by_id = {a["id"]: a for a in manifest["assets"]}

    missing = [k for k, v in picks.items() if (v if isinstance(v, str) else v["clip"]) not in rows]
    if missing:
        raise SystemExit(f"clip ids not in {corpus_dir}/index.jsonl: {missing}")

    for key, pick in picks.items():
        pick = {"clip": pick} if isinstance(pick, str) else pick
        row = rows[pick["clip"]]
        src = corpus_dir / row["local_path"]
        preview = proj / "assets" / "previews" / f"{key}.jpg"
        if row["kind"] == "video":
            dest = proj / "assets" / "video" / f"{key}.mp4"
            sh("ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-c:v", "libx264", "-crf", 16,
               "-preset", "fast", "-pix_fmt", "yuv420p", dest)
            sh("ffmpeg", "-v", "error", "-y", "-ss", pick.get("in", 0), "-i", dest, "-frames:v", 1,
               "-vf", "scale=800:-2", preview)
        else:
            dest = proj / "assets" / "images" / f"{key}.jpg"
            sh("ffmpeg", "-v", "error", "-y", "-i", src, "-frames:v", 1, "-q:v", 2, dest)
            sh("ffmpeg", "-v", "error", "-y", "-i", dest, "-vf", "scale=800:-2", "-q:v", 3, preview)

        credits[key] = {"clip_id": row["clip_id"], "source": row["source"], "kind": row["kind"],
                        "page": row["source_url"], "license": row.get("license") or None,
                        "artist": row.get("creator") or None}
        aid = f"asset_{key}"
        by_id[aid] = {
            "id": aid, "type": row["kind"], "path": str(dest), "source_tool": "corpus_builder",
            "scene_id": pick.get("slot", key), "provider": row["source"],
            "license": row.get("license") or "unknown (check the source page)",
            "original_url": row["source_url"], "subtype": "stock",
            "resolution": f"{row.get('width', 0)}x{row.get('height', 0)}",
            "generation_summary": f"clip_search pick {row['clip_id']} for '{row.get('query', '')}'",
        }
        if row["kind"] == "video":
            by_id[aid]["duration_seconds"] = row.get("duration") or 0
        print(f"{key:<16} {row['kind']:<5} {row['source']:<12} {row.get('license') or '?'}", flush=True)

    manifest["assets"] = list(by_id.values())
    cred_path.write_text(json.dumps(credits, indent=1, ensure_ascii=False))
    man_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
