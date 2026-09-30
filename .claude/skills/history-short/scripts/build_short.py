"""Build a 9:16 history Short (HyperFrames workspace) from <project>/short.json.

  python build_short.py projects/<id>              # crops, mixes audio, writes hyperframes/index.html
  python build_short.py projects/<id> --no-mix     # skip the audio re-mix
  python build_short.py projects/<id> --landscape  # 1920x1080 long-form cut -> hyperframes-16x9/

Then: cd projects/<id>/hyperframes && npx hyperframes lint && \
      npx hyperframes snapshot --at 1,10,20 --no-end && \
      npx hyperframes render --quality delivery --output ../renders/final.mp4

See ../SKILL.md for the short.json format. Crop coords (cx, cy, h) are in the
image's 800px-wide preview space: centre x, centre y, crop height.
A shot key with assets/video/<key>.mp4 (archival film from the corpus) is cut as a
video clip; an optional 6th shot field is its in-point in seconds.

--landscape reuses the same short.json. Each crop keeps its vertical extent and widens to
16:9 around the same centre; when the image is too narrow for that (busts, statues),
the crop sits centred over a blurred, darkened copy of itself instead of being cut.
If projects/<id>/short_16x9.json exists, --landscape uses it instead of short.json (e.g. a long-form
ending with a spoken call to action while the Short keeps its loop).
"crops_16x9" in short.json overrides the 16:9 crop per image name or shot index:
{"camuccini": [cx, cy, h], "12": [cx, cy, h]} (h = crop height, width = h*16/9).
Widening can bring back what a 9:16 crop excluded, so re-check the contact sheet for nudity.
"""
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1920

# Camera moves on each shot: (from, to) GSAP props. Pans/tilts hold a 1.1 scale so the
# frame never shows an edge (1.1 x 1080 leaves 54 px spare each side, 96 px top/bottom).
MOVES = {
    "push_in":   ({"scale": 1.0, "x": 0}, {"scale": 1.08, "x": 18}),
    "pull_out":  ({"scale": 1.1, "x": 0}, {"scale": 1.0, "x": 0}),
    "pan_left":  ({"scale": 1.1, "x": 40}, {"scale": 1.1, "x": -40}),
    "pan_right": ({"scale": 1.1, "x": -40}, {"scale": 1.1, "x": 40}),
    "tilt_up":   ({"scale": 1.1, "y": 70}, {"scale": 1.1, "y": -70}),
    "tilt_down": ({"scale": 1.1, "y": -70}, {"scale": 1.1, "y": 70}),
}
# Default rotation: no move repeats back to back, and push-ins dominate.
MOVE_CYCLE = ["push_in", "pan_left", "pull_out", "tilt_up", "push_in", "pan_right", "pull_out", "tilt_down"]
PARTICLES = {  # color, size px, rise px over one loop, loop seconds, peak opacity
    "dust":   {"color": "255,236,200", "size": (2, 5), "rise": (60, 160), "loop": (8, 14), "alpha": 0.45},
    "embers": {"color": "255,140,60", "size": (2, 6), "rise": (400, 900), "loop": (4, 8), "alpha": 0.8},
}
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
    fo = music.get("fade_out")
    fade_out = f",afade=t=out:st={total - fo}:d={fo}" if fo else ""
    fl.append(f"[1:a]atrim=0:{total + 0.1},loudnorm=I=-24:TP=-2,aresample=44100,aformat=channel_layouts=stereo,"
              f"volume={music.get('gain_db', -14)}dB{gap_expr},afade=t=in:st=0:d=0.5{fade_out}[m]")
    labels = ["[v]", "[m]"]
    for i, s in enumerate(cfg.get("sfx", [])):
        inputs.append(proj / s["file"])
        ms = int(s["at"] * 1000)
        fade = f",afade=t=out:st={s['fade_out'][0]}:d={s['fade_out'][1]}" if s.get("fade_out") else ""
        fl.append(f"[{i + 2}:a]volume={s.get('volume', 0.8)}{fade},aformat=channel_layouts=stereo,adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    fl.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.9[out]")
    args = ["ffmpeg", "-v", "error", "-y"]
    for f in inputs:
        args += ["-i", f]
    sh(*args, "-filter_complex", ";".join(fl), "-map", "[out]", "-t", total, "-ar", 44100, "-c:a", "pcm_s16le", out)


GRADE = ("eq=contrast=1.12:saturation=0.82:brightness=-0.05:gamma=0.92,"
         "colorbalance=rs=0.04:gs=0.0:bs=-0.05:rm=0.03:bm=-0.03")


