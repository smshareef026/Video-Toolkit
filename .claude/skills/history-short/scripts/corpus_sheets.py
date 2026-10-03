"""Labelled contact sheets of a whole corpus, so you can pick images by eye instead of trusting scores.

  python corpus_sheets.py <id> [--per-sheet 20] [--out DIR]

Writes sheet_0.jpg, sheet_1.jpg, ... (5 columns x 4 rows, each tile labelled with the clip id and the
Commons file title) and titles.json (clip_id -> file title). Open each sheet with Read.
CLIP scores sit around 0.3-0.4 for almost everything, so they don't tell good picks from bad ones;
the sheets do, and they also show unrelated junk the queries pulled in (subway stations, etc.).
Run it with the project venv (needs Pillow).
"""
import argparse
import json
import urllib.parse
from pathlib import Path

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project id or path to projects/<id>")
    ap.add_argument("--per-sheet", type=int, default=20)
    ap.add_argument("--out", default=None, help="output dir (default: the project's renders/corpus_sheets)")
    a = ap.parse_args()

    proj = Path(a.project)
    if not proj.exists():
        proj = Path("projects") / a.project
    corpus = proj / "corpus"
    out = Path(a.out) if a.out else proj / "renders" / "corpus_sheets"
    out.mkdir(parents=True, exist_ok=True)

    recs = [json.loads(line) for line in open(corpus / "index.jsonl")]
    titles = {}
    for r in recs:
        r["title"] = urllib.parse.unquote(r["source_url"].split("File:")[-1])
        titles[r["clip_id"]] = r["title"]
    json.dump(titles, open(out / "titles.json", "w"), indent=1)

    W, H, cols = 360, 360, 5
    rows = -(-a.per_sheet // cols)
    for n in range(0, len(recs), a.per_sheet):
        sheet = Image.new("RGB", (cols * W, rows * H), "black")
        for i, r in enumerate(recs[n:n + a.per_sheet]):
            try:
                im = Image.open(corpus / r["local_path"])
                im.thumbnail((W, H - 24))
            except Exception as e:  # videos or unreadable files
                print("skip", r["clip_id"], e)
                continue
            x, y = (i % cols) * W, (i // cols) * H
            sheet.paste(im, (x, y + 24))
            ImageDraw.Draw(sheet).text((x + 2, y + 4), r["clip_id"].split("_", 1)[-1] + " " + r["title"][:40], fill="white")
        sheet.save(out / f"sheet_{n // a.per_sheet}.jpg", quality=80)
    print(f"{len(recs)} clips -> {out}")


if __name__ == "__main__":
    main()
