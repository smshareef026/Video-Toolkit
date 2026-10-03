---
name: history-short
description: Make a 9:16 YouTube Short / Reel about a history story using REAL public-domain artwork and archival film (no AI images), found through OpenMontage's documentary-montage pipeline (CLIP-searchable corpus over Wikimedia Commons + Archive.org), with an ElevenLabs narrator, SFX, music, 1-3 word pop captions and a subscribe end banner, rendered with HyperFrames. Use when the user pastes a history-shorts brief (scene prompts, loop script, editing rules, title/tags), gives just a topic ("write the script for this short: <title>"), or asks for a "history short", "dark history reel", "ancient Rome short", "hidden city short", etc. Works for places and sites (photos) as well as artwork.
---

# History Short (real artwork, not AI images)

This is the house recipe for the user's recurring history Shorts channel. The first one was "Elagabalus lion dinner" (Sept 2026),
the second "They Found a Hidden City Under Their Living Room" (Derinkuyu, Oct 2026; photos of a place, not artwork).
`example_short.json` and `example_UPLOAD.md` in this folder are the first video's real config and upload kit.
The user often gives only a title ("write the script for this short: ..."). Then you write the script yourself to the
30-second blueprint below, stop at the `idea` gate, and carry on stage by stage.

## User preferences (standing, don't re-ask)
- **Real images only. Never use AI image generation**, even if the brief contains AI image prompts, so YouTube doesn't flag the video as AI.
  Treat the brief's `[scene]` prompts as a *shot list* to match with real paintings, sculpture photos and
  (for filmed eras) public-domain archival film, retrieved from the documentary-montage corpus.
- Keep the narration script **word for word**, including the "infinite loop" ending that cuts mid-sentence.
  Only fix clear factual errors, and tell the user what you changed.
  Example: Elagabalus was 14 at accession, not in 221 AD, so "In 221 AD" became "According to ancient Roman writers".
- **Captions are always plain white** (black stroke), never coloured highlight words. The user asked for this.
- Always add an on-screen closing banner: **"Subscribe for more History Uncovered Videos With Real Images."** with a pulsing red SUBSCRIBE button, over the last ~7 s.
  Use this exact text in every video (the user set it in Oct 2026), even if a brief proposes different banner wording.
  It is **on screen only, never spoken**, so the loop ending still flows back into the first line.
  The user's 30-second blueprint (Oct 2026) says the same: no spoken "subscribe". (On the Derinkuyu Short the user first
  asked for a spoken CTA near the end, then for an ending that doesn't cut off, then adopted the blueprint, so the latest
  rule wins. If they ask for a spoken CTA again, do it, and keep the looping cut as a spare.)
  The 7 s banner covers ~28% of a 25 s Short, including the payoff line. Offer a shorter banner (~3.5 s) if end drop-off shows up in analytics, but don't change it unasked.
- Runtime: **HyperFrames** (the user chose it). Output 1080×1920, 30 fps.
- **Default format: the 30-second blueprint** (user, Oct 2026). Scripts are **75-85 words**, voiced by Brian at **speed 1.15**
  (about 2.65 words/s, so 77 words ≈ 24 s and 85 words ≈ 29 s). The shot cadence is **a new image or crop every 1.5-2.0 s**
  (about 15-20 changes), there is **no spoken CTA**, and the ending is the seamless-loop clause. The reason the user gives:
  a viewer who is pulled into watching the start twice pushes average percentage viewed past 100%.
  Treat that as the user's strategy, not a verified fact: the tier and view-count numbers in it are unconfirmed, so say so if asked.
