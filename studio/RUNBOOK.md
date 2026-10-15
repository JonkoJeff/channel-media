# Daily run: Crazy Facts channel machine

You run unattended, once a day. All video content is in English. Use the ponytail skill: smallest complete change, reuse what exists. A new video is a new JSON file, never new code unless something is broken.

- Repo `JonkoJeff/channel-media` (public). Studio: `studio/`. Video files for Metricool: branch `media`, folder `files/` (via `studio/publish.sh`).
- Metricool brand `2266272`, timezone Europe/Amsterdam. YouTube channel `UCynthMQNy9uDsuHcewQDERg`.
- Links of published videos: Metricool `getScheduledPosts` (brand 2266272, Europe/Amsterdam, a date range around the publish date, `extendedRange: true`). A published post has `providers[0].status: "PUBLISHED"` and `publicUrl` (the YouTube link). The YouTube RSS feed and watch pages block WebFetch, so don't use them.

## YouTube route (check first)
- If `studio/yt/APPROVED` exists (Google approved the API audit): **all YouTube uploads go through our own uploader**, no post limit. Append items to `studio/yt/queue.json` (`{id, file, thumb, title, description, tags, publish_at (UTC ISO, e.g. 17:00 Amsterdam = 15:00Z in summer, 16:00Z in winter), short, status: "pending"}`) and push; GitHub Actions uploads each item within 26 h of its `publish_at`, max 8 per run (daily at 06:30 UTC), and writes back `video_id`. Max 8 uploads a day per channel (long + Shorts together). If a run reports "daily upload limit reached", lower to 5 a day for 2 weeks and say so in the report. Rhythm: one long 2.5 h video every day at 17:00; Shorts (from then on) up to 7 a day at 08:00, 10:00, 12:00, 14:00, 19:00, 21:00 and 23:00 (Amsterdam), from the 12 Shorts per video plus the back catalog (best performers first, never a segment twice, never 2 in a row from the same video). Items in `studio/queue.json` with status `later` go back into the rotation. Metricool then only posts Shorts to TikTok/Instagram (if connected), within the 20-post budget below.
- If it does not exist yet: uploads through our own uploader stay private, so keep using Metricool for YouTube with the budget below.

## Post budget (Metricool free plan: 20 posts per calendar month)
- Count every post in `getScheduledPosts` whose publication date is in that month, any status. One Metricool post counts once, however many networks it goes to.
- Until approval, all slots go to the daily long videos (no Shorts). Shorts only use what is left: `free = 20 - counted - reserved`. If `free <= 0`, no Short that month.
- Every Short is one post to every connected network at once (YouTube Short + Instagram Reel + TikTok), so each slot gets the most reach.
- If the user upgrades the plan, they will say so; then this section goes away.

## A. Every day: link and schedule due Shorts (≈5 min)
Order of a run: A, then C, then B (every day). Until `studio/yt/APPROVED` exists, Part A is skipped (no Shorts).
1. Read `studio/queue.json`. Take items with `status: "pending"` and `due` today or earlier.
2. For each item, find the long video whose title equals `long_title` in `getScheduledPosts` with status PUBLISHED and take its `publicUrl`. Not published yet: leave the item pending, retry tomorrow.
3. Check the post budget for the month of `due`. No free slot: leave it pending and set `due` to the 1st of the next month at 12:00. Max 1 Short per day.
4. On a match with a free slot, Metricool `createScheduledPost` (brand 2266272, `autoPublish: true`):
   - date = `due` (Europe/Amsterdam). If that time has passed or is less than 20 min away, use now + 30 min.
   - media = [`file`], providers: youtube, plus instagram and tiktok if `getBrandSettings` shows them connected. `youtubeData {title, type: "short", privacy: "public", category: "EDUCATION", madeForKids: false, isAiGeneratedContent: true, tags (without #)}`, `instagramData {type: "REEL", isAiGenerated: true}`, `tiktokData {title, isAigc: true}`.
   - text = `<hook>\n\nWatch the full video: <long video URL>\n\n<tags joined by spaces>`
