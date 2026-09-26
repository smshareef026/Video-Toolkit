"""Build word timeline, captions.ts and public/mix.wav from the ElevenLabs Daniel takes.

Run from the repo root after narration_raw.wav / cta_raw.wav and their transcripts exist.
"""
import json, re, subprocess
from pathlib import Path

ROOT = Path("projects/elagabalus-short")
A = ROOT / "assets/audio"
NARR_OFFSET = 0.15
CTA_GAP = 0.56  # beat between last main word and CTA

MAIN = ("This Roman emperor let lions loose at his dinner parties, just to watch his guests panic. "
        "Elagabalus became emperor at fourteen. Drunk guests would wake up to lions and leopards lying next to them. "
        "Some reportedly died of fright. He served them fake feasts made of wax and glass, and expected them to keep eating. "
        "Then he dropped so many flower petals from the ceiling, that guests were buried alive under them. "
        "By eighteen, his own guards had killed him. And the guests who survived? They still had to come to dinner, "
        "with this Roman emperor—")
CTA = ("I'm covering history's most chaotic rulers all week. Hit subscribe so you don't miss tomorrow's video "
       "on the emperor who tried to make his horse a politician.")
EMPH = {"LIONS", "PANIC", "FRIGHT", "FAKE", "WAX", "GLASS", "BURIED", "ALIVE", "KILLED",
        "CHAOTIC", "SUBSCRIBE", "HORSE", "POLITICIAN"}


def words(transcript, script, offset):
    asr = json.loads((A / transcript).read_text())["word_timestamps"]
    toks = script.split()
    assert len(asr) == len(toks), (transcript, len(asr), len(toks))
    out = []
    for w, tok in zip(asr, toks):
        start, end = w["start"], w["end"]
        # Whisper hangs the preceding pause on the next word's start; pull it back.
        est = 0.12 + 0.07 * len(tok)
        if end - start > est + 0.25:
            start = end - est
        out.append({"text": tok.upper(), "start": round(start + offset, 3), "end": round(end + offset, 3),
                    "emph": re.sub(r"[^A-Z]", "", tok.upper()) in EMPH})
    return out


main = words("narration_raw_transcript.json", MAIN, NARR_OFFSET)
cta_offset = round(main[-1]["end"] + CTA_GAP, 3)
cta = words("cta_raw_transcript.json", CTA, cta_offset)
allw = main + cta

pages, cur = [], []
for w in allw:
    cur.append(w)
    if len(cur) == 3 or re.search(r"[.?!—]$", w["text"]) or w is main[-1]:
        pages.append(cur); cur = []
if cur:
    pages.append(cur)

(ROOT / "composition/captions.ts").write_text(
    "export type Word={text:string;start:number;end:number;emph:boolean};\n"
    f"export const PAGES: Word[][] = {json.dumps(pages)};\n")
(ROOT / "artifacts/captions.json").write_text(json.dumps({"pages": pages}, indent=1))

# SRT
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
srt = []
for i, p in enumerate(pages):
    end = pages[i + 1][0]["start"] if i + 1 < len(pages) else p[-1]["end"] + 0.4
    srt.append(f"{i+1}\n{ts(p[0]['start'])} --> {ts(min(end, p[-1]['end'] + 0.6))}\n{' '.join(w['text'] for w in p)}\n")
(ROOT / "artifacts/captions.srt").write_text("\n".join(srt))


def at(ws, text, n=0):
    hits = [w for w in ws if re.sub(r"[^A-Z]", "", w["text"]) == text]
    return hits[n]["start"]


cta_len = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", str(A / "cta_raw.wav")]))
duration = round(cta_offset + cta_len + 0.35, 2)
cues = {
    "hook_end": at(main, "ELAGABALUS"), "drunk": at(main, "DRUNK"), "lions2": at(main, "LIONS", 1),
    "leopards": at(main, "LEOPARDS"), "some": at(main, "SOME"), "he_served": at(main, "HE"),
    "then": at(main, "THEN"), "dropped": at(main, "DROPPED"), "glass": at(main, "GLASS"), "by": at(main, "BY"),
    "killed": at(main, "KILLED"), "and_guests": at(main, "AND", 3), "with_this": at(main, "WITH"),
    "cta": cta_offset, "hit": at(cta, "HIT"), "on_emperor": at(cta, "ON"), "duration": duration,
}
(ROOT / "artifacts/timeline.json").write_text(json.dumps(cues, indent=1))
print(json.dumps(cues, indent=1))

# ---- mix ----
music_start = 62.0
sfx = [  # (file, time, gain, trim)
    ("sfx_hit.mp3", 0.0, 0.8, 3.0),
    ("sfx_lion.mp3", cues["lions2"] - 0.05, 0.55, 3.2),
    ("sfx_clink.mp3", cues["glass"] - 0.02, 1.8, 2.5),
    ("sfx_whoosh.mp3", cues["dropped"] - 0.25, 0.6, 2.0),
    ("sfx_hit.mp3", cues["killed"], 0.9, 3.0),
    ("sfx_whoosh.mp3", cues["on_emperor"] - 0.3, 0.6, 2.0),
]
inputs = ["-i", str(A / "narration_raw.wav"), "-i", str(A / "cta_raw.wav"),
          "-ss", str(music_start), "-t", str(duration), "-i", str(A / "music_candidate.mp3")]
for f, *_ in sfx:
    inputs += ["-i", str(A / f)]
fc = [
    f"[0:a]adelay={int(NARR_OFFSET*1000)}:all=1[n]",
    f"[1:a]adelay={int(cta_offset*1000)}:all=1[c]",
    f"[n][c]amix=inputs=2:normalize=0,apad=whole_dur={duration},loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,asplit=2[v][vsc]",
    f"[2:a]aresample=48000,volume=0.22,afade=t=in:d=0.4,afade=t=out:st={duration-1.6}:d=1.6[m]",
    "[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[md]",
]
labels = []
for i, (f, t, g, trim) in enumerate(sfx):
    d = int(max(t, 0) * 1000)
    fc.append(f"[{3+i}:a]aresample=48000,atrim=0:{trim},afade=t=out:st={trim-0.6}:d=0.6,volume={g},adelay={d}:all=1[s{i}]")
    labels.append(f"[s{i}]")
fc.append(f"[v][md]{''.join(labels)}amix=inputs={2+len(sfx)}:normalize=0:duration=first,atrim=0:{duration},"
          "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[out]")
(ROOT / "public").mkdir(exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[out]", "-t", str(duration),
                "-ac", "2", "-ar", "48000", str(ROOT / "public/mix.wav")], check=True)
print("mix ok")
