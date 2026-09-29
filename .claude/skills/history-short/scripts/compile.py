"""Run the mechanical tail of a history Short in one command: ingest -> build -> lint ->
snapshots -> render -> upload encode (+ loudness fix, optional <30 MB preview).

  python compile.py <id>                # full run, projects/<id>/renders/upload.mp4
  python compile.py <id> --check-only   # stop after lint + snapshots (review the contact sheet first)
  python compile.py <id> --draft        # quick draft render, no upload encode
  python compile.py <id> --preview      # also write renders/preview.mp4 under 30 MB

Other flags: --skip-ingest (don't re-run from_corpus.py), --no-mix (keep the existing audio mix).
<id> can also be a path to the project directory.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parents[3]
TARGET_LUFS = -14.0
MIN_LUFS = -15.0  # quieter than this gets a gain + limiter remux
PREVIEW_MB = 28


def step(msg):
    print(f"\n==> {msg}", flush=True)


def run(*cmd, cwd=None, capture=False):
    cmd = list(map(str, cmd))
    if capture:
        r = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if r.returncode:
            sys.exit(f"failed ({r.returncode}): {' '.join(cmd)}\n{r.stdout[-2000:]}")
        return r.stdout
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode:
        sys.exit(f"failed ({r.returncode}): {' '.join(cmd)}")


def duration(path):
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                     path, capture=True).strip())


def loudness(path):
    out = run("ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
              "-f", "null", "-", capture=True)
    summary = out[out.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--skip-ingest", action="store_true")
    ap.add_argument("--no-mix", action="store_true")
    a = ap.parse_args()

    proj = Path(a.project)
    if not proj.is_dir():
        proj = REPO / "projects" / a.project
    proj = proj.resolve()
    if not (proj / "short.json").exists():
        sys.exit(f"no short.json in {proj}")
    hf, renders = proj / "hyperframes", proj / "renders"
    renders.mkdir(exist_ok=True)
    total = json.loads((proj / "short.json").read_text())["total"]

    picks = proj / "picks.json"
    if a.skip_ingest or not picks.exists():
        step("ingest: skipped" + ("" if a.skip_ingest else " (no picks.json)"))
    else:
        step("ingest picks from the corpus")
        run(sys.executable, SCRIPTS / "from_corpus.py", proj, picks)

    step("build the HyperFrames composition")
    run(sys.executable, SCRIPTS / "build_short.py", proj, *(["--no-mix"] if a.no_mix else []))

    step("lint")
    out = run("npx", "hyperframes", "lint", cwd=hf, capture=True)
    errors = re.search(r"(\d+) error\(s\)", out)
    if not errors or int(errors.group(1)):
        sys.exit(out[-3000:] + "\nlint failed")
    print(out.strip().splitlines()[-1])

    step("snapshots")
    times = ",".join(f"{total * (i + 0.5) / 12:.1f}" for i in range(12))
    for old in (hf / "snapshots").glob("*"):
        old.unlink()  # don't let a previous run's frames pass for this one
    run("npx", "hyperframes", "snapshot", "--at", times, "--no-end", "--describe", "false", cwd=hf, capture=True)
    for sheet in sorted((hf / "snapshots").glob("contact-sheet*.jpg")) or [hf / "snapshots"]:
        print(f"contact sheet: {sheet}")
    if a.check_only:
        print("check-only: review the contact sheet (crops, dark shots, nudity), then re-run without --check-only")
        return

    final = renders / ("draft.mp4" if a.draft else "final.mp4")
    step(f"render ({'draft' if a.draft else 'delivery'}) -> {final.name}")
    run("npx", "hyperframes", "render", "--quality", "draft" if a.draft else "delivery", "--output", final, cwd=hf)
    if a.draft:
        print(f"\ndone: {final}")
        return

    upload = renders / "upload.mp4"
    step("upload encode")
    run("ffmpeg", "-v", "error", "-y", "-i", final, "-c:v", "libx264", "-preset", "slow", "-crf", 19,
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", upload)
    lufs = loudness(upload)
    print(f"loudness: {lufs:.1f} LUFS")
    if lufs < MIN_LUFS:
        gain = TARGET_LUFS - lufs
        step(f"loudness fix: +{gain:.1f} dB with a limiter")
        tmp = renders / "upload.tmp.mp4"
        run("ffmpeg", "-v", "error", "-y", "-i", upload, "-c:v", "copy", "-af",
            f"volume={gain:.1f}dB,alimiter=limit=0.8:level=false", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", tmp)
        tmp.replace(upload)
        print(f"loudness now: {loudness(upload):.1f} LUFS")

    if a.preview and upload.stat().st_size <= PREVIEW_MB * 1e6:
        step("preview: upload.mp4 is already under 30 MB, send that")
    elif a.preview:
        step("preview under 30 MB (2-pass)")
        dur = duration(upload)
        kbps = int(PREVIEW_MB * 8192 / dur - 160)
        preview = renders / "preview.mp4"
        common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p"]
        run("ffmpeg", "-v", "error", "-y", "-i", upload, *common, "-pass", 1, "-passlogfile", renders / "ff2pass",
            "-an", "-f", "mp4", "/dev/null")
        run("ffmpeg", "-v", "error", "-y", "-i", upload, *common, "-pass", 2, "-passlogfile", renders / "ff2pass",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", preview)
        for f in renders.glob("ff2pass*"):
            f.unlink()
        print(f"preview: {preview} ({preview.stat().st_size / 1e6:.1f} MB)")

    print(f"\ndone: {upload} ({upload.stat().st_size / 1e6:.1f} MB, {duration(upload):.1f} s)")


if __name__ == "__main__":
    main()
