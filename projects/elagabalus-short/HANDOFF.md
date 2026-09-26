# Elagabalus Short — handoff

Status: **v3 final rendered (42.9s, ElevenLabs Daniel)**. `renders/elagabalus_short_share.mp4` (28 MB, 1080×1920)
+ `renders/elagabalus_short.srt`. The full-quality crf-18 render is regenerable with `scripts/render.py`
(not committed, 82 MB).

## v3 notes
- Voice: ElevenLabs Daniel `onwK4e9ZLuTAKqWW03F9`, `eleven_multilingual_v2`, stability 0.55 / similarity 0.85 /
  style 0.2 / speed 1.12 (free tier: mp3_44100_128 only). Sentence-end pauses trimmed to 0.38s
  (`narration_raw.mp3` / `cta_raw.mp3` are the untrimmed takes).
- `scripts/build_timeline.py` regenerates captions.ts/json/srt, `artifacts/timeline.json` (cut cues) and
  `public/mix.wav` (−14 LUFS, −1.5 dBTP) from the transcripts. Shot times in `Short.tsx` come from timeline.json.
- `scripts/render.py [scale] [out]` renders via `video_compose` atelier mode.

## Decisions (approved by user)
- Pipeline: cinematic · runtime: Remotion · composition mode: atelier (`composition/`)
- Visuals: real public-domain art only (see `art-direction.md` for sources) — no AI imagery
- Voice: ElevenLabs Daniel (replaces Piper en_US-ryan-high)
- SFX: Pixabay (lion @ "lions", clink @ "glass", whoosh @ "dropped" and @ Caligula cut, hits @ 0s and "killed")
- Music: "Dark Tension" — AtlasAudio (Pixabay), window 62s→104.4s, ducked under voice
- CTA appended at end (loop no longer seamless — user's choice)
- Loudness target −14 LUFS, TP −1.5

## Script
Main (0–32s):
> This Roman emperor let lions loose at his dinner parties... just to watch his guests panic.
> Elagabalus became emperor at fourteen. Drunk guests would wake up to lions and leopards lying
> next to them. Some reportedly died of fright. He served them fake feasts made of wax and glass,
> and expected them to keep eating. Then he dropped so many flower petals from the ceiling, that
> guests were buried alive under them. By eighteen, his own guards had killed him. And the guests
> who survived? They still had to come to dinner... with this Roman emperor

CTA (after a ~0.5s beat):
> I'm covering history's most chaotic rulers all week. Hit subscribe so you don't miss tomorrow's
> video on the emperor who tried to make his horse a politician.

## Re-render steps (new session with ELEVENLABS_API_KEY set)
1. `pip install -r requirements.txt faster-whisper`, `apt-get install -y ffmpeg`, `cd remotion-composer && npm install`
2. `elevenlabs_tts` → `assets/audio/narration_raw.wav` and `assets/audio/cta_raw.wav`
   (voice_id `onwK4e9ZLuTAKqWW03F9`; read `.agents/skills/elevenlabs` first).
3. `transcriber` (model_size small) on both → word timestamps.
4. Rebuild `public/mix.wav` — narration at +0.15s, CTA ~0.5s after narration ends; move SFX
   delays to the new word times; music window 62s→; loudnorm −14.
5. Regenerate `composition/captions.ts` from the transcripts (script text wins over ASR spelling,
   e.g. "glass", "fourteen", "eighteen"; last main word = "EMPEROR—").
6. Retime `SHOTS` in `composition/Short.tsx` to the new word times (cuts are on words: "lions",
   "leopards", "Some", "He served", "Then he dropped", "By eighteen", "And the guests",
   "with this", CTA start, "Hit subscribe", "on the emperor"); update `DURATION_S` / `LOOP_END`.
7. `video_compose` render, `composition_mode: "atelier"`, entry `projects/elagabalus-short/composition/index.tsx`,
   composition `ElagabalusShort`, `public_dir: projects/elagabalus-short/public`, crf 18.
   Keep under 45s; make a ≤30 MB copy for sharing; regenerate the .srt.
