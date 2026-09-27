"""Build a 9:16 history Short (HyperFrames workspace) from <project>/short.json.

  python build_short.py projects/<id>            # crops, mixes audio, writes index.html
  python build_short.py projects/<id> --no-mix   # skip the audio re-mix

Then: cd projects/<id>/hyperframes && npx hyperframes lint && \
      npx hyperframes snapshot --at 1,10,20 --no-end && \
      npx hyperframes render --quality delivery --output ../renders/final.mp4

See ../SKILL.md for the short.json format. Crop coords (cx, cy, h) are in the
image's 800px-wide preview space: centre x, centre y, crop height.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1920
SKILL = Path(__file__).resolve().parent


def sh(*cmd, **kw):
    return subprocess.run(list(map(str, cmd)), check=True, **kw)


def ensure_runtime_files(hf):
    """Local gsap + fonts so the render never depends on a CDN."""
    (hf / "lib").mkdir(exist_ok=True)
    (hf / "fonts").mkdir(exist_ok=True)
    need = {
        hf / "lib" / "gsap.min.js": ("gsap@3.14.2", "dist/gsap.min.js"),
        hf / "fonts" / "anton-latin-400-normal.woff2": ("@fontsource/anton", "files/anton-latin-400-normal.woff2"),
        hf / "fonts" / "cinzel-latin-700-normal.woff2": ("@fontsource/cinzel", "files/cinzel-latin-700-normal.woff2"),
    }
    tmp = hf / ".pkgtmp"
    for dest, (pkg, inner) in need.items():
        if dest.exists():
            continue
        tmp.mkdir(exist_ok=True)
        tgz = subprocess.check_output(["npm", "pack", pkg, "-q"], cwd=tmp, text=True).strip().splitlines()[-1]
        sh("tar", "xzf", tmp / tgz, "-C", tmp)
        shutil.copy(tmp / "package" / inner, dest)
        shutil.rmtree(tmp / "package")
    if tmp.exists():
        shutil.rmtree(tmp)


def mix_audio(proj, cfg, out):
    """Voice at -16 LUFS, music ~22 dB under it (with an optional silent gap), SFX at fixed times."""
    total = cfg["total"]
    music = cfg["music"]
    inputs = [proj / cfg.get("narration", "assets/audio/narration.mp3"), proj / music["file"]]
    fl = ["[0:a]loudnorm=I=-16:TP=-2:LRA=11,aresample=44100,aformat=channel_layouts=stereo,apad=pad_dur=0.5[v]"]
    gap = music.get("gap")
    gap_expr = f",volume='if(between(t,{gap[0]},{gap[1]}),0,1)':eval=frame" if gap else ""
    for d0, d1, g in music.get("duck", []):  # [start, end, gain 0-1], 0.3 s ramps in and out
        gap_expr += f",volume='1-{1 - g}*clip(min((t-{d0})/0.3,({d1}-t)/0.3),0,1)':eval=frame"
    fl.append(f"[1:a]atrim=0:{total + 0.1},loudnorm=I=-24:TP=-2,aresample=44100,aformat=channel_layouts=stereo,"
              f"volume={music.get('gain_db', -14)}dB{gap_expr},afade=t=in:st=0:d=0.5[m]")
    labels = ["[v]", "[m]"]
    for i, s in enumerate(cfg.get("sfx", [])):
        inputs.append(proj / s["file"])
        ms = int(s["at"] * 1000)
        fade = f",afade=t=out:st={s['fade_out'][0]}:d={s['fade_out'][1]}" if s.get("fade_out") else ""
        fade += f",afade=t=in:st=0:d={s['fade_in']}" if s.get("fade_in") else ""
        fl.append(f"[{i + 2}:a]volume={s.get('volume', 0.8)}{fade},aformat=channel_layouts=stereo,adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    fl.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.9[out]")
    args = ["ffmpeg", "-v", "error", "-y"]
    for f in inputs:
        args += ["-i", f]
    sh(*args, "-filter_complex", ";".join(fl), "-map", "[out]", "-t", total, "-ar", 44100, "-c:a", "pcm_s16le", out)


def crop(img_dir, out_dir, name, cx, cy, h, idx):
    src = img_dir / f"{name}.jpg"
    dims = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", str(src)], text=True).strip()
    sw, shh = map(int, dims.split(",")[:2])
    k = sw / 800
    ch = min(h * k, shh)
    cw = ch * 9 / 16
    if cw > sw:
        cw, ch = sw, sw * 16 / 9
    x = min(max(cx * k - cw / 2, 0), sw - cw)
    y = min(max(cy * k - ch / 2, 0), shh - ch)
    out = out_dir / f"s{idx:02d}_{name}.jpg"
    vf = (f"crop={int(cw)}:{int(ch)}:{int(x)}:{int(y)},scale={W}:{H}:flags=lanczos,"
          "eq=contrast=1.12:saturation=0.82:brightness=-0.05:gamma=0.92,"
          "colorbalance=rs=0.04:gs=0.0:bs=-0.05:rm=0.03:bm=-0.03")
    sh("ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-q:v", 2, out)
    return out.name


def caption_chunks(words_file, highlights, total):
    raw = json.loads(Path(words_file).read_text())
    toks = [(w["text"], w["start"], w["end"]) for w in raw["words"] if w["type"] == "word"]
    norm = lambda s: s.lower().strip(".,:;!?'\"")
    starts_phrase = lambda i: next(((p, c) for p, c in highlights.items()
                                    if " ".join(norm(t[0]) for t in toks[i:i + len(p.split())]) == p), None)
    chunks, i = [], 0
    while i < len(toks):
        hit = starts_phrase(i)
        if hit:
            n = len(hit[0].split())
            grp = toks[i:i + n]
            chunks.append((" ".join(t[0] for t in grp), grp[0][1], grp[-1][2], hit[1]))
            i += n
            continue
        grp = [toks[i]]
        i += 1
        while i < len(toks) and len(grp) < 3:
            prev = grp[-1]
            if prev[0][-1] in ".,:;!?" or toks[i][1] - prev[2] > 0.25 or starts_phrase(i):
                break
            grp.append(toks[i])
            i += 1
        chunks.append((" ".join(t[0] for t in grp), grp[0][1], grp[-1][2], None))
    out = []
    for j, (txt, s, e, col) in enumerate(chunks):
        nxt = chunks[j + 1][1] if j + 1 < len(chunks) else total
        e = min(max(e, s + 0.3), nxt, e + 0.6)  # hold until next chunk, max +0.6s
        out.append((txt.rstrip(".,:;").replace("...", ""), round(s, 3), round(e, 3), col))
    return out


def main(proj, do_mix=True):
    proj = Path(proj).resolve()
    cfg = json.loads((proj / "short.json").read_text())
    total = cfg["total"]
    hf = proj / "hyperframes"
    shots_dir = hf / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    (hf / "audio").mkdir(exist_ok=True)
    ensure_runtime_files(hf)
    if do_mix:
        mix_audio(proj, cfg, hf / "audio" / "final_mix.wav")

    shots, tl = cfg["shots"], []
    chaos = cfg.get("chaos_window")
    shot_html = []
    for idx, (start, name, cx, cy, h, *opt) in enumerate(shots):
        end = shots[idx + 1][0] if idx + 1 < len(shots) else total
        dur = round(end - start, 3)
        fn = crop(proj / "assets" / "images", shots_dir, name, cx, cy, h, idx)
        sid = f"shot{idx:02d}"
        shot_html.append(f'<img id="{sid}" class="clip shot" src="shots/{fn}" '
                         f'data-start="{start}" data-duration="{dur}" data-track-index="1" />')
        drift = 18 if idx % 2 else -18  # 100% -> 108% zoom (or opt[0]) with a slight alternating drift
        zoom, ease = (opt[0], '"power2.out"') if opt else (1.08, '"none"')
        tl.append(f'tl.fromTo("#{sid}",{{scale:1,x:0}},{{scale:{zoom},x:{drift},duration:{dur},ease:{ease}}},{start});')
        if chaos and chaos[0] <= start < chaos[1]:
            tl.append(f'tl.fromTo("#{sid}",{{filter:"brightness(1.9)"}},'
                      f'{{filter:"brightness(1)",duration:0.18,ease:"power2.out",immediateRender:false}},{start});')

    cap_html = []
    words = proj / cfg.get("words", "artifacts/words_raw.json")
    for j, (txt, s, e, col) in enumerate(caption_chunks(words, cfg.get("highlights", {}), total)):
        cid = f"cap{j:03d}"
        style = f' style="color:{col}"' if col else ""
        cap_html.append(f'<div id="{cid}" class="clip cap" data-start="{s}" data-duration="{round(e - s, 3)}" '
                        f'data-track-index="3"><span{style}>{txt.upper()}</span></div>')
        tl.append(f'tl.fromTo("#{cid} span",{{scale:0.72,opacity:0}},'
                  f'{{scale:1,opacity:1,duration:0.12,ease:"back.out(2.5)"}},{s});')

    extras = ""
    nt = cfg.get("nametag")
    if nt:
        extras += (f'\n      <div id="nametag" class="clip nametag" data-start="{nt["start"]}" data-duration="{nt["duration"]}" '
                   f'data-track-index="4">\n        <div class="nt-line">{nt["title"]}</div><div class="nt-sub">{nt["sub"]}</div>\n      </div>')
        tl.append(f'tl.from("#nametag .nt-line",{{y:30,opacity:0,duration:0.4,ease:"power3.out"}},{nt["start"]});')
        tl.append(f'tl.from("#nametag .nt-sub",{{y:20,opacity:0,duration:0.4,ease:"power3.out"}},{nt["start"] + 0.15});')
    for k, lb in enumerate(cfg.get("labels", [])):  # small corner tags, e.g. "Authentic 16th-Century Portrait"
        lid = f"label{k}"
        extras += (f'\n      <div id="{lid}" class="clip corner" data-start="{lb["start"]}" data-duration="{lb["duration"]}" '
                   f'data-track-index="6"><span>{lb["text"]}</span></div>')
        tl.append(f'tl.from("#{lid} span",{{x:-40,opacity:0,duration:0.35,ease:"power3.out"}},{lb["start"]});')
    bn = cfg.get("banner")
    if bn:
        b0 = bn["start"]
        extras += (f'\n      <div id="subbanner" class="clip subbanner" data-start="{b0}" data-duration="{round(total - b0, 2)}" '
                   f'data-track-index="5">\n        <div class="sb-inner"><div class="sb-btn">{bn.get("button", "SUBSCRIBE")}</div>\n'
                   f'        <div class="sb-text">{bn["text"]}</div></div>\n      </div>')
        tl.append(f'tl.from("#subbanner .sb-inner",{{y:80,opacity:0,duration:0.5,ease:"back.out(1.6)"}},{b0});')
        pulses = max(1, int((total - b0 - 0.6) / 0.9) * 2 - 1)
        tl.append(f'tl.fromTo("#subbanner .sb-btn",{{scale:1}},{{scale:1.08,duration:0.45,yoyo:true,repeat:{pulses},ease:"sine.inOut"}},{b0 + 0.6});')

    html = TEMPLATE.format(total=total, shots="\n      ".join(shot_html), caps="\n      ".join(cap_html),
                           extras=extras, timeline="\n      ".join(tl))
    (hf / "index.html").write_text(html)
    print(f"{len(shots)} shots, {len(cap_html)} captions -> {hf / 'index.html'}")


TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>History Short</title>
    <script src="lib/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Anton"; src: url("fonts/anton-latin-400-normal.woff2") format("woff2"); }}
      @font-face {{ font-family: "Cinzel"; font-weight: 700; src: url("fonts/cinzel-latin-700-normal.woff2") format("woff2"); }}
      html, body {{ margin: 0; background: #000; }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      .bg {{ position: absolute; inset: 0; background: #000; }}
      .shot {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; display: block; }}
      .vignette {{ position: absolute; inset: 0; pointer-events: none;
        background: radial-gradient(ellipse 75% 60% at 50% 48%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.78) 100%); }}
      .cap {{ position: absolute; left: 60px; right: 60px; top: 860px; height: 200px;
        display: flex; align-items: center; justify-content: center; text-align: center; }}
      .cap span {{ display: block; font-family: "Anton", sans-serif; font-size: 118px; line-height: 1.02;
        color: #fff; letter-spacing: 1px; -webkit-text-stroke: 7px #000; paint-order: stroke fill;
        text-shadow: 0 8px 24px rgba(0,0,0,0.85); }}
      .nametag {{ position: absolute; left: 0; right: 0; top: 1360px; height: 220px; text-align: center; }}
      .nt-line {{ font-family: "Cinzel", serif; font-weight: 700; font-size: 92px; color: #e9c46a;
        letter-spacing: 10px; text-shadow: 0 4px 18px #000; }}
      .nt-sub {{ font-family: "Cinzel", serif; font-weight: 700; font-size: 34px; color: #f1e6d0;
        letter-spacing: 6px; margin-top: 8px; text-shadow: 0 3px 12px #000; }}
      .corner {{ position: absolute; left: 48px; top: 230px; }}
      .corner span {{ display: inline-block; font-family: "Cinzel", serif; font-weight: 700; font-size: 34px;
        color: #f4e9d2; letter-spacing: 2px; padding: 10px 20px; background: rgba(8,6,4,0.72);
        border-left: 6px solid #e9c46a; border-radius: 6px; }}
      .subbanner {{ position: absolute; left: 0; right: 0; top: 1380px; height: 330px; }}
      .sb-inner {{ margin: 0 70px; padding: 34px 30px 38px; background: rgba(8,6,4,0.78);
        border: 3px solid #e9c46a; border-radius: 26px; text-align: center; }}
      .sb-btn {{ display: inline-block; background: #e3171d; color: #fff; font-family: "Anton", sans-serif;
        font-size: 64px; letter-spacing: 3px; padding: 10px 46px; border-radius: 16px; }}
      .sb-text {{ font-family: "Cinzel", serif; font-weight: 700; font-size: 54px; color: #f4e9d2;
        margin-top: 22px; line-height: 1.2; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-width="1080" data-height="1920" data-duration="{total}" data-fps="30">
      <div id="bgfill" class="clip bg" data-start="0" data-duration="{total}" data-track-index="0"></div>
      {shots}
      <div id="vig" class="clip vignette" data-start="0" data-duration="{total}" data-track-index="2"></div>
      {caps}
      {extras}
      <audio id="mix" src="audio/final_mix.wav" data-start="0" data-duration="{total}" data-track-index="10" data-volume="1"></audio>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {timeline}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


if __name__ == "__main__":
    main(sys.argv[1], do_mix="--no-mix" not in sys.argv)
