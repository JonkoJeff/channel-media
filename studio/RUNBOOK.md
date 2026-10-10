# Daily run: Crazy Facts channel machine

You run unattended, once a day. All video content is in English. Use the ponytail skill: smallest complete change, reuse what exists. A new video is a new JSON file, never new code unless something is broken.

- Repo `JonkoJeff/channel-media` (public). Studio: `studio/`. Video files for Metricool: branch `media`, folder `files/` (via `studio/publish.sh`).
- Metricool brand `2266272`, timezone Europe/Amsterdam. YouTube channel `UCynthMQNy9uDsuHcewQDERg`.
- Links of published videos: Metricool `getScheduledPosts` (brand 2266272, Europe/Amsterdam, a date range around the publish date, `extendedRange: true`). A published post has `providers[0].status: "PUBLISHED"` and `publicUrl` (the YouTube link). The YouTube RSS feed and watch pages block WebFetch, so don't use them.

## YouTube route (check first)
- If `studio/yt/APPROVED` exists (Google approved the API audit): **all YouTube uploads go through our own uploader**, no post limit. Append items to `studio/yt/queue.json` (`{id, file, thumb, title, description, tags, publish_at (UTC ISO, e.g. 17:00 Amsterdam = 15:00Z in summer, 16:00Z in winter), short, status: "pending"}`) and push; GitHub Actions uploads each item within 26 h of its `publish_at`, max 8 per run (daily at 06:30 UTC), and writes back `video_id`. Max 8 uploads a day per channel (long + Shorts together). If a run reports "daily upload limit reached", lower to 5 a day for 2 weeks and say so in the report. Rhythm (owner's choice, 8 uploads a day): 1 long video every day at 17:00 + 7 Shorts a day at 08:00, 10:00, 12:00, 14:00, 19:00, 21:00 and 23:00 (Amsterdam). Make 5 Shorts per new long video (A hook, B study, C tip, D and E strong moments); fill the rest from the back catalog (best performers first, never a segment twice). Never 2 Shorts in a row from the same video. Part B then runs EVERY day and makes 1 long video (plus its 5 Shorts) instead of 2 on Sundays/Wednesdays. Items in `studio/queue.json` with status `later` go back into the rotation. Metricool then only posts Shorts to TikTok/Instagram (if connected), within the 20-post budget below.
- If it does not exist yet: uploads through our own uploader stay private, so keep using Metricool for YouTube with the budget below.

## Post budget (Metricool free plan: 20 posts per calendar month)
- Count every post in `getScheduledPosts` whose publication date is in that month, any status. One Metricool post counts once, however many networks it goes to.
- Long videos come first: always reserve one slot for each Mon/Wed/Fri 17:00 still ahead in the month. Shorts only use what is left: `free = 20 - counted - reserved`. If `free <= 0`, no Short that month.
- Every Short is one post to every connected network at once (YouTube Short + Instagram Reel + TikTok), so each slot gets the most reach.
- If the user upgrades the plan, they will say so; then this section goes away.

## A. Every day: link and schedule due Shorts (≈5 min)
Order of a run: A, then C, then B (Sundays and Wednesdays).
1. Read `studio/queue.json`. Take items with `status: "pending"` and `due` today or earlier.
2. For each item, find the long video whose title equals `long_title` in `getScheduledPosts` with status PUBLISHED and take its `publicUrl`. Not published yet: leave the item pending, retry tomorrow.
3. Check the post budget for the month of `due`. No free slot: leave it pending and set `due` to the 1st of the next month at 12:00. Max 1 Short per day.
4. On a match with a free slot, Metricool `createScheduledPost` (brand 2266272, `autoPublish: true`):
   - date = `due` (Europe/Amsterdam). If that time has passed or is less than 20 min away, use now + 30 min.
   - media = [`file`], providers: youtube, plus instagram and tiktok if `getBrandSettings` shows them connected. `youtubeData {title, type: "short", privacy: "public", category: "EDUCATION", madeForKids: false, isAiGeneratedContent: true, tags (without #)}`, `instagramData {type: "REEL", isAiGenerated: true}`, `tiktokData {title, isAigc: true}`.
   - text = `<hook>\n\nWatch the full video: <long video URL>\n\n<tags joined by spaces>`
5. Set `status: "scheduled"`, `long_url`, `metricool_id`. Then `bash studio/publish.sh --rm <id>.mp4` for those files (Metricool copied them when scheduling; the response's media URL starts with static.metricool.com).
6. Commit and push `studio/queue.json`.

## C. Every day: check what went live, learn from it (≈10 min)
Published videos are never edited or deleted. If something is wrong: bad luck, the next one must be better.
1. With `getScheduledPosts` (last 3 days), take every post with status PUBLISHED that is not in the `checked` list in `studio/lessons.md`:
   - Check what was sent: title, description (chapters for long videos, "Watch the full video: <link>" in Shorts and that this link is the right `publicUrl`), privacy public, AI disclosure line present. Any status other than PUBLISHED (e.g. an error) is a problem to report.
   - Re-check 3 claims from its script (`studio/assetedit/videos/<id>.json`): open the sources again with WebSearch/WebFetch and confirm names, years and numbers.
   - If vidIQ credits allow (`vidiq_balance`): read the transcript (`vidiq_video_transcript`) and compare it with the script, and read the comments (`vidiq_video_comments`) for viewers pointing out mistakes or confusion.
2. Write the result in `studio/lessons.md`:
   - Add the video id to `checked`.
   - For every problem, add one concrete rule under `## Rules`, for example "Say years in digits on cards; the voice reads '2020' fine". Keep rules short and testable. Merge duplicates.
3. Commit and push `studio/lessons.md`.
4. Refresh the dashboard hub (https://claude.ai/artifact/WvKMoV3qDoFScfsTEhJUDX): read `studio/yt/status.json` (written by the daily GitHub Actions check at 06:30 UTC) and the latest Actions run result. Write `yt_videos.json` from `status.json` videos (id, title without " #shorts", channel, type Short/Lang, published, seconds, views, likes, comments, url) and `hub_channels.json` (one row per channel and platform: channel, platform, status live/off/planned, subscribers, views, videos, route, checked_at, key = "channel · platform") and `hub_apis.json` (api, role, status ok/pending/limited/off/error, detail, checked_at; keep the Metricool row with checked_at "live"). Upload each with Artifact (`asset: true`), then ArtifactData `update` datasets `yt_videos` / `hub_channels` / `hub_apis` with the new `source.url` and `updated {at, by: "daily task"}`. If the Actions check failed, set the YouTube API row to error with the annotation text.

## B. Sundays and Wednesdays: make the next videos (≈1.5 h)
Rhythm: long video is the main route: 3 a week (Mon, Wed, Fri at 17:00). Shorts fill the leftover post budget (see Post budget): about 7 a month, at 12:00, max 1 a day, never 2 in a row from the same video.
Back catalog: from 10 published long videos on, add 2 extra Shorts a week cut from older videos, best performers first, never a segment already used (check shorts.json).
Scale every 3 weeks from insights.md within the post budget: good retention/CTR -> keep 3 long a week; dropping -> fewer, better long videos. Each run makes 2 long videos, unless the next 7 days already have 3 scheduled; then make 1, or 0 and only do A and C.

### B0. Setup
```
bash studio/setup.sh      # Kokoro voice (Apache-2.0) + espeak-ng; prints "voice OK"
```

### B1. Learn from the numbers (Metricool, free)
- First read `studio/lessons.md` (rules from earlier mistakes) and the last 2 blocks of `studio/insights.md`. Every rule there applies to this run.
- `getAnalyticsDataByMetrics` brand 2266272, from 2026-10-01 to today, metrics `YTVV02, YTVV17, YTVV06, YTVV08, YTVV09, YTVV11, YTVV12` (date, title, views, avg view duration, likes, comments, shares).
- Append a dated block to `studio/insights.md` with these columns per video: views, avg view duration as % of length, likes and comments per 1k views. Then 3 bullets: what worked, what didn't, and what to change this week.
- Rules of thumb:
  - A long video where viewers watch under 30% on average → the hook is too slow. Shorten the intro list and open with the payoff.
  - A topic with the best views per day → put a close cousin next in the queue.
  - A Short with high views → reuse its hook style.
- With fewer than 3 videos older than 3 days, only log the numbers. Draw no conclusions yet.

### B2. Pick the topics (1 or 2, see above)
- Take the next 2 titles from `studio/assetedit/videos/series.json` that have no JSON file yet, unless B1 says another topic should jump the queue.
- Always keep at least 3 planned titles after the ones you make, because descriptions promise "coming up next". Use the pattern "Why <relatable thing your brain does>", backed by a real study. Seasonal topics go in 1–2 weeks early.

### B3. Research and script (per video; next id = lfNN)
- Do 2–4 web searches. Every number, study, name and year must come from a source you opened. Never invent figures. If a study has no numbers, use `list` or `study` cards, not `bars` or `stat`.
- Copy the structure of `studio/assetedit/videos/lf01.json`:
  1. Hook: 2–4 `char` segments, with the payoff promised within 15 s.
  2. An "In this video" list.
  3. 4 `chapter` parts, with a comment question in the middle and a re-hook before part 3.
  4. Practical tips.
  5. A callback to the opening.
  6. An `end` segment that teases the next title in series.json.
- Length: 1,450–1,650 words. `python3 studio/est.py <file>` must print OK.
- Use approved sprites and backgrounds only (`longform.validate` enforces this; A07 cannot be used). Fill in `thumb`, `desc`, `sources` and `tags`.

### B4. Render and check
```
cd studio/assetedit && python3 longform.py videos/lfNN.json    # ≈20 min each
```
- Check that the length is ≥ 8:00 and the file has audio, and go through every rule in `studio/lessons.md` one by one. Look at 6 frames (`ffmpeg -ss`) and at the thumbnail. Fix and re-render if anything overflows or looks wrong.
- Add 2 Shorts per video to `videos/shorts.json` (A = hook segments, B = study reveal; each ≤ 58 s). A goes first in the queue, B only if the budget has room. Render only the new ones: put them in a temp JSON and run `python3 shorts.py <temp.json>`.

### B5. Schedule
- `bash studio/publish.sh renders/lfNN.mp4 renders/lfNN_thumb.png renders/shNNa.mp4 renders/shNNb.mp4` prints the public URLs.
- Thumbnail: add `videoThumbnailUrl` (the png URL) to the long-video post (channel is verified). Thumbnail text in `thumb.text`: max 3 words / ~12 characters that add to the title, never repeat it (curiosity gap). Pick the sprite with the strongest emotion for the topic.
- Long videos: Metricool `createScheduledPost` at 17:00 on the first free Monday, Wednesday or Friday after the last long video already scheduled (`getScheduledPosts`). Never 2 long videos on one day; never a gap longer than 3 days:
  - text = `renders/lfNN_description.txt`
  - `youtubeData {title, type: "video", privacy: "public", category: "EDUCATION", madeForKids: false, isAiGeneratedContent: true, tags}`
  - Afterwards: `publish.sh --rm lfNN.mp4`
- Shorts: do not schedule them now. Append them to `studio/queue.json` (status pending, due at 12:00, one per day, starting the day after their long video and never on a day that already has a Short in the queue). Part A links them to the long video once it is live. Part A applies the post budget; leftover Shorts roll to next month.
- Check `getScheduledPosts` first so nothing collides.

### B6. Save and report
- Commit the new JSON files, `insights.md`, `series.json` and `queue.json`. Never commit renders/, audio wav or models.
- On the first Sunday of each month, shrink the media branch: recreate it as an orphan holding only files still pending in queue.json, then force-push.

## Always end with a short report
Say what was scheduled (titles and dates), the insight bullets (Sundays and Wednesdays), and anything that failed with what is needed. Never schedule something broken.

## Never
- Use anything that costs money (paid plans, paid APIs, credits). The goal is to run everything for free; if something can only be done paid, report it instead.
- Post the same video twice.
- Reuse a script and only swap the topic (YouTube's "inauthentic content" rule).
- Remove the AI disclosure.
- Use copyrighted music or clips, or quote song lyrics.
