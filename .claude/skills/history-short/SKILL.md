---
name: history-short
description: Make a 9:16 YouTube Short / Reel about a history story using REAL public-domain artwork and archival film (no AI images), found through OpenMontage's documentary-montage pipeline (CLIP-searchable corpus over Wikimedia Commons + Archive.org), with an ElevenLabs narrator, SFX, music, 1-3 word pop captions and a subscribe end banner, rendered with HyperFrames. Use when the user pastes a history-shorts brief (scene prompts, loop script, editing rules, title/tags) or asks for a "history short", "dark history reel", "ancient Rome short", etc.
---

# History Short (real artwork, not AI images)

This is the house recipe for the user's recurring history Shorts channel. The first one was "Elagabalus lion dinner" (Sept 2026).
`example_short.json` and `example_UPLOAD.md` in this folder are that video's real config and upload kit.

## User preferences (standing, don't re-ask)
- **Real images only. Never use AI image generation**, even if the brief contains AI image prompts, so YouTube doesn't flag the video as AI.
  Treat the brief's `[scene]` prompts as a *shot list* to match with real paintings, sculpture photos and
  (for filmed eras) public-domain archival film, retrieved from the documentary-montage corpus.
- Keep the narration script **word for word**, including the "infinite loop" ending that cuts mid-sentence.
  Only fix clear factual errors, and tell the user what you changed.
  Example: Elagabalus was 14 at accession, not in 221 AD, so "In 221 AD" became "According to ancient Roman writers".
- **Captions are always plain white** (black stroke), never coloured highlight words. The user asked for this.
- Always add an on-screen closing banner: **"Subscribe for more such interesting videos"** with a pulsing red SUBSCRIBE button, over the last ~7 s.
  It is **on screen only, never spoken**, so the loop ending still flows back into the first line.
- Runtime: **HyperFrames** (the user chose it). Output 1080×1920, 30 fps.
- The script usually runs longer than the brief's scene timings (~160 words ≈ 69 s).
  Keep the full script and stretch the visuals to the voice length. Don't trim.

## Pipeline: `documentary-montage`
This skill runs on OpenMontage's **Documentary Montage** pipeline (`pipeline_defs/documentary-montage.yaml`).
Artwork and archival film come from its **CLIP-searchable corpus**: `corpus_builder` fans each query out to
**Wikimedia Commons** (paintings, museum photos of busts and coins) and **Archive.org** (public-domain film),
downloads and embeds every candidate, and `clip_search` ranks them against each shot's description.
Don't hand-pick files by title or call the stock adapters directly. Go through the two tools.

Per Rule Zero, read `skills/pipelines/documentary-montage/executive-producer.md` and each stage's director
skill before that stage. The sections below are this channel's **overrides** to those directors.

Project workspace: `projects/<kebab-id>/` (gitignored). Initialize it and open the board:
`python -c "from lib.checkpoint import init_project; init_project('<id>', title='<Title>', pipeline_type='documentary-montage')"`
then `python -m backlot open <id>`.

**Gates.** `idea`, `scene_plan`, `assets` and `edit` gate on human approval in this manifest.
At each one, write the checkpoint with `status="awaiting_human"`, give a short summary and end the turn.
Keep the summaries brief: the standing preferences above are already approved, so don't re-ask them.