def crop_box(src, cx, cy, h):
    """Filter graph ([0:v] -> [out]) for a W:H window centred on (cx, cy) in 800px-preview coords.

    h is the crop height; the width follows the canvas aspect. On a landscape canvas a crop
    too wide for the image keeps the image's full width and is fitted over a blurred copy."""
    dims = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", str(src)], text=True).strip()
    sw, shh = map(int, dims.split(",")[:2])
    k = sw / 800
    ch = min(h * k, shh)
    cw = ch * W / H
    fit = False
    if cw > sw:
        if W > H:  # landscape: keep the approved vertical framing, pillarbox the rest
            cw, fit = sw, True
        else:
            cw, ch = sw, sw * H / W
    x = min(max(cx * k - cw / 2, 0), sw - cw)
    y = min(max(cy * k - ch / 2, 0), shh - ch)
    box = f"crop={int(cw)}:{int(ch)}:{int(x)}:{int(y)}"
    if not fit:
        return f"[0:v]{box},scale={W}:{H}:flags=lanczos,{GRADE}[out]"
    return (f"[0:v]{box},{GRADE},split[a][b];"
            f"[b]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=40,"
            f"eq=brightness=-0.22:saturation=0.7[bg];"
            f"[a]scale=-2:{H}:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:0[out]")


def crop(img_dir, out_dir, name, cx, cy, h, idx):
    src = img_dir / f"{name}.jpg"
    out = out_dir / f"s{idx:02d}_{name}.jpg"
    sh("ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", crop_box(src, cx, cy, h),
       "-map", "[out]", "-q:v", 2, out)
    return out.name


def crop_video(src, out_dir, name, cx, cy, h, idx, t_in, dur):
    """Cut `dur` seconds of archival film from `t_in`, cropped, graded, 30 fps, silent."""
    out = out_dir / f"s{idx:02d}_{name}.mp4"
    graph = crop_box(src, cx, cy, h).replace("[out]", "[c];[c]fps=30[out]")
    sh("ffmpeg", "-v", "error", "-y", "-ss", t_in, "-i", src, "-t", dur, "-an",
       "-filter_complex", graph, "-map", "[out]", "-c:v", "libx264", "-crf", 17,
       "-preset", "fast", "-pix_fmt", "yuv420p", out)
    return out.name


def move_tween(sid, move, dur, start, intensity):
    a, b = MOVES[move]
    # Offsets are tuned for 1080x1920; scale them to the canvas so 1.1 zoom still hides the edges.
    px = {"x": W / 1080, "y": H / 1920}
    scale = lambda d: {k: (1 + (v - 1) * intensity if k == "scale" else round(v * intensity * px[k], 1)) for k, v in d.items()}
    js = lambda d: "{" + ",".join(f"{k}:{v}" for k, v in d.items())
    return f'tl.fromTo("#{sid}",{js(scale(a))}}},{js(scale(b))},duration:{dur},ease:"sine.inOut"}},{start});'


def particle_layer(spec, total):
    """Seeded (so every render is identical) drifting dust or embers over the whole Short.

    Plain solid dots on purpose: HyperFrames captures black frames once ~40 elements carry
    blur / gradient CSS, so particles must not use either."""
    spec = {"style": spec} if isinstance(spec, str) else dict(spec)
    style = PARTICLES[spec.get("style", "dust")]
    rng = random.Random(spec.get("seed", 7))
    html, tl = [], []
    for i in range(int(spec.get("count", 36))):
        size = rng.uniform(*style["size"])
        loop = rng.uniform(*style["loop"])
        rise = rng.uniform(*style["rise"])
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        pid = f"pt{i:02d}"
        # Drift moves the <i>; the twinkle fades the inner <b>, so each element has one tween.
        html.append(f'<i id="{pid}" style="left:{x:.0f}px;top:{y:.0f}px;width:{size:.1f}px;height:{size:.1f}px">'
                    f'<b style="background:rgb({style["color"]})"></b></i>')
        reps = int(total / loop) + 1
        tl.append(f'tl.fromTo("#{pid}",{{x:0,y:0}},{{x:{rng.uniform(-40, 40):.0f},y:{-rise:.0f},duration:{loop:.2f},'
                  f'ease:"none",repeat:{reps}}},{rng.uniform(0, 1.5):.2f});')
        tl.append(f'tl.fromTo("#{pid} b",{{opacity:0}},{{opacity:{style["alpha"] * spec.get("opacity", 1):.2f},'
                  f'duration:{loop / 2:.2f},ease:"sine.inOut",yoyo:true,repeat:{reps * 2}}},{rng.uniform(0, 1.5):.2f});')
    div = (f'<div id="particles" class="clip particles" data-start="0" data-duration="{total}" data-track-index="7">'
           + "".join(html) + "</div>")
    return div, tl


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