- Longer scripts: if the user pastes one (~160 words ≈ 69 s), keep it word for word and stretch the visuals to the voice length. Don't trim.
  State the estimated length at the `idea` stop and offer the 30 s blueprint as an alternative.

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
  Target runtime for scripts you write is **~25-30 s, 75-85 words** (see the 30-second blueprint above). Brian at speed 1.0 runs
  about 2.3 words/s; at 1.15 about 2.65. Aim for 77-85 words and check the real length once the voice exists.
  A pasted script stays word for word per the preferences above. If it runs well past 30 s, state the estimated
  length at the stop and let the user decide whether to cut.
  A script with a lot of facts tempts you to list them. Keep one twist (a detail that reverses what the viewer expects)
  and a teaser line for it early ("But the strangest part is the doors."), then pay it off before the loop clause.
- **First 2 seconds (`idea`, user rule, Oct 2026).** Open on the most startling mystery or statement, never on
  environmental context or scene-setting.
  - Weak: "An unprecedented drought just forced the river to recede..." (context first, payoff later).
  - Strong: "A 3,400-year-old lost empire just emerged from underwater..." (the shock is the first thing heard).
  - Lead with the subject plus the strangest fact, put the cause (drought, excavation, discovery) second.
    **The spoken hook must be finished within ~2 s** (user, Oct 2026: viewers decide to stay or swipe in the first 2 s).
    Example: "A city was hiding under his living room." ends at 1.7 s. A 6-second hook sentence is too slow.
  - Measured on the 46 s Derinkuyu Short: 56.4% stayed (43.6% swiped away) even with that 1.7 s hook, while average view
    duration was 77%. So the swipe decision is made on what is **seen and heard in the first second**, not on the wording.
  - When you write a script, open this way. When a pasted script opens with context, keep it word for word but
    propose a front-loaded rewrite of the first line at the `idea` stop and let the user pick.
    Check that the loop tail still flows into the new first line.
  - The first shot is the most visually startling hero image (ruins breaking the water, the bust, the twist painting), not an establishing shot.
    The first caption chunk carries the shock words.
  - **First frame: bright, high contrast, one clear subject.** The Derinkuyu Short opened on a dark green tunnel and lost
    44% in the first seconds. Pick the first image by how it looks as a thumbnail on a phone, not by how well it matches the sentence.
    Cut inside the first second (a second crop of the same image works) and use a loud sound hit on the first word.
    Show the caption from frame 1, as a chunk of the hook ("A CITY", then "UNDER HIS LIVING ROOM").
