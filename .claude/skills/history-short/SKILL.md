---
name: history-short
description: Make a 9:16 YouTube Short / Reel about a history story using REAL public-domain artwork (Wikimedia Commons paintings + museum photos, no AI images), an ElevenLabs narrator, SFX, music, 1-3 word pop captions and a subscribe end banner, rendered with HyperFrames. Use when the user pastes a history-shorts brief (scene prompts, loop script, editing rules, title/tags) or asks for a "history short", "dark history reel", "ancient Rome short", etc.
---

# History Short (real artwork, not AI images)

This is the house recipe for the user's recurring history Shorts channel. The first one was "Elagabalus lion dinner" (Sept 2026).
`example_short.json` and `example_UPLOAD.md` in this folder are that video's real config and upload kit.

## User preferences (standing, don't re-ask)
- **Real images only. Never use AI image generation**, even if the brief contains AI image prompts, so YouTube doesn't flag the video as AI.
  Treat the brief's `[scene]` prompts as a *shot list* to match with real paintings and sculpture photos.
- Keep the narration script **word for word**, including the "infinite loop" ending that cuts mid-sentence.
  Only fix clear factual errors, and tell the user what you changed.
  Example: Elagabalus was 14 at accession, not in 221 AD, so "In 221 AD" became "According to ancient Roman writers".
- Always add an on-screen closing banner: **"Subscribe for more such interesting videos"** with a pulsing red SUBSCRIBE button, over the last ~7 s.
  It is **on screen only, never spoken**, so the loop ending still flows back into the first line.
- Runtime: **HyperFrames** (the user chose it). Output 1080×1920, 30 fps.
- The script usually runs longer than the brief's scene timings (~160 words ≈ 69 s).
  Keep the full script and stretch the visuals to the voice length. Don't trim.

## Pipeline (what worked)
Project workspace: `projects/<kebab-id>/` (gitignored). Initialize it:
`python -c "from lib.checkpoint import init_project; init_project('<id>', title='<Title>', pipeline_type='documentary-montage')"`

1. **Setup (cloud container).**
   - `apt-get install -y ffmpeg`
   - `pip install -r requirements.txt`
   - `npx -y hyperframes@latest browser ensure`
   - Only `ELEVENLABS_API_KEY`, `PEXELS_API_KEY` and `UNSPLASH_ACCESS_KEY` have real values (plus `WIKIMEDIA_CONTACT` if the user has added it).
     The other provider keys are set but empty, so check lengths before trusting the registry.
2. **Script → `artifacts/script.txt`, then voice.**
   - Use the registry tool `elevenlabs_tts` (`registry._tools['elevenlabs_tts'].execute({...})`).
   - Voice **Brian** `nPczCjzI2devNBz1zQrb`, `eleven_multilingual_v2`, stability 0.45, speed 1.0.
   - Output to `assets/audio/narration.mp3`.
   - The user's ElevenLabs is on the **free plan** (10k chars/month, no commercial licence), so check credits first:
     `GET /v1/user/subscription`
3. **Word timings.** ElevenLabs Scribe gives the word timestamps used for captions and shot timing:
   `POST /v1/speech-to-text` with `model_id=scribe_v1`, `timestamps_granularity=word` → `artifacts/words_raw.json`
4. **Artwork.** Run `scripts/wikimedia.py search "<painting> <artist>" ...`, then
   `scripts/wikimedia.py download projects/<id> images.json`. This writes the files plus `artifacts/image_credits.json`.
   - Commons [rate limits by client identity](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits).
     Without a contact in the User-Agent, a request counts as "IP only": 10 req/min, shared by everyone on a cloud IP.
     Set `WIKIMEDIA_CONTACT` (an email) for the 200/min tier. An optional `WIKIMEDIA_ACCESS_TOKEN` (an OAuth 2.0 owner-only token) goes higher still.
     If neither is set, the script warns you. Expect 10-20 min for ~15 files then, so run downloads with `run_in_background`.
     The script is resumable. When the API keeps answering 429, it falls back to fetching straight from `upload.wikimedia.org`.
     Those entries get `license: null`, so fill them in from the `search` output.
     Don't run your own curl probes against Commons while a download is running. They use up the same rate limit.
     About 12 good images are enough for a 45 s Short, so don't block on the last few.
   - Never `pkill -f` a pattern that matches your own shell command. It kills the shell.
   - Go-to sources: 19th-century academic/Romantic painters (Alma-Tadema, Gérôme, Couture, Rivière, Delacroix, Siemiradzki, Rubens).
     Also museum photos of busts and coins, which are often CC BY-SA and need credit in the description.
   - Make 800px-wide previews (`ffmpeg -vf scale=800:-1`) and look at them with Read before choosing crops.
