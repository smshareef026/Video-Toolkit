"""Flag picked images whose licence or author note could cause trouble on YouTube.

  python check_credits.py <id>

Reads projects/<id>/artifacts/image_credits.json (written by from_corpus.py) and prints one line per pick.
A line is marked CHECK when the licence is missing/unknown/NC/ND, or when the author's credit text is long or
contains words like "not", "exclude", "permission", "social" (some Commons authors add a note that
contradicts the CC licence, e.g. "this specifically excludes use in social media"). Swap those picks for another
photo before rendering: a licence tag on Commons is not a guarantee when the author says otherwise.
Exit code 1 if anything is flagged.
"""
import json
import re
import sys
from pathlib import Path

OK_LICENCES = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [1-4]\.\d)", re.I)
RISKY_TEXT = re.compile(r"\bnot\b|exclud|permission|social|prohibit|no commercial|without", re.I)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    proj = Path(sys.argv[1])
    if not proj.exists():
        proj = Path("projects") / sys.argv[1]
    cred = json.load(open(proj / "artifacts" / "image_credits.json"))
    bad = 0
    for key, v in cred.items():
        lic = (v.get("license") or "").strip()
        artist = re.sub(r"\s+", " ", v.get("artist") or "").strip()
        why = []
        if not OK_LICENCES.match(lic) or re.search(r"\bN[CD]\b", lic):
            why.append(f"licence '{lic or 'missing'}'")
        if len(artist) > 80:
            why.append("long author note")
        if RISKY_TEXT.search(artist):
            why.append("restrictive wording in author note")
        flag = "CHECK " + "; ".join(why) if why else "ok"
        bad += bool(why)
        print(f"{key:14} {lic:14} {artist[:50]:50} {flag}")
    print(f"\n{bad} flagged of {len(cred)}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