- **Seamless loop (`idea` → `compose`, user rule, Oct 2026).** No outro. The last line is an unfinished clause that
  completes *into* the opening sentence, so the replay sounds like one continuous thought and retention can pass 100%.
  - Pattern: "...which explains why" + [restart] "a 3,400-year-old lost empire just emerged from underwater...".
    Good bridges: "which explains why", "and that's exactly why", "because", "which is how".
  - Test at the `idea` stop: read the tail followed by the first sentence aloud as one sentence. It must be grammatical
    and make sense. If you change the opening (e.g. the hook-first rewrite), rewrite the tail to match.
  - No spoken outro or call to subscribe before the tail. The banner does that job on screen. If a pasted script has
    one, keep it word for word but point out at the `idea` stop that it breaks the loop and offer a version without it.
  - Edit and compose: the last shot is the first shot's image (same picture, a nearby crop) so the cut back is invisible.
    No fade to black, no music fade at the cut (leave `music.fade_out` unset; it's for the long-form cut), and
    `total` ≈ narration length + ~0.3 s so there's no dead air.
    At compose, compare the first and last frames and confirm the voice stops mid-clause.
- **Shot list (`scene_plan`).** A visual change (a new image, a new crop or a new camera move) at least every 1.5-2.0 s on the
  30 s format (2.5 s is the hard ceiling for longer scripts). Count about 15-20 changes for 25-30 s. The chaos burst
  (0.5 s hard cuts) counts as 4-5 of them.
- **Assets and crops (`assets`, `edit`).** Prefer high-contrast portraits, busts and battle or crowd scenes.
  Avoid text-heavy maps, documents and low-contrast images, which read badly on a phone.

### Setup (cloud container)
- `apt-get install -y ffmpeg`
- `make setup` (creates `.venv`, installs requirements, Remotion, Piper and warms HyperFrames). Then run everything with `.venv/bin/python`
  and `export PYTHONPATH=.` (so `lib` and `tools` import).
- `corpus_builder` also needs `torch` + `transformers` for CLIP. Not in requirements.txt. Install the CPU build:
  `.venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu && .venv/bin/python -m pip install transformers pillow`
  (use `python -m pip`; the venv has no `bin/pip` shim).
- `npx -y hyperframes@latest browser ensure`
- Only `ELEVENLABS_API_KEY`, `PEXELS_API_KEY` and `UNSPLASH_ACCESS_KEY` have real values (plus `WIKIMEDIA_CONTACT` if the user has added it).
  The other provider keys are set but empty, so check lengths before trusting the registry.
- Preflight as usual (`registry.provider_menu_summary()`). Check `corpus_builder.get_info()["source_provider_summary"]`
  lists `wikimedia` and `archive_org` as available.

### 1. `idea` → `artifacts/brief.json`
Follow `idea-director.md`, with these fixed choices from the channel:
- **Narration: yes.** The loop script, word for word, is an explicit user request.
  This overrides the pipeline's "no narration by default" rule, so record it as user-approved.
- `music_plan`: Freesound CC0 via the `freesound_music` tool with `license: "cc0"` (free, no credit needed).
  In the cloud container Pixabay returns HTTP 403 to every request (Cloudflare blocks the IP), so don't plan on `pixabay_music` there.
- `end_tag_plan: null`, with `end_tag_opt_out_reason`: "replaced by the channel's on-screen subscribe banner".
- **Runtime: HyperFrames.** The user chose it, and this Short is built by `build_short.py`.
  It doesn't use the Remotion `CinematicRenderer` or its end-tag overlay, which are why the manifest defaults to Remotion.
  Log `render_runtime_selection` with both runtimes in `options_considered`. Remotion's `rejected_because` is
  "user's standing choice is HyperFrames; build_short.py composition has no Remotion dependency".
- `era_mix`: `vintage`. `sources_allowed`: `["wikimedia", "archive_org"]`. Canvas 1080×1920, 30 fps.
- Script → `artifacts/script.txt` (only clear factual fixes, reported to the user).
- **Schema notes** (saves a failed write): `brief.schema.json` is generic and `additionalProperties: false`. Required:
  `version "1.0"`, `title`, `hook`, `key_points[]`, `tone`, `style`, `target_platform` (enum: youtube...), `target_duration_seconds`.
  Put everything documentary-specific (`thematic_question`, `music_plan`, `end_tag_plan`, `narration`, `render_runtime`, `era_mix`,
  `sources_allowed`) in `metadata`. The `decision_log` goes in the checkpoint's `artifacts` as `{"decision_log": {...}}`;
  its `category` must be from the schema enum (`render_runtime_selection`, `voice_selection`, `music_source`, ...).
  Write checkpoints with `write_checkpoint(Path("projects"), id, stage, status, {"brief": brief, "decision_log": dl},
  pipeline_type="documentary-montage", human_approval_required=True, human_approved=<bool>)`. Stage names are
  `idea, scene_plan, assets, edit, compose`. A gated stage can only be `completed` with `human_approved=True`, so only set
  that after the user has approved (their "start generating" or "approved" after you stopped counts for that stage only).

### 2. `scene_plan` → `artifacts/scene_plan.json`
Treat the brief's `[scene]` prompts as the shot list. Each becomes one slot in `metadata.slots[]`:
- `description`: a concrete visual sentence written for **CLIP ranking** of real artwork,
  e.g. "19th-century academic oil painting, Roman emperor reclining at a banquet, rose petals falling".
- `queries`: 2-3 short **Commons/Archive.org search phrases**. Name real works and artists where you know them:
  "Roses of Heliogabalus Alma-Tadema", "Gerome lion colosseum", "Elagabalus bust Capitoline".
- `preferred_sources`: `["wikimedia"]` for paintings, busts and coins.
  Add `archive_org` only for subjects that were **filmed** (roughly 1900 onward: wars, expeditions, disasters).
- Slots last 1.5-2.0 s on the 30 s format, so a 25-30 s script needs ~15-20 slots (~70 s needs ~30). Several slots can reuse one
  image with different crops, and the last slot reuses slot 1 (loop). Mark the bust close-up (nametag shot) and the twist image as `hero`.
- **Places and sites** (a ruin, a city, a cave): the corpus will be modern photographs, not paintings. Write descriptions as photos
  ("narrow carved stone tunnel, arched ceiling, warm lamp light"), query by the site name plus part ("Derinkuyu tunnel",
  "Derinkuyu stone door"), and add 2-3 context slots for the wider story (the region, a related period's fresco or manuscript).
  Wikimedia has few photos of specific interior parts (stables, kitchens, wine cellars): plan to reuse related-site images
  and say so in `metadata.rejected_picks` and to the user.

### 3. `assets` → corpus, voice, music, SFX, `artifacts/asset_manifest.json`
Use the asset director's **standard path** (corpus + CLIP retrieval).

**Voice first, in parallel with the corpus build:**
- Voice: registry tool `elevenlabs_tts` (`registry._tools['elevenlabs_tts'].execute({...})`).
  Use voice **Brian** `nPczCjzI2devNBz1zQrb`, `eleven_multilingual_v2`, stability 0.45, **speed 1.15** for the 30 s format
  (1.0 only for long pasted scripts; the tool accepts 0.7-1.2) → `assets/audio/narration.mp3`.
  The user's ElevenLabs is on the **free plan** (10k chars/month, no commercial licence), so check credits first with
  `GET /v1/user/subscription` (`character_count` / `character_limit`). One 80-word script is ~500-700 characters, and
  sound effects also draw on the allowance.
- **Don't re-voice to drop or change the last words.** Cut the existing file with ffmpeg at the end of the last wanted word plus
  ~0.3 s and a short fade (`-t <end> -af afade=t=out:st=<end-0.3>:d=0.3`), remove the dropped words from `words_raw.json`
  (keep the whole `words` list, filter on `start`), and reduce `short.json` `total`. Save the originals first.
  Re-voice only when the wording itself changes (and keep the old file as `narration_<tag>.mp3`).
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
Then, per slot, run `rank_for_slot` with `query_text` = the slot **description** (the parameter is `query_text`, not `slot_description`) plus `kind: "image"`.
**Scores don't discriminate**: for photos they sit around 0.3-0.45 for everything, and the top 5 are often near-duplicates of one
image. So build labelled contact sheets of the whole corpus and choose by eye:
`.venv/bin/python .claude/skills/history-short/scripts/corpus_sheets.py <id>` (20 tiles per sheet, each labelled with the clip id and
Commons file title; open every sheet with Read). The corpus also contains junk the queries pulled in (subway stations, a London
memorial): ignore it.
Use `kind: "video"` with `motion_min: 1.5` for film slots.
Use `tag_weight: 0.4`, since Commons titles and descriptions name the painting and artist, which helps.
Choose from the top 3-5 by judgement, and open the thumbnails with Read:
- Right subject and era. No modern reenactment photos or AI-looking art. Avoid modern tourists in the frame.
- **No nudity.** Many of these paintings have nudes. Crop around them or pick another.
- Has a region that survives a 9:16 crop.
- **Bright and readable on a phone.** Skip near-black shots (a shaft photo that is 90% black), blurry close-ups of featureless rock
  and smooth stone surfaces (a close crop of a stone door face renders as a blank orange/grey wall: crop wide enough to show
  the door's edge, its hole, the groove or the sign). Prefer a clear subject with an edge or light source.
- **Check the licence text, not just the tag.** Run `.venv/bin/python .claude/skills/history-short/scripts/check_credits.py <id>` after
  materializing the picks. It flags licences that aren't CC0 / public domain / CC BY(-SA) and long or restrictive author notes.
  (One Commons author's note said their CC BY-SA photos must not be used in social media; both pictures were swapped out.
  Same-author alternatives and other photos of the same thing are usually available.) Replace anything flagged and re-run
  `from_corpus.py`.
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
- Music: `freesound_music` tool with `license: "cc0"`, e.g. `query="dark ambient drone cinematic", min_duration=50, max_duration=300` → `assets/music/bg.mp3`.
  The tool returns only the top hit per call, so try 3-4 queries into `cand_*.mp3` and choose. Check the returned `license`, `name` and `tags`:
  skip horror tracks with jump scares, and anything with nature sounds (a "cave scape" track had birds and waves).
  Measure candidates before choosing: `ffmpeg -i f.mp3 -af silencedetect=n=-40dB:d=2 -f null -` (no long silent intros) and
  `ebur128` (steady loudness; LRA under ~4 LU is steady under a voice). Queries that worked: "suspense dark ambient pad",
  "dark cinematic drone tension". Delete the unused candidates.
  `pixabay_music` works only off-cloud. Freesound previews are 128 kbps MP3, which is fine under a voice.
- SFX: ElevenLabs `POST /v1/sound-generation` with `duration_seconds` 2-5 and `prompt_influence` 0.5.
  A typical set is door slam, low lion growl, crash-and-screams chaos and deep boom. For a place story: low rumble, stone grinding,
  deep boom, air whoosh (2-3 s each; four effects cost well under 300 characters of the allowance).
  Place them on the exact spoken words from `words_raw.json`: rumble on word 1, the grind on the twist noun, the boom on the last
  words of the payoff line, with a short music `gap` right before that line.

### 4. `edit` → `projects/<id>/short.json` + `artifacts/edit_decisions.json`
`short.json` is this Short's timeline (format below). Shots change on phrase boundaries from `words_raw.json`,
and SFX land on the exact spoken word, not on the brief's nominal timestamps.
Also write `edit_decisions.json` per `edit-director.md`, with `renderer_family: "documentary-montage"`,
one cut per shot (clip_id, in/out and a one-line reason), the music config, and `end_tag: null` with the opt-out note.
Required keys are `version`, `cuts[]` (each `id`, `source`, `in_seconds`, `out_seconds`) and `render_runtime`; put the rest in `metadata`.

**Timeline recipe for the 30 s format** (from the Derinkuyu Short, ~25 s, 20 shots):
- 0.0 hero image wide, ~0.95 a tight crop of the same image, then a new image every 1.4-2.0 s on phrase boundaries from `words_raw.json`.
- Crops: landscape previews (800×600) use `h` = 600 (full height) and a `cx` you choose; portrait previews can use `h` up to the
  image height. Read the previews first and pick `cx, cy` from where the subject actually is.
- Chaos burst (`chaos_window`, ~2 s) on the twist line, with 4-5 shots of 0.5 s each from 2-3 different door/twist images
  (not the same blank crop).
- `labels` (small top-left tags, ~2-2.8 s each) with 4-5 facts timed to the narration: year/place, depth, capacity, the twist.
- `highlights`: 4-6 shock phrases that should stay on one caption chunk ("a city", "living room", "never got in").
- `banner.start` = `total` - 7. `music.gap` is a ~0.5 s silence just before the payoff line. Leave `music.fade_out` unset.
- Last shot = shot 1's image with a nearby crop (loop).

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
   This review can't be automated, so never skip it. The 12-frame sheet samples only a few instants, so for the chaos burst and
   the first 2 seconds also check the frames at the cut times (`ffmpeg -ss <t> -i renders/upload.mp4 -frames:v 1 f.jpg`).
   Fix blank/dark crops by changing `[cx, cy, h]` or the image, then re-run `--check-only` (about 20 s) before the real render.
2. **Render.** The full run renders at delivery quality (about 4 min for 70 s on CPU) → `renders/final.mp4`.
   It re-encodes `renders/upload.mp4` (`crf 19`, `+faststart`, AAC 192k) and measures loudness.
   Under −15 LUFS it remuxes with `volume=+NdB,alimiter=limit=0.8:level=false` to about −14 LUFS
   (not single-pass loudnorm, which overshot to +3 dBTP).
   `--preview` also writes a 2-pass `renders/preview.mp4` under 30 MB for SendUserFile, or skips it when the upload already fits.
   `--draft` does a quick draft render only. `--no-mix` keeps the existing audio mix.
   Run the render with `nohup ... > render.log &` and wait with `until grep -qE "^done:|failed|Traceback" render.log; do sleep 15; done`
   in a background command. Don't wait with `pgrep -f <script>`: the waiting shell's own command line matches the pattern, so it never exits.
   A 25 s Short renders in ~2 min and a 46 s one in ~3-4 min on CPU. Narration changes need a full re-run without `--no-mix`.
   Before delivering a loop cut, extract frame 0 and the frame near the end: they must be the same picture, and the voice must stop mid-clause.
3. **Deliver.**
   - Write `render_report.json` with `music_mixed: true`, `end_tag_rendered: false` plus the banner opt-out note,
     and `render_runtime: "hyperframes"`.
   - Write `renders/UPLOAD.md` with the title, a description (source note plus all credits from `image_credits.json`,
     CC BY-SA ones by name and URL), tags, the AI-voice disclosure note and the free-plan licence warning.
     Also give the user, in chat: **3 title options** (specific and story-like, e.g. "They Found a Hidden City Under Their Living Room #shorts"),
     the description (hook line, 2-sentence story, an "accounts vary" line when sources disagree, the on-banner subscribe line, the
     "images are real photographs, narration is an AI voice" line, 3-5 hashtags, music credit), a **pinned comment** (an either/or or
     theory question such as "What do you think they were trying to lock out?"), and a comma-separated tag list (put the proper-noun
     spelling people search for in the title and tags). Hidden tags matter little for Shorts; title and the first 2 seconds matter most.
   - Keep earlier cuts as `renders/upload_<tag>.mp4` (e.g. `upload_46s.mp4`, `upload_25s_loop.mp4`) so the user can compare versions,
     and update UPLOAD.md for the cut that is the current `upload.mp4`.
   - Send the user `preview.mp4` (or `upload.mp4` when it's under 30 MB) with SendUserFile.
   - `projects/` is gitignored and the cloud container is ephemeral. Tell the user to download the files.

### Optional: 16:9 long-form version
YouTube treats any vertical video up to 3 minutes as a Short. For long-form treatment (regular pre-roll ads),
render the same edit at 1920×1080. It reuses `short.json`, the audio mix and the captions:
```bash
python .claude/skills/history-short/scripts/compile.py <id> --landscape --check-only --skip-ingest
python .claude/skills/history-short/scripts/compile.py <id> --landscape --skip-ingest --no-mix --preview
```
- Output goes to `hyperframes-16x9/` and `renders/{final,upload,preview}_16x9.mp4`.
- Each crop keeps its vertical framing and widens to 16:9 around the same centre. Upright images (busts, statues)
  that can't fill the width sit centred over a blurred, darkened copy of themselves.
- **Widening can bring back what a 9:16 crop left out** (a nude figure beside the subject, say).
  Review every wide crop, not just the 12-frame contact sheet: `hyperframes-16x9/shots/*.jpg`.
  Fix problems with `"crops_16x9": {"<image or shot index>": [cx, cy, h]}` in `short.json`.
- Captions sit in the lower third, labels top-left, and the subscribe card top-right.
- Long-form doesn't loop, so the Short's loop ending sounds cut off there. For a proper ending, voice only the new tail
  (ElevenLabs `previous_text` = the script before it, same voice settings) and splice it after the last full sentence
  in a natural pause. Re-run Scribe on the spliced file, then write `short_16x9.json` with its own `narration`,
  `words`, `total`, closing shots, banner start and `music.fade_out`. `--landscape` uses `short_16x9.json` when it
  exists; the Short keeps `short.json` and its loop.
- Long-form needs a custom 1280×720 thumbnail: public-domain art plus a short headline, never show stills.
  Build it as a one-frame HyperFrames page and `npx hyperframes snapshot --describe false` it.
- Any manual `npx hyperframes snapshot` call needs `--describe false`. Without it, the CLI sends the frames to Gemini
  whenever `GEMINI_API_KEY` is set. `compile.py` already passes it.

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
 "banner": {"start": 62.0, "text": "Subscribe for more History Uncovered Videos With Real Images."},
 "labels": [{"start": 0.0, "duration": 4.0, "text": "AUTHENTIC ROMAN BUST"}],  // optional small top-left Cinzel tags
 "music": {"file": "assets/music/bg.mp3", "gain_db": -14, "gap": [43.0, 45.3]},
 "sfx": [{"file": "assets/audio/sfx_door.mp3", "at": 4.4, "volume": 0.9},
         {"file": "assets/audio/sfx_chaos.mp3", "at": 41.5, "volume": 0.55, "fade_out": [3.5, 1.2]}]
}
```
The shot's `h` is the crop height in preview pixels; the width is h×9/16. A small `h` means a tight crop, which upscales and gets soft.
Keep the source crop at roughly 600 px tall or more.

## Reading the first analytics (what we have so far)
The Derinkuyu Short (46 s cut, spoken CTA, 2 hours, 1,770 views): 56.4% stayed vs swiped away, average view duration 35 s (77.3%),
59 likes, +7 subscribers, 1 comment. Retention once people stay is strong; the first-seconds swipe-away is the problem, and
comments are low. The follow-ups: a brighter first frame with a caption from frame 1, a 25 s loop cut, and a pinned theory question.
Later reading (same 46 s cut, more views): 3,067 views, 59.3% stayed, average view duration 39 s (84.9%), 85 likes, 1 share, few comments.
It out-pulled the channel's other recent Shorts in views (about 1.6k each), and the stayed rate improved (56.4% to 59.3%) as it reached more people.
Stayed ratios the user's best Shorts reach are ~65-70%, which is the target to beat. A 46 s Short already holds ~85% of viewers, so length wasn't the problem:
the opening second is. The 25-30 s loop format is a test of whether the loop pushes average viewed past 100%; don't claim it's better until the numbers say so.
Two hours is a small sample, so say so. When the user pastes analytics (or another tool's feedback), first check it is about this video:
one pasted note mentioned a "Mesopotamian script" and "receding river" that belong to a different Short.
Don't copy a suggested hook that is longer than the 2 s rule. Log new results here so the recipe keeps improving.

## Honesty notes to pass on each time
- Motion and particles make the Short look better. They don't make it exempt from YouTube's "reused/repetitive content"
  policy, which is a review of whether a video adds original value. What qualifies these Shorts is their original
  script, narration and editing. Don't tell the user the effects get around YouTube's review.
- The narration is an AI voice. YouTube's disclosure toggle targets *realistic* synthetic content, so a narrator over paintings usually doesn't need it.
  It's the user's call.
- Monetized channel → a paid ElevenLabs plan is needed for commercial use.
- Many ancient anecdotes (e.g. the *Historia Augusta*) are unreliable. Suggest "ancient sources claim…" wording where it fits.
- Discovery stories and figures for sites (who found it, depth, capacity, dates) vary between sources. Use "roughly", "up to", and
  "historians still argue" in the script, and put an "accounts vary" line in the description.
- The retention-tier / 100% / seed-pool numbers in the user's 30 s blueprint are unverified. Say so rather than promising reach or subscribers.
- Don't count the images' "real photo" status as a licence: run `check_credits.py` and list CC BY-SA credits in the description.