5. Set `status: "scheduled"`, `long_url`, `metricool_id`. Files on the media branch (old Shorts only): `bash studio/publish.sh --rm <id>.mp4` (Metricool copied them when scheduling; the response's media URL starts with static.metricool.com).
6. Commit and push `studio/queue.json`.

## C. Every day: check what went live, learn from it (≈10 min)
Published videos are never edited or deleted. If something is wrong: bad luck, the next one must be better.
1. With `getScheduledPosts` (last 3 days), take every post with status PUBLISHED that is not in the `checked` list in `studio/lessons.md`:
   - Check what was sent: title, description (chapters for long videos, "Watch the full video: <link>" in Shorts and that this link is the right `publicUrl`), privacy public, AI disclosure line present. Any status other than PUBLISHED (e.g. an error) is a problem to report.
   - Re-check 3 claims from its script (`studio/assetedit/videos/<id>.json`): open the sources again with WebSearch/WebFetch and confirm names, years and numbers.
2. Write the result in `studio/lessons.md`:
   - Add the video id to `checked`.
   - For every problem, add one concrete rule under `## Rules`, for example "Say years in digits on cards; the voice reads '2020' fine". Keep rules short and testable. Merge duplicates.
3. Commit and push `studio/lessons.md`.
4. Refresh the dashboard hub (https://claude.ai/artifact/WvKMoV3qDoFScfsTEhJUDX): read `studio/yt/status.json` (written by the daily GitHub Actions check at 06:30 UTC) and the latest Actions run result. Write `yt_videos.json` from `status.json` videos (id, title without " #shorts", channel, type Short/Lang, published, seconds, views, likes, comments, url) and `hub_channels.json` (one row per channel and platform: channel, platform, status live/off/planned, subscribers, views, videos, route, checked_at, key = "channel · platform") and `hub_apis.json` (api, role, status ok/pending/limited/off/error, detail, checked_at; keep the Metricool row with checked_at "live"). Upload each with Artifact (`asset: true`), then ArtifactData `update` datasets `yt_videos` / `hub_channels` / `hub_apis` with the new `source.url` and `updated {at, by: "daily task"}`. If the Actions check failed, set the YouTube API row to error with the annotation text.

## T. Every 8 hours: trend study (≈10 min, separate scheduled task)
GitHub Actions `trend-scan` runs at 05:15, 13:15 and 21:15 UTC and writes `studio/trends/latest.json` (per niche: the last 7 days' videos that beat their channel size most, with title, description, tags, length, chapters yes/no, views, views/hour, outlier = views ÷ subscribers) and `studio/trends/thumbs/<id>.jpg`. Topics live in `studio/trends/topics.json` (add a line per new channel).
1. `git pull`. If `latest.json` is older than 9 h, check the last `trend-scan` run and report the error annotation.
2. Per group, study the top videos: look at every thumbnail with Read, and read titles and descriptions. Note per video in one line: title formula (length, words, curiosity gap, number, "you/your"), thumbnail (face/emotion, words on it, colors, focal object, layout), description (first line, chapters, links, hashtags), length.
3. Editing style: the API gives no frames. Infer it from length, chapters and Shorts format. Never download videos.
4. Update `studio/trends.md`: replace the `## Now working` block (max 12 bullets, each with an example title + channel + outlier score), and add a dated line to `## Log`. Turn a pattern into a rule under `## Rules` only when it shows up in 2+ scans; remove rules that stop showing up for 2 weeks.
5. Never copy a title, thumbnail or script. Take the pattern, not the content. Our own numbers (insights.md) beat outside trends when they disagree.
6. Commit and push. Only report when a new rule was added or something failed.

## STRATEGY (owner, 12 Oct 2026) — overrides anything below that conflicts
- TWO channels, both daily: Crazy Facts (`lfNN`, psychology) and Money at Night (`mnNN`, money psychology; video JSON has `"channel": "moneyatnight"`; build blocks with `CHANNEL_DIR=$PWD/studio/channels/moneyatnight`; render with `inputs[channel]=moneyatnight`). One ~2.5 h calm video per channel per day at 17:00 (Europe/Amsterdam), 20–30 blocks.
- Everything goes out via Zernio (verified 12 Oct), NOT Metricool: `zernio.yml cmd=post a=<id> b=YYYY-MM-DDT17:00`. Pick the first day that channel has no long video yet: look at `scheduled` in every `studio/renders/*/result.json` of that channel. Never two long videos on one channel on one day.
- Shorts are ON (Zernio posts YouTube Shorts directly, no audit needed). Every video gets ~1 Short per block in `videos/shorts.json` (best ≤58 s moment, hook `top`, `title`), rendered with the parts. Schedule: `cmd=shorts a=<id> b=YYYY-MM-DD` (3/day 09:00/13:00/21:00) or `b=YYYY-MM-DD@11:00,15:00,19:00` for a second stream. Goal: 6 Shorts/day per channel (two streams), never more than 50 Zernio posts/day in total. Start a video's Shorts on the day its stream slot frees up (see `shorts_posted` `when` in result.json).
- More Shorts from an already rendered video (part artifacts live 3 days): add entries with a new prefix to shorts.json, then `shorts.yml id=<id> run=<render-long run id> prefix=<prefix>`, then schedule them.
- AI images: Cloudflare free quota (~30–40 images/day, all channels). If it is used up, turn `photo` scenes into `char` scenes (allowed sprite/background pairs) and remove those `#ai` lines from photos.json, instead of waiting — publishing daily matters more. Openverse fallback only with a contact-sheet review.
- Encoding: mega.py default = fast 1080p for Zernio (`inputs[metricool]=1` only for a Metricool upload).

## VARIETY (owner, 12 Oct 2026) — overrides the fixed "2.5 h every day" in STRATEGY
Never publish the same template twice in a row on one channel. Rotate through these 15 formats (length = number of blocks of ~11 min; est.py for the check). Pick the next one that differs from the last two videos of that channel in length AND structure, and note it as `"format": "F07"` in the video JSON.
| F | Length | Structure | Look and pace |
| --- | --- | --- | --- |
| F01 | 150 min | deep dive, one story, wind-down at the end | calm, current default |
| F02 | 120 min | sleep marathon: half story, half guided wind-down | calm, speed 0.8, fewer visuals, mostly char scenes |
| F03 | 90 min | one story with a twist halfway | calm |
| F04 | 60 min | one study in depth (design, result, criticism, what it means) | calm, study/stat/bars scenes |
| F05 | 45 min | 5 myths debunked | normal speed, no wind-down, list scenes |
| F06 | 30 min | quick-fire "10 facts" | normal speed, lists and stats, short pauses |
| F07 | 30 min | one case file (a real experiment or event, step by step) | normal, conspiracy_board backgrounds |
| F08 | 60 min | 10 big questions, each answered in ~5 min | calm, quote and char scenes |
| F09 | 90 min | then and now: how an idea changed over time | curve/bars/timeline scenes |
| F10 | 120 min | myth versus science, point by point | normal, study scenes |
| F11 | 45 min | guided wind-down only, with a short fact story as intro | very slow, speed 0.8, pause 1.6 |
| F12 | 60 min | three classic experiments retold | calm, study scenes |
| F13 | 30 min | mini-course: 5 short lessons with a recap | normal, list scenes |
| F14 | 75 min | a day in the life of your brain / money, hour by hour | calm, curve scenes |
| F15 | 150 min | long listen: 12 short stories, each a different topic | calm, new chapter every ~12 min |
- Also vary: title pattern ("Why...", "The ... of ...", "How ...", "What ... Really ..."), thumbnail layout (text left or mirrored, accent colour), opening (cold open with the twist, or a quiet title start), sprite/background set and voice speed. Never reuse the scene list of an earlier video.
- Shorter videos cost fewer tokens: 1 Short per ~6 min of video; 6 Shorts a day per channel come from the whole back catalogue (shorts.yml), not only the newest video.
- New art from the owner (low resolution): register new sprites/backgrounds in the channel's manifest.json and upscale them with the `upscale` workflow before use; use them in new videos to keep the look varied.

## B. Every day: one 2.5-hour video (owner's strategy since 2026-10-11)
Strategy: publish ONE long video every day at 17:00, about 2.5 hours (140–160 min, 20,000–22,000 words), about ONE topic, with a calm, warm vibe. No Shorts until `studio/yt/APPROVED` exists (Part A then does nothing).
- One topic, one flowing story (e.g. "Your Brain at Night, Explained" = we follow the brain through one night). Viewers never see "parts": no "Part one", no part numbers, no "in this part", no progress bar, no chapter list in the description. Move on with natural spoken transitions ("Now, let's go deeper into the night...").
- Calm and warm: set `"vibe": "calm"` in the video and in every block. Unhurried sentences, friendly and cozy, no hype words, no shouting caps, no "SMASH that like". Calm sprites only (HAPPY, NEUTRAL, THINKING, CALM-looking poses; never SHOCKED, ANGRY or panic effects). Warm, soft backgrounds (bedroom_night, living_room_day, cozy ones). The renderer then uses the calm voice (am_michael at 0.92), longer pauses, warm grade, crossfades, no sound effects and soft amber captions.
- Internally the script is split into 12–18 blocks (`lfNN_b01` ...; ~800–1,600 words each, listed in `parts`) only so GitHub can render them in parallel. Block boundaries are invisible: the story just continues.
- Length check before rendering: total words × 60 / 183 + sentences × 0.85 s + segments × 0.5 s must be ≥ 150 min (owner: 2.5 h for maximum watch time; calm voice 0.86, pauses 0.85 s; after the render, check the real length in the mega.py output and add a block next time if it came out under 2:25). Too short: add a real subtopic (never filler). End calm videos with practical takeaways and a gentle guided wind-down block (`"speed": 0.8, "pause": 1.6`), then the `end` segment.
- Write blocks in the compact format and convert them: `python3 studio/scripts/block.py lfNN_bXX script.txt` (format in the script's docstring; it validates sprites/backgrounds and adds `#ai` / `#ov` images to `studio/assetedit/photos.json`). Example: lf06 (`Your Brain at Night, Explained`).
- Thumbnail for calm videos: `thumb.text` 2 lines, the last line lands on a warm block automatically; the sprite with the most fitting mood (e.g. A19 sleeping for a night topic), contrast with the text ("IT NEVER|SLEEPS" + sleeping character).
- Order of each daily run: first B5 (schedule yesterday's rendered video for today 17:00), then write today's complete video (all 12 blocks) and start its render (B4).
- Metricool free plan = 20 posts a month: until `studio/yt/APPROVED` exists, all 20 go to these long videos; when the month's budget is used up, keep producing and rendering (so videos are ready), but schedule them from the 1st of next month, and say so in the report. After approval: our own uploader, every day, no limit.

### B0. Setup
```
bash studio/setup.sh      # Kokoro voice (Apache-2.0) + espeak-ng; prints "voice OK"
```

### B1. Learn from the numbers (Metricool, free)
- First read `studio/lessons.md`, `studio/trends.md` (`## Rules` and `## Now working`: apply them to titles, thumbnails, hooks and descriptions) and the last 2 blocks of `studio/insights.md`. Every rule there applies to this run.
- `getAnalyticsDataByMetrics` brand 2266272, from 2026-10-01 to today, metrics `YTVV02, YTVV17, YTVV06, YTVV08, YTVV09, YTVV11, YTVV12`. Append a dated block to `studio/insights.md` (views, average view duration in minutes and as % of length, likes and comments per 1k views) + 3 bullets: what worked, what didn't, what to change. Only once per 3 days; with fewer than 3 videos older than 3 days, only log.
- For 2.5 h videos, watch time in minutes matters more than %; a part where many viewers drop → make the matching part of the next video shorter and punchier.

### B2. Theme and plan (when no video is in progress)
- A video is "in progress" when `studio/assetedit/videos/<id>.json` exists without `studio/renders/<id>/result.json`. Finish it first.
- New video: next id `lfNN`. Pick a theme from `series.json` (or a bigger cousin of what B1 shows works). Title: short and punchy, max ~40 characters, curiosity first (e.g. "Your Brain at Night, Explained"), never clickbait the video doesn't deliver. Write `videos/lfNN.json` = `{id, title, desc, tags, sources, thumb, vibe: "calm", parts: ["lfNN_b01" ... "lfNN_b12"], plan: [12 one-line block outlines]}` and add the title to `series.json`. Keep 3 planned titles after it.

### B3. Research and script (all 12 blocks in one run)
- Every block file `videos/lfNN_bXX.json` = `{id, part: true, vibe: "calm", segments}` in the segment format of `videos/lf01.json`. A new subtopic may start with a `chapter` segment: in calm videos it shows as a quiet caption of its `title` (no number) and its `say` is a natural transition, never "Part X". Block 1 opens with a gentle hook (what we'll discover tonight, within 15 s) and an overview list titled e.g. "Tonight, we'll explore" (no part numbers). Block 12 ends with calm takeaways, a callback to the opening and an `end` segment teasing tomorrow's video.
- ~1,700 words per part (`python3 studio/est.py <part>` for a time check, ≈11–13 min each). 2–4 web searches per part; every number, study, name and year from a source you opened; add them to the video's `sources`.
- Motion and variety (this is what keeps people watching for 2.5 h): per part at least 1 `photo` scene with an AI B-roll image (see AI images) or a free photo, a mix of `list`, `study`, `stat`, `bars`, `curve`, `quote`, `char` scenes, never more than 3 `char` scenes in a row, and different sprites/backgrounds leading each part. Captions, character motion, drifting backgrounds, transitions and the part progress bar are automatic.
- Real screenshots (`screen` scenes) only when the topic is about a real tool, site or app and seeing it helps. Never reuse a screenshot; vary `move`, `focus` and `side`. Public pages only, never logged-in dashboards, never edited, never implying a sponsor. List them in the channel's `shots.json` ({file, url}); the `screenshots` workflow fetches them; look at every shot before using it.
- Photos (`photo` scenes): free-licensed images via Openverse only (commercial use + changes allowed), listed in `photos.json` ({file, query}); credits go in the description automatically. Never images from Google, Pinterest or other sites; never reuse a photo; look at each one first.
- AI images (free): for ideas, metaphors, moods and B-roll add `{file, ai: "<prompt>"}` to `photos.json` (Flux on Cloudflare Workers AI, free tier ~100 a day for all channels; stay under 30 a run). Describe scene, style, light, "no text, no logos"; never real people, brands, copyrighted characters or our own character. Look at every result and regenerate with a new file name if it fails. Proof (prices, dashboards, earnings) is always a real screenshot. If the CF_API_TOKEN secret is missing, use Openverse and report it.
- Push `photos.json` / `shots.json` early in the run so the workflow fetches them while you write.
- Every video unique: vary hook type, part structure, scene order and mix; never copy the scene list of an earlier video.
- Use approved sprites and backgrounds only (`longform.validate` enforces this; A07 cannot be used).
- Shorts (only once `studio/yt/APPROVED` exists): for every block add 1 entry to `videos/shorts.json` (`{id: "shNNxx", src: "lfNN_pXX", first, last, top, title, tags}`, the part's strongest ≤58 s moment, hook text on top).
- Check one part locally before committing all: `cd studio/assetedit && python3 -c "import json,longform as L;L.validate(json.load(open('videos/lfNN_pXX.json')))"`.

### B4. Render (GitHub Actions, free) when all 12 parts are written
- Commit and push, then start the render: `gh api -X POST repos/JonkoJeff/channel-media/actions/workflows/render-long.yml/dispatches -f ref=main -f "inputs[id]=lfNN"` (for another channel add `-f "inputs[channel]=<slug>"`). All 12 parts render in parallel (voice, frames, captions, its Shorts), then they are stitched. Takes about 1 hour. It writes `studio/renders/lfNN/` (thumb.png, description.txt, 12 review frames, result.json with the public video and Shorts URLs on the GitHub release `lfNN`).
- If it fails: read the error annotation of the failed job (check-runs annotations API), fix the part, run again.
- Before the audit is approved the video is 720p and ≤ 500 MB (Metricool's limit); after approval it is 1080p via our own uploader.

### B5. Check and schedule (the run after the render)
- Look at the 12 review frames and the thumbnail: text overflow, wrong sprite, broken image, captions over the character. Read the description (chapters in h:mm:ss, sources, AI disclosure). Go through every rule in `studio/lessons.md`. Anything wrong: fix and re-render, never schedule it.
- Thumbnail text in `thumb.text`: max 3 words that add to the title; the strongest emotion sprite.
- Schedule with Metricool `createScheduledPost` at 17:00 today (or the next day without a long video; see the monthly budget): media = [result.json `video`], `videoThumbnailUrl` = result.json `thumb`, text = `studio/renders/lfNN/description.txt`, `youtubeData {title, type: "video", privacy: "public", category: "EDUCATION", madeForKids: false, isAiGeneratedContent: true, tags}`. With `studio/yt/APPROVED`, use our own uploader queue instead (see YouTube route).
- Shorts (only after approval): append the 12 Shorts to `studio/queue.json` (status pending, `file` = their URL from result.json, `long_title` = the title, due at 12:00, one per day from the day after the long video). Part A links and schedules them within the post budget.

### B6. Save and report
- Commit the JSON files, `insights.md`, `series.json` and `queue.json`. Never commit renders/, audio wav or models.

## Always end with a short report
Say what was scheduled (titles and dates), which parts of the video in progress were written, the insight bullets (when made), and anything that failed with what is needed. Never schedule something broken.

## Never
- Use vidIQ (owner's choice: not used at all).
- Use anything that costs money (paid plans, paid APIs, credits). The goal is to run everything for free; if something can only be done paid, report it instead.
- Post the same video twice.
- Reuse a script and only swap the topic (YouTube's "inauthentic content" rule).
- Remove the AI disclosure.
- Use copyrighted music or clips, or quote song lyrics.

## Zernio route (replaces Metricool for long videos once it works)
- Secret `ZERNIO_API_KEY` in GitHub (never in the repo or chat). The workspace cannot reach zernio.com; everything runs via `.github/workflows/zernio.yml`.
- Once: `cmd=accounts` (stores the YouTube accountId in `studio/yt/zernio.json`), then `cmd=playlist a="Title" b="description"` per playlist.
- Each video JSON has `playlists` (first one is used when posting). Playlists: Your Brain, Explained · Sleep & Your Brain · Everyday Psychology · Memory & Mind Tricks · Fall Asleep Learning.
- Schedule: `cmd=post a=lfNN b=YYYY-MM-DDT17:00` (local time). Writes `zernio_id` to result.json. Up to 5 GB, so 1080p is possible later.
- VERIFIED 12 Oct 2026: Zernio Short sh08_01 went public on schedule. Zernio is now the default route for long videos and Shorts; mega.py encodes a fast single-pass 1080p (set env METRICOOL=1 for the old 500 MB Metricool encode).

## CHARACTER IDENTITIES (owner, 12 Oct 2026; spread over Crazy Facts and Money at Night)
Every character is its own "show": own voice (Kokoro, all tested 12 Oct), own pace, own edit style, own thumbnail layout and palette. Set `voice`/`speed` in the video JSON. Never mix two characters in one video. Sprite ids per manifest: prefix = character.
| Channel | Character (prefix) | Voice / speed | Edit style | Thumbnail |
|---|---|---|---|---|
| Crazy Facts | Chibi, red hoodie (A) | am_puck 1.0 | fast cuts, punch, sfx, pop-up captions | bold yellow/red, big face, 2-word text |
| Crazy Facts | Teal-polo man (TP) | am_eric 0.97 | everyday habits, steady cuts, before/after cards | teal + rust, split before/after |
| Crazy Facts | Green-jacket man (GJ) | am_liam 1.0 | lifestyle/behaviour, brisk, location cards | green + white, big scene |
| Crazy Facts | Fawn, sprout antlers (FW) | bf_lily 0.88 | cosy "animal + sleep psychology", soft pans, slow | pastel green + cream, rounded text |
| Money at Night | Calm host (F, existing) | am_michael 0.92 | warm grade, crossfades, no sfx | navy + gold, chart motif |
| Money at Night | Navy blazer A (NB) | bm_george 0.95 | office/charts, clean lower-thirds | navy + white, chart + arrow |
| Money at Night | Navy blazer B (NC) | am_adam 0.95 | money habits, case-file style, card-heavy | navy + coral, big number |
| Money at Night | Bearded sweater (BS) | bm_lewis 0.92 | study/lecture, quote and study cards, euro motifs | khaki + navy, serif text |
| (on hold, API) | Pip cloud (own channel) | bm_fable 0.85 | very slow, dusk palette | indigo + star yellow |
Sheets are cut by silhouette with `assetedit/cutsheet.py` and registered with `assetedit/register.py` (emotion tags by owner review); baked-scene poses are not registered. Allowed pairs follow the emotion lists of the backgrounds. 4x upscale via the `upscale` workflow into `assets_hd`.

## RELIGION UNFOLDED (owner, 12 Oct 2026) - channel "religion", 3rd channel, own Zernio account (secret ZERNIO_API_KEY_2, alias ZERNO_API_KEY_2)
The Pip/mythology channel concept is CANCELLED. This channel replaces it. The YouTube channel is "Belief Through Time" (@BeliefThroughTime) (owner, 12 Oct); Religion Unfolded is the brand/art name in the scripts. Zernio: key 1 = Crazy Facts + Money at Night, key 2 = Belief Through Time only (separate Zernio account).
SCOPE (owner): the machine does ONLY write script -> narration -> render -> QC -> publish/schedule (plus minimal code fixes to unblock). No hub, no stats, no trend study, no new concepts, no thumbnail work, no brainstorming. Strategy of Crazy Facts and Money at Night is unchanged.
- Source of truth: the owner's approved stories/titles/thumbnails of the first 30 episodes. Thumbnails are in `studio/channels/religion/thumbs/` (bible_01..10, 301..310, Q01..Q10 = Quran backlog). Stories are NOT in the repo yet: if the story for an episode is missing, report it in one line and skip (never invent).
- Order is fixed: Christianity (101-110), episodes 201-210, Hindu epics/Buddhism (301-310). Never repeat a finished episode. Quran Q01-Q10 are backlog: do not research/script/render before their turn.
- Video JSON: `"channel": "religion"`; default 15 min (~130 wpm, real length x1.105 rule applies). One narrator, one voice for all episodes: bm_lewis 0.92 (Kokoro, tested), light compression, -16 LUFS, peaks <= -1 dBTP, soft ending.
- Style: dark navy/black + gold, slow zooms/pans, maps, dates, minimal text, licensed sources only (Wikimedia, Met, Smithsonian, Rijksmuseum, LoC), attribution saved in the video JSON "sources". Never depict Prophet Muhammad. AI-narration and synthetic-media disclosure on.
- Posting: `zernio.yml cmd=post` (the script picks key 2 for channel religion). First run once: cmd=accounts a=2 to store the account id. Schedule per the owner's existing schedule; never change privacy/time without owner.
- Reply format after a job: Episode / Script / Narration / Render / Publishing / Video URL / Token usage / Est. cost, nothing else.

## TOKEN RULES (owner, 12 Oct 2026)
Only these recurring jobs exist: the daily channel-machine task. Disabled: hourly hub+Gmail check, 8-hourly trend study, hub/trend schedules in Actions. One model call per script; no re-reading of finished work; no re-running successful stages; keep chat output minimal; rendering and posting run in GitHub Actions (no tokens).

## RELIGION: scripts from ChatGPT (owner, 12 Oct 2026)
- Order = `studio/channels/religion/episode_list.md` (1-10 Bible, 11-20 Christianity, 21-30 Quran; Hindu/Buddhism 301-310 is a separate series, thumbs ready). Scripts are written by the owner via ChatGPT in `studio/channels/religion/stories/NN.txt` (format: stories/FORMAT.md). The machine does NOT write or rewrite scripts: it only parses, voices, renders, checks, publishes.
- Length ~1 hour per video, 4 Shorts per video (from the SHORTS header), posted via key 2 like the long video. Thumbnail = thumbs file with the same number (01-10 bible_*, Q01-Q10 for 21-30, 301-310). Missing thumb or script -> one-line report, skip.
- PRIORITY: Belief Through Time comes first. If tokens run short, Money at Night is cut first (fewer/shorter videos), then Crazy Facts; never Belief Through Time.

## RELIGION: order and titles (owner, 12 Oct 2026, replaces the "order" lines above)
- Publish in MIXED order for variety, not 1-30: rotate Bible, Quran, Christianity: 1, 21, 11, 2, 22, 12, 3, 23, 13, ... (an episode whose script or thumbnail is missing is skipped until the next one that is ready; never reorder inside a tradition).
- YouTube title = the story title only, from episode_list.md, WITHOUT the list number and without "Part N" / "Episode N".
- Priority: 1 Belief Through Time, 2 Crazy Facts, 3 Money at Night (lowest; cut or shorten first when tokens run short).

## DAILY RULE (owner, 13 Oct 2026, 00:02)
Belief Through Time gets ONE video EVERY day (plus its 4 Shorts). If that cannot be guaranteed (no script ready, tokens/limits short), the posting of Money at Night is STOPPED completely (no long video, no Shorts) until Belief Through Time is covered again. Crazy Facts keeps running. Default times (owner gave none): long 19:00 Europe/Amsterdam daily; Shorts 10:00, 13:00, 16:00, 22:00 on the following days (zernio.yml cmd=shorts DATE@10:00,13:00,16:00,22:00). Build with religion.yml ep=NN, then zernio.yml cmd=post a=relNN.

## MONEY AT NIGHT REMOVED (owner, 13 Oct 2026, 08:14)
Money at Night is SCRAPPED: the owner rebuilt that YouTube channel into Belief Through Time. Only TWO channels remain: Crazy Facts and Belief Through Time. Do NOT build, render, schedule or post anything for Money at Night (mnNN, NB/NC/BS characters, studio/channels/moneyatnight). This overrides every earlier MaN line, the priority list and the DAILY RULE's MaN clause (nothing left to stop). Zernio key 1 = Crazy Facts only; key 2 = Belief Through Time. Free tokens go to Belief Through Time first, then Crazy Facts.
Zernio (owner, 13 Oct 08:30): key 2 does nothing. Belief Through Time posts via KEY 1, on the 2nd YouTube account (the former Money at Night account, id in zernio.json youtube.religion). `religion_key: 1` in zernio.json.

## NO MONEY VIDEOS EVER (owner, 13 Oct 17:21)
Never again any video about money/finance on any channel. Scheduled Money at Night posts were deleted. Repo is PRIVATE since 13 Oct: release downloads must use the GITHUB_TOKEN (gh), not anonymous curl.
## VARIETY (owner, 13 Oct)
Vary thumbnails and videos: rotate characters, backgrounds, layouts, colours, headline styles; no two consecutive uploads with the same look.
Thumb options in the video JSON (longform.thumbnail): `"mirror": true` = sprite left / text right (background flipped, sprite not, so "?" stays readable); `"accent": "#RRGGBB"` = colour of the word block + rim (use light colours; text on the block is dark). Used: lf09 amber/left, lf11 #FF8FB1/mirror, lf10 #4FD1C5/left.

## NEVER UPLOAD TWICE (owner, 14 Oct)
zernio.py post/shorts: (1) refuses when result.json already has zernio_id / the Short is in shorts_posted; (2) checks Zernio for an existing live post with the same content and adopts it; (3) on no answer (timeout) it looks for the post instead of retrying; (4) the workflow always commits result.json, even after a failed step. To re-post on purpose: delete the Zernio post, clear zernio_id in result.json, then run again. Never re-run a failed post/shorts run without first running cmd=status or cmd=list.

## CRAZY FACTS SHORTS: 4 PER DAY (owner, 14 Oct)
Crazy Facts gets exactly 4 Shorts per day (09:00, 12:00, 15:00, 20:00; the long video stays at 17:00), only the most interesting points. zernio.py shorts defaults to these 4 slots; `zernio.yml cmd=reslot a=<first day> b=<slots>` re-times all pending Shorts to 4/day. Per video, schedule only its best Shorts (hook + strongest fact); skip filler cuts.

## THUMBNAILS (14 Oct): private repo
raw.githubusercontent.com URLs no longer work for Zernio/YouTube (repo is private) -> YouTube picked an auto frame (rel01). zernio.py now uploads the thumbnail file to Zernio media (host_thumb) when posting. `zernio.yml cmd=rethumb a=lf10,lf11` re-attaches it to still-SCHEDULED posts; published videos need the thumbnail set in YouTube Studio. result.json "thumb" stays a repo URL (only used to find the file).

## SHORTS: thumbnail + selection (14 Oct)
Shorts now get a thumbnail (frame at 1.5 s with the hook text, hosted on Zernio). Select Shorts per studio/factory/learned.md (14 Oct rule: one study + one twist + numbers, never intros/agendas, hook = the surprising claim). 4 per day.

## GROWTH LOOP (owner, 14 Oct: grow per video, quality over volume)
Daily 05:00 UTC `stats.yml` refreshes studio/yt/status.json (Actions only, no Claude tokens). Once a week (when videos have 7 days of data) run the factory analyst `cf_analyze` on status.json: winners and flops per hook/length/slot/topic -> proposals -> learned.md. Per video: keep only Shorts that follow learned.md; fewer, stronger uploads beat more filler. Trend scan (`trends.yml`) and competitor lookup (`lookup.yml`) stay manual: run them only when the weekly analysis asks for it.

## LANGUAGES (owner, 15 Oct): main language American English, plus translated titles/descriptions
Every long Crazy Facts video gets localized title + short description in: es, pt-BR, hi, id, fr, de, ar, tr, ru, it, ja, ko (YouTube shows them by viewer language; audio stays English, viewers use YouTube's auto-translated subtitles). After a long video goes live: add its YouTube id and the translated titles to studio/yt/localize.json (Codex translates, Claude checks) and run `localize.yml`. Needs the Crazy Facts YouTube token; Belief Through Time (Zernio-only) has to be done in Studio.

## BOTH CHANNELS (owner, 15 Oct, replaces "FOCUS: only Brain After Dark")
Both channels active: Brain After Dark (formerly Crazy Facts) and Belief Through Time, each 1 long video at 20:00 + 4 Shorts at 15:00, 18:00, 21:00, 23:30 (Europe/Amsterdam). BAD is the standard; BTT catches up per studio/channels/religion/GAP.md. Pending Shorts: `zernio.yml cmd=reslot a=<first day> b=15:00,18:00,21:00,23:30 c=<lf|rel>`.

## VOICE FLOW (15 Oct)
Long-video narration (longform.py voice()): 1-2 sentences per Kokoro take (<170 chars, not across a question), speed 0.93 (calm) with +-3% repeatable variation per take, pause 0.6 s (calm) scaled by take length / question and jittered, 12 ms fades. Voices unchanged (am_michael). Only affects NEW audio (cached *_vo.wav stay). Owner feedback: voice was too robotic.

## US POST TIMES (15 Oct, owner approved)
Brain After Dark (Europe/Amsterdam): Shorts 15:00, 18:00, 21:00, 23:30 (= 9am/12pm/3pm/5:30pm ET); long video 20:00 (2pm ET). Use `reslot a=<first day> b=15:00,18:00,21:00,23:30` for Shorts and these times for new long posts. Belief Through Time 15 Oct Shorts deleted (rel01).

## CAPTIONS + EDITING (15 Oct, owner: editing boring, subtitles wrong)
- Captions: shorts.sentence_spans() measures real sentence start/end from the voice wav (the n-1 longest silences in a segment = sentence boundaries); only the words inside a sentence are estimated (length + comma weight). Old method (whole segment by letter count, x0.92) drifted by seconds. Used by longform.py and shorts.render. Captions never hang through a pause (word end +0.25 s max).
- Editing (calm long videos): every sentence re-frames the shot (wide -> toward the text -> close on the character, zoom 1.0/1.07/1.13 + shift, plus slow push-in). Still to do: more scene variety (photo/screen cards, B-roll) per script, see GAP/STYLE.

## BTT VOICE APPROVED (owner, 15 Oct)
Owner: "STEM IS PERFECT". Belief Through Time uses studio/voice/flow.py (same natural flow as Brain After Dark, voice bm_lewis 0.92) + quiet music bed. Unpublished episodes rel03, rel04, rel22, rel23, rel24 are re-rendered with it; published ones (rel01, rel21) stay as they are.
- VOICE (15 Oct, owner): Brain After Dark long videos (vibe calm) now use the same voice as Belief Through Time: bm_lewis 0.92 (overrides the per-block voice am_michael). Shorts cut from the long audio follow automatically. Revert = restore "am_michael"/0.93 in longform.py voice().
- WARM VOICE (15 Oct, owner: "beetje meer warmer"): calm long videos get flow.warm() on the final voice wav (+3.5 dB at 160 Hz, +1.5 at 320 Hz, -2.5 dB at 3.8 kHz, lowpass 7.8 kHz). Tune WARM in studio/voice/flow.py; Belief Through Time is untouched (owner: its voice is perfect).
- VOICE FINAL (15 Oct, owner chose "mid D"): Brain After Dark calm long videos = voice am_onyx+bm_lewis+bm_lewis (blend), speed 0.88, pause 0.7 s, flow.warm(wav, pitch 0.97). Replaces the bm_lewis/0.92 line above. Belief Through Time stays bm_lewis 0.92.

## NO MORE GITHUB ACTIONS SPEND (15 Oct, owner)
GitHub Actions billing failed (private repo minutes) and the owner will not pay: posting runs LOCALLY with `python studio/local/post_btt.py` (key in env ZERNIO_API_KEY, never in repo; releases are free to download). Scheduled crons (stats, youtube) are commented out; workflow_dispatch stays. Rendering still needs a free place to run (local machine) until billing is fixed.

## REPO PUBLIC AGAIN (owner, 15 Oct)
Owner made the repo public: GitHub Actions is free and unlimited again (private-repo minutes were used up). Scheduled crons (stats, youtube) are back on. Keys stay in GitHub Secrets only (scan 15 Oct: no secrets in code or history). Local posting runner studio/local/post_btt.py stays available.
- THUMBNAILS (15 Oct, owner: "elke thumbnail een andere kleur"): longform.thumbnail() takes the rim glow + word block colour from ACCENTS[video number % 10] (10 saturated colours), ignoring th.accent unless th.accent_lock=true; mirrored text keeps 150 px from the right edge.
- THUMBNAILS 2 (15 Oct): no green accents; background rotates among approved backgrounds that allow the sprite emotion (th.bg_lock=true keeps the block value).

## SHORT COVER FRAME (BAD)
Every BAD Short now opens with a designed 1.7 s cover (shorts.py `cover()`): character with accent glow + big hook text (`top`), colour per Short id (ACCENTS, no green). Zernio's auto-picked frame (1.5 s) is therefore a real thumbnail. BTT Shorts: same idea still to do.

## POSE VARIETY (BAD thumbnails + Short covers)
Sprites N01–N30 (owner sheet, 15 Oct) cut + 4x upscaled + registered with emotion and `family`. `longform.pick_sprite(key, base)` swaps the scripted sprite for another of the SAME emotion, never one of the last 6 sprites or last 2 pose families (per prefix lf/sh), remembered in `studio/assetedit/thumb_history.json` (commit it after a render). Lock a pose with `thumb.sprite_lock: true`. Props that only fit a matching story (N02, N11, N18, N19, N23, N26) and A18 have `auto: false`.