5. **Music + SFX.**
   - Music: `pixabay_music` tool (free, no attribution), e.g. `query="dark epic cinematic suspense", min_duration=70`.
   - SFX: ElevenLabs `POST /v1/sound-generation` with `duration_seconds` 2-5 and `prompt_influence` 0.5.
     Typical set: door slam, low lion growl, crash-and-screams chaos, deep boom.
   - Place SFX on the exact spoken word (from `words_raw.json`), not on the brief's nominal timestamps.
6. **`projects/<id>/short.json`**: shots, highlights, nametag, banner, music gap and SFX. See the format below.
   Then run `python .claude/skills/history-short/scripts/build_short.py projects/<id>`.
   That one command crops and grades every shot, mixes the audio and writes `hyperframes/index.html`.
7. **Check.** From `projects/<id>/hyperframes`:
   - `npx hyperframes lint` should show 0 errors. The "track too dense" and "nested structure" warnings are fine.
   - Run `npx hyperframes snapshot --at <~12 times> --no-end`, stack the snapshots into a contact sheet and Read it.
   - Look for bad crops, unreadable dark shots and **nudity**. Many of these paintings have nudes; crop around them or swap the shot.
8. **Render and deliver.**
   - `npx hyperframes render --quality delivery --output ../renders/final.mp4` takes about 4 min for 70 s on CPU.
   - Re-encode the upload file: `-c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 192k` (about 55 MB).
   - Measure loudness (`-af ebur128=peak=true`). The Caligula mix came out at −20 LUFS.
     If it's under about −15, remux with `volume=+NdB,alimiter=limit=0.8:level=false` (not single-pass loudnorm, which overshot to +3 dBTP).
   - SendUserFile caps at 30 MB. A 45 s Short at `-crf 21` fits (about 28 MB). Longer ones also need a 2-pass `-b:v 2800k` preview (about 25 MB).
   - Write `renders/UPLOAD.md` with the title, a description (source note plus all image credits, CC BY-SA ones by name and URL), tags,
     the AI-voice disclosure note and the free-plan licence warning.
   - `projects/` is gitignored and the cloud container is ephemeral. Tell the user to download the files.

## Editing rules baked into build_short.py
- Every shot scales 100%→108% with a slight alternating x-drift. Shots last 1-2.5 s and change on phrase boundaries.
- `chaos_window` gives hard cuts every ~0.5 s with a white flash. Alternate two or three chaos paintings.
- Captions: Anton 118px, white with a black stroke, centered, 1-3 words.
  They break on punctuation or a gap longer than 0.25 s. `highlights` phrases show as one chunk in yellow `#ffd21f` or red `#ff2a2a`.
- The grade: contrast 1.12, saturation 0.82, slightly dark and warm, plus a vignette overlay.
- Audio: voice at −16 LUFS, music at −24 LUFS then −14 dB (about 22 dB under the voice).
  The music `gap` gives a dramatic silence at the twist, and the final mix comes out around −14 LUFS.
- Nametag (Cinzel, gold) under the first bust close-up, e.g. "ELAGABALUS / EMPEROR OF ROME · 218–222 AD".

## short.json format
```json
{
 "total": 69.15,                          // = narration length + ~0.3 s
 "shots": [[0.0, "roses", 470, 246, 470], ...],   // [start_s, image_key, cx, cy, h] in 800px-preview coords
 "chaos_window": [41.0, 43.5],
 "highlights": {"lock you inside": "#ffd21f", "unhinged": "#ff2a2a"},
 "nametag": {"start": 15.2, "duration": 2.1, "title": "ELAGABALUS", "sub": "EMPEROR OF ROME · 218–222 AD"},
 "banner": {"start": 62.0, "text": "Subscribe for more such interesting videos"},
 "labels": [{"start": 0.0, "duration": 4.0, "text": "AUTHENTIC ROMAN BUST"}],  // optional small top-left Cinzel tags
 "music": {"file": "assets/music/bg.mp3", "gain_db": -14, "gap": [43.0, 45.3]},
 "sfx": [{"file": "assets/audio/sfx_door.mp3", "at": 4.4, "volume": 0.9},
         {"file": "assets/audio/sfx_chaos.mp3", "at": 41.5, "volume": 0.55, "fade_out": [3.5, 1.2]}]
}
```
The shot's `h` is the crop height in preview pixels; the width is h×9/16. A small `h` means a tight crop, which upscales and gets soft.
Keep the source crop at roughly 600 px tall or more.

## Honesty notes to pass on each time
- The narration is an AI voice. YouTube's disclosure toggle targets *realistic* synthetic content, so a narrator over paintings usually doesn't need it.
  It's the user's call.
- Monetized channel → a paid ElevenLabs plan is needed for commercial use.
- Many ancient anecdotes (e.g. the *Historia Augusta*) are unreliable. Suggest "ancient sources claim…" wording where it fits.