**What to check at each stop** (the user's channel strategy):
- **Script (`idea`).** The hook in the first line must grab: historical irony, a bizarre death or an ancient scandal.
  Target runtime is **~47 s**. Brian runs about 2.3 words/s (160 words ≈ 69 s), so 47 s ≈ 110 words.
  When you write or rework a script, aim for that. A pasted script stays word for word per the preferences above.
  If it runs well past 47 s, state the estimated length at the stop and let the user decide whether to cut.
- **Shot list (`scene_plan`).** A visual change (a new image, a new crop or a new camera move) at least every 2-2.5 s.
  Nothing holds longer than 2.5 s.
- **Assets and crops (`assets`, `edit`).** Prefer high-contrast portraits, busts and battle or crowd scenes.
  Avoid text-heavy maps, documents and low-contrast images, which read badly on a phone.

### Setup (cloud container)
- `apt-get install -y ffmpeg`
- `pip install -r requirements.txt`. `corpus_builder` also needs `torch` + `transformers` for CLIP (CPU is fine).
- `npx -y hyperframes@latest browser ensure`
- Only `ELEVENLABS_API_KEY`, `PEXELS_API_KEY` and `UNSPLASH_ACCESS_KEY` have real values (plus `WIKIMEDIA_CONTACT` if the user has added it).
  The other provider keys are set but empty, so check lengths before trusting the registry.
- Preflight as usual (`registry.provider_menu_summary()`). Check `corpus_builder.get_info()["source_provider_summary"]`
  lists `wikimedia` and `archive_org` as available.

### 1. `idea` → `artifacts/brief.json`
Follow `idea-director.md`, with these fixed choices from the channel:
- **Narration: yes.** The loop script, word for word, is an explicit user request.
  This overrides the pipeline's "no narration by default" rule, so record it as user-approved.
- `music_plan`: `generated` via the `pixabay_music` tool (free, no attribution).
- `end_tag_plan: null`, with `end_tag_opt_out_reason`: "replaced by the channel's on-screen subscribe banner".
- **Runtime: HyperFrames.** The user chose it, and this Short is built by `build_short.py`.
  It doesn't use the Remotion `CinematicRenderer` or its end-tag overlay, which are why the manifest defaults to Remotion.
  Log `render_runtime_selection` with both runtimes in `options_considered`. Remotion's `rejected_because` is
  "user's standing choice is HyperFrames; build_short.py composition has no Remotion dependency".
- `era_mix`: `vintage`. `sources_allowed`: `["wikimedia", "archive_org"]`. Canvas 1080×1920, 30 fps.
- Script → `artifacts/script.txt` (only clear factual fixes, reported to the user).

### 2. `scene_plan` → `artifacts/scene_plan.json`
Treat the brief's `[scene]` prompts as the shot list. Each becomes one slot in `metadata.slots[]`:
- `description`: a concrete visual sentence written for **CLIP ranking** of real artwork,
  e.g. "19th-century academic oil painting, Roman emperor reclining at a banquet, rose petals falling".
- `queries`: 2-3 short **Commons/Archive.org search phrases**. Name real works and artists where you know them:
  "Roses of Heliogabalus Alma-Tadema", "Gerome lion colosseum", "Elagabalus bust Capitoline".
- `preferred_sources`: `["wikimedia"]` for paintings, busts and coins.
  Add `archive_org` only for subjects that were **filmed** (roughly 1900 onward: wars, expeditions, disasters).
- Slots last 1-2.5 s, so a ~47 s script needs ~20-25 slots (~70 s needs ~25-35). Several slots can reuse one artwork with different crops.
  Mark the bust close-up (nametag shot) and the twist image as `hero`.

### 3. `assets` → corpus, voice, music, SFX, `artifacts/asset_manifest.json`
Use the asset director's **standard path** (corpus + CLIP retrieval).

**Voice first, in parallel with the corpus build:**
- Voice: registry tool `elevenlabs_tts` (`registry._tools['elevenlabs_tts'].execute({...})`).
  Use voice **Brian** `nPczCjzI2devNBz1zQrb`, `eleven_multilingual_v2`, stability 0.45, speed 1.0 → `assets/audio/narration.mp3`.
  The user's ElevenLabs is on the **free plan** (10k chars/month, no commercial licence), so check credits first with
  `GET /v1/user/subscription`.
- Word timings: ElevenLabs Scribe, `POST /v1/speech-to-text` with `model_id=scribe_v1`,
  `timestamps_granularity=word` → `artifacts/words_raw.json`. They drive captions, shot timing and SFX placement.

**Corpus build.** Run `corpus_builder` with `run_in_background`, because Commons is rate limited:
```python
registry._tools["corpus_builder"].execute({
    "corpus_dir": "projects/<id>/corpus",
    "queries": [{"query": q, "kind": "image", "per_source": 6} for q in painting_queries],
    "sources": ["wikimedia"],
    "filters": {"min_width": 1200},
    "max_new_clips": 150,
})
# Only if a slot wants archival film: a separate archive_org batch,
# {"kind": "video", "per_source": 4}, "sources": ["archive_org"], filters {"min_duration": 4}.
```
- Commons [rate limits by client identity](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits).
  The adapter adds `WIKIMEDIA_CONTACT` (an email) to its User-Agent for the 200 req/min tier, and sends
  `WIKIMEDIA_ACCESS_TOKEN` (optional OAuth 2.0 owner-only token) to the API only.
  It honours `Retry-After` on 429s. Without a contact you're in the shared 10 req/min IP-only tier, so expect a slow build.
  If it warns the token was rejected (401), the value is probably the OAuth client key or secret, not the owner-only
  access token (a JWT with two dots). The build carries on without the token, so tell the user once.
- Large Commons images come down as 1920 px thumbnails, not the 100 MB+ museum TIFF originals.
- The corpus is append-only and resumable. Re-running skips clips it already has.
- Don't run your own curl probes against Commons while a build runs. They use up the same rate limit.
- Never `pkill -f` a pattern that matches your own shell command. It kills the shell.

**Pick per slot.** Run `clip_search` `stats` first (aim for 5-8× the unique-artwork count).
Then, per slot, run `rank_for_slot` with the slot **description** plus `kind: "image"`.
Use `kind: "video"` with `motion_min: 1.5` for film slots.
Use `tag_weight: 0.4`, since Commons titles and descriptions name the painting and artist, which helps.
Choose from the top 3-5 by judgement, and open the thumbnails with Read:
- Right subject and era. No modern reenactment photos or AI-looking art.
- **No nudity.** Many of these paintings have nudes. Crop around them or pick another.
- Has a region that survives a 9:16 crop.
- Score under ~0.22 means grow the corpus with better queries (named works, artists, museum + object).
  Two growth passes, then tell the user the shot has no good open-licence match.
- Log passes in `metadata.rejected_picks`.

Go-to painters: Alma-Tadema, Gérôme, Couture, Rivière, Delacroix, Siemiradzki, Rubens.
Museum photos of busts and coins are often CC BY-SA and need credit.

**Materialize the picks** by writing `projects/<id>/picks.json` (`{"<shot_key>": "<clip_id>"}`,
or `{"clip": id, "in": 12.5, "slot": "slot_07"}` for a film clip), then:
`python .claude/skills/history-short/scripts/from_corpus.py projects/<id> projects/<id>/picks.json`
- It writes `assets/images/<key>.jpg` or `assets/video/<key>.mp4`, plus an 800 px preview in `assets/previews/<key>.jpg`.
  Crop coordinates are in that preview space. Read the previews before choosing crops.
- It also writes `artifacts/image_credits.json` (licence + artist + page for every file) and adds one
  `asset_manifest.json` entry per pick. Entries already there, such as narration, music and SFX, are kept.

**Music + SFX** (add them to `asset_manifest.json` as `music` / `sfx` entries):
- Music: `pixabay_music` tool, e.g. `query="dark epic cinematic suspense", min_duration=70` → `assets/music/bg.mp3`.
- SFX: ElevenLabs `POST /v1/sound-generation` with `duration_seconds` 2-5 and `prompt_influence` 0.5.
  A typical set is door slam, low lion growl, crash-and-screams chaos and deep boom.

### 4. `edit` → `projects/<id>/short.json` + `artifacts/edit_decisions.json`
`short.json` is this Short's timeline (format below). Shots change on phrase boundaries from `words_raw.json`,
and SFX land on the exact spoken word, not on the brief's nominal timestamps.
Also write `edit_decisions.json` per `edit-director.md`, with `renderer_family: "documentary-montage"`,
one cut per shot (clip_id, in/out and a one-line reason), the music config, and `end_tag: null` with the opt-out note.

### 5. `compose` → `renders/upload.mp4` + `artifacts/render_report.json`
Everything after the edit is one command, `scripts/compile.py`:
```bash
python .claude/skills/history-short/scripts/compile.py <id> --check-only   # ingest + build + lint + snapshots
python .claude/skills/history-short/scripts/compile.py <id> --skip-ingest --preview   # render + encode
```
1. **Check first.** `--check-only` runs `from_corpus.py` (when `picks.json` exists), `build_short.py` and `hyperframes lint`.
   It stops on any lint error; the "track too dense" and "nested structure" warnings are fine.
   Then it takes 12 evenly spaced snapshots and prints the contact-sheet paths.
   Read the sheets and look for bad crops, unreadable dark shots and nudity. Fix `short.json` or `picks.json`, then re-run.
   This review can't be automated, so never skip it.
2. **Render.** The full run renders at delivery quality (about 4 min for 70 s on CPU) → `renders/final.mp4`.
   It re-encodes `renders/upload.mp4` (`crf 19`, `+faststart`, AAC 192k) and measures loudness.
   Under −15 LUFS it remuxes with `volume=+NdB,alimiter=limit=0.8:level=false` to about −14 LUFS
   (not single-pass loudnorm, which overshot to +3 dBTP).
   `--preview` also writes a 2-pass `renders/preview.mp4` under 30 MB for SendUserFile, or skips it when the upload already fits.
   `--draft` does a quick draft render only. `--no-mix` keeps the existing audio mix.
3. **Deliver.**
   - Write `render_report.json` with `music_mixed: true`, `end_tag_rendered: false` plus the banner opt-out note,
     and `render_runtime: "hyperframes"`.
   - Write `renders/UPLOAD.md` with the title, a description (source note plus all credits from `image_credits.json`,
     CC BY-SA ones by name and URL), tags, the AI-voice disclosure note and the free-plan licence warning.
   - `projects/` is gitignored and the cloud container is ephemeral. Tell the user to download the files.

## Editing rules baked into build_short.py
- Every shot gets a camera move, rotating through push-in, pan left, pull-out, tilt up, push-in, pan right, pull-out
  and tilt down, so no move repeats back to back. Pans and tilts hold a 1.1 scale so no frame edge shows.
  Override a shot with `motion.moves` (e.g. a slow push-in on the nametag bust) and scale everything with `motion.intensity`.
  Shots last 1-2.5 s and change on phrase boundaries.
- A seeded particle layer (`dust` by default, `embers` for fire/battle stories, `"particles": false` to turn it off)
  drifts over every shot. The particles are plain solid dots: blur or gradient CSS on ~40 elements makes HyperFrames
  capture black frames.
- `chaos_window` gives hard cuts every ~0.5 s with a white flash. Alternate two or three chaos paintings.
- Captions: Anton 118px, white with a black stroke, centered, 1-3 words.
  They break on punctuation or a gap longer than 0.25 s. `highlights` phrases show as one chunk, still in white.
- The grade: contrast 1.12, saturation 0.82, slightly dark and warm, plus a vignette overlay.
- Audio: voice at −16 LUFS, music at −24 LUFS then −14 dB (about 22 dB under the voice).
  The music `gap` gives a dramatic silence at the twist, and the final mix comes out around −14 LUFS.
- Nametag (Cinzel, gold) under the first bust close-up, e.g. "ELAGABALUS / EMPEROR OF ROME · 218–222 AD".

## short.json format
```json
{
 "total": 69.15,                          // = narration length + ~0.3 s
 "shots": [[0.0, "roses", 470, 246, 470], ...],   // [start_s, key, cx, cy, h] in 800px-preview coords
                                          // film shot: [start_s, key, cx, cy, h, in_s] (key in assets/video/)
 "chaos_window": [41.0, 43.5],
 "motion": {"moves": {"4": "push_in"}, "intensity": 1.0},   // optional; shot index -> push_in|pull_out|pan_left|pan_right|tilt_up|tilt_down
 "particles": {"style": "dust", "count": 36, "opacity": 1.0},  // optional; or "embers", or false
 "highlights": {"lock you inside": "", "unhinged": ""},   // phrases kept as one caption chunk; the value is ignored
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
- Motion and particles make the Short look better. They don't make it exempt from YouTube's "reused/repetitive content"
  policy, which is a review of whether a video adds original value. What qualifies these Shorts is their original
  script, narration and editing. Don't tell the user the effects get around YouTube's review.
- The narration is an AI voice. YouTube's disclosure toggle targets *realistic* synthetic content, so a narrator over paintings usually doesn't need it.
  It's the user's call.
- Monetized channel → a paid ElevenLabs plan is needed for commercial use.
- Many ancient anecdotes (e.g. the *Historia Augusta*) are unreliable. Suggest "ancient sources claim…" wording where it fits.
