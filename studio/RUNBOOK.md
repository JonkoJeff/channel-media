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