def main(proj, do_mix=True, landscape=False):
    global W, H
    if landscape:
        W, H = 1920, 1080
    proj = Path(proj).resolve()
    cfg_file = proj / "short_16x9.json" if landscape and (proj / "short_16x9.json").exists() else proj / "short.json"
    cfg = json.loads(cfg_file.read_text())
    total = cfg["total"]
    hf = proj / ("hyperframes-16x9" if landscape else "hyperframes")
    wide = cfg.get("crops_16x9", {}) if landscape else {}
    shots_dir = hf / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    (hf / "audio").mkdir(exist_ok=True)
    ensure_runtime_files(hf)
    if do_mix:
        mix_audio(proj, cfg, hf / "audio" / "final_mix.wav")

    shots, tl = cfg["shots"], []
    chaos = cfg.get("chaos_window")
    motion = cfg.get("motion", {})
    overrides = {int(k): v for k, v in motion.get("moves", {}).items()}
    intensity = motion.get("intensity", 1.0)
    shot_html = []
    for idx, (start, name, cx, cy, h, *rest) in enumerate(shots):
        cx, cy, h = wide.get(str(idx)) or wide.get(name) or (cx, cy, h)
        end = shots[idx + 1][0] if idx + 1 < len(shots) else total
        dur = round(end - start, 3)
        sid = f"shot{idx:02d}"
        video = proj / "assets" / "video" / f"{name}.mp4"
        if video.exists():
            fn = crop_video(video, shots_dir, name, cx, cy, h, idx, rest[0] if rest else 0, dur)
            shot_html.append(f'<video id="{sid}" class="clip shot" src="shots/{fn}" muted playsinline '
                             f'data-start="{start}" data-duration="{dur}" data-track-index="1"></video>')
        else:
            fn = crop(proj / "assets" / "images", shots_dir, name, cx, cy, h, idx)
            shot_html.append(f'<img id="{sid}" class="clip shot" src="shots/{fn}" '
                             f'data-start="{start}" data-duration="{dur}" data-track-index="1" />')
        move = overrides.get(idx) or MOVE_CYCLE[idx % len(MOVE_CYCLE)]
        if chaos and chaos[0] <= start < chaos[1]:
            move = "push_in"  # the chaos cuts are too short for a pan to read
        tl.append(move_tween(sid, move, dur, start, intensity))
        if chaos and chaos[0] <= start < chaos[1]:
            tl.append(f'tl.fromTo("#{sid}",{{filter:"brightness(1.9)"}},'
                      f'{{filter:"brightness(1)",duration:0.18,ease:"power2.out",immediateRender:false}},{start});')

    cap_html = []
    words = proj / cfg.get("words", "artifacts/words_raw.json")
    for j, (txt, s, e, col) in enumerate(caption_chunks(words, cfg.get("highlights", {}), total)):
        cid = f"cap{j:03d}"
        style = ""  # captions are always white (channel rule); highlights only keep a phrase together
        cap_html.append(f'<div id="{cid}" class="clip cap" data-start="{s}" data-duration="{round(e - s, 3)}" '
                        f'data-track-index="3"><span{style}>{txt.upper()}</span></div>')
        tl.append(f'tl.fromTo("#{cid} span",{{scale:0.72,opacity:0}},'
                  f'{{scale:1,opacity:1,duration:0.12,ease:"back.out(2.5)"}},{s});')

    particles = ""
    if cfg.get("particles", "dust"):
        particles, ptl = particle_layer(cfg.get("particles", "dust"), total)
        tl.extend(ptl)

    extras = ""
    nt = cfg.get("nametag")
    if nt:
        extras += (f'\n      <div id="nametag" class="clip nametag" data-start="{nt["start"]}" data-duration="{nt["duration"]}" '
                   f'data-track-index="4">\n        <div class="nt-line">{nt["title"]}</div><div class="nt-sub">{nt["sub"]}</div>\n      </div>')
        tl.append(f'tl.from("#nametag .nt-line",{{y:30,opacity:0,duration:0.4,ease:"power3.out"}},{nt["start"]});')
        tl.append(f'tl.from("#nametag .nt-sub",{{y:20,opacity:0,duration:0.4,ease:"power3.out"}},{nt["start"] + 0.15});')
    for k, lb in enumerate(cfg.get("labels", [])):  # small top-left "museum" tags, e.g. AUTHENTIC ROMAN BUST
        lid = f"label{k}"
        extras += (f'\n      <div id="{lid}" class="clip label" data-start="{lb["start"]}" data-duration="{lb["duration"]}" '
                   f'data-track-index="6">{lb["text"]}</div>')
        tl.append(f'tl.from("#{lid}",{{x:-30,opacity:0,duration:0.35,ease:"power2.out"}},{lb["start"]});')
    bn = cfg.get("banner")
    if bn:
        b0 = bn["start"]
        extras += (f'\n      <div id="subbanner" class="clip subbanner" data-start="{b0}" data-duration="{round(total - b0, 2)}" '
                   f'data-track-index="5">\n        <div class="sb-inner"><div class="sb-btn">{bn.get("button", "SUBSCRIBE")}</div>\n'
                   f'        <div class="sb-text">{bn["text"]}</div></div>\n      </div>')
        tl.append(f'tl.from("#subbanner .sb-inner",{{y:80,opacity:0,duration:0.5,ease:"back.out(1.6)"}},{b0});')
        pulses = max(1, int((total - b0 - 0.6) / 0.9) * 2 - 1)
        tl.append(f'tl.fromTo("#subbanner .sb-btn",{{scale:1}},{{scale:1.08,duration:0.45,yoyo:true,repeat:{pulses},ease:"sine.inOut"}},{b0 + 0.6});')

    html = TEMPLATE.format(w=W, h=H, canvas_css=(LANDSCAPE_CSS if landscape else "") + (cfg.get("extra_css", "") if not landscape else ""), total=total, shots="\n      ".join(shot_html), caps="\n      ".join(cap_html),
                           particles=particles,
                           extras=extras, timeline="\n      ".join(tl))
    (hf / "index.html").write_text(html)
    print(f"{len(shots)} shots, {len(cap_html)} captions -> {hf / 'index.html'}")


TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <title>History Short</title>
    <script src="lib/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Anton"; src: url("fonts/anton-latin-400-normal.woff2") format("woff2"); }}
      @font-face {{ font-family: "Cinzel"; font-weight: 700; src: url("fonts/cinzel-latin-700-normal.woff2") format("woff2"); }}
      html, body {{ margin: 0; background: #000; }}
      #root {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; background: #000; }}
      .bg {{ position: absolute; inset: 0; background: #000; }}
      .shot {{ position: absolute; inset: 0; width: {w}px; height: {h}px; object-fit: cover; display: block; }}
      .vignette {{ position: absolute; inset: 0; pointer-events: none;
        background: radial-gradient(ellipse 75% 60% at 50% 48%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.78) 100%); }}
      .particles {{ position: absolute; inset: 0; pointer-events: none; overflow: hidden; }}
      .particles i {{ position: absolute; display: block; }}
      .particles b {{ position: absolute; inset: 0; display: block; border-radius: 50%; opacity: 0; }}
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
      .label {{ position: absolute; left: 54px; top: 150px; font-family: "Cinzel", serif; font-weight: 700;
        font-size: 34px; letter-spacing: 5px; color: rgba(255,255,255,0.8); text-shadow: 0 2px 10px #000;
        padding-left: 16px; border-left: 4px solid #e9c46a; }}
      .subbanner {{ position: absolute; left: 0; right: 0; top: 1380px; height: 330px; }}
      .sb-inner {{ margin: 0 70px; padding: 34px 30px 38px; background: rgba(8,6,4,0.78);
        border: 3px solid #e9c46a; border-radius: 26px; text-align: center; }}
      .sb-btn {{ display: inline-block; background: #e3171d; color: #fff; font-family: "Anton", sans-serif;
        font-size: 64px; letter-spacing: 3px; padding: 10px 46px; border-radius: 16px; }}
      .sb-text {{ font-family: "Cinzel", serif; font-weight: 700; font-size: 54px; color: #f4e9d2;
        margin-top: 22px; line-height: 1.2; }}{canvas_css}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-width="{w}" data-height="{h}" data-duration="{total}" data-fps="30">
      <div id="bgfill" class="clip bg" data-start="0" data-duration="{total}" data-track-index="0"></div>
      {shots}
      <div id="vig" class="clip vignette" data-start="0" data-duration="{total}" data-track-index="2"></div>
      {particles}
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


# 16:9 overrides: captions in the lower third, labels top-left, subscribe card top-right.
LANDSCAPE_CSS = """
      .cap {{ left: 200px; right: 200px; top: 790px; height: 190px; }}
      .cap span {{ font-size: 92px; -webkit-text-stroke: 6px #000; }}
      .nametag {{ top: 560px; height: 200px; }}
      .nt-line {{ font-size: 76px; }}
      .label {{ left: 64px; top: 60px; font-size: 28px; }}
      .subbanner {{ left: auto; right: 60px; top: 56px; width: 640px; height: auto; }}
      .sb-inner {{ margin: 0; padding: 22px 24px 26px; border-radius: 22px; }}
      .sb-btn {{ font-size: 48px; padding: 6px 34px; border-radius: 12px; }}
      .sb-text {{ font-size: 36px; margin-top: 14px; }}""".replace("{{", "{").replace("}}", "}")


if __name__ == "__main__":
    main(sys.argv[1], do_mix="--no-mix" not in sys.argv, landscape="--landscape" in sys.argv)
