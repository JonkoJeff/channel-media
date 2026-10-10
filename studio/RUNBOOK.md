# Daily run: Crazy Facts channel machine

You run unattended, once a day. All video content is in English. Use the ponytail skill: smallest complete change, reuse what exists. A new video is a new JSON file, never new code unless something is broken.

- Repo `JonkoJeff/channel-media` (public). Studio: `studio/`. Video files for Metricool: branch `media`, folder `files/` (via `studio/publish.sh`).
- Metricool brand `2266272`, timezone Europe/Amsterdam. YouTube channel `UCynthMQNy9uDsuHcewQDERg`.
- Links of published videos: Metricool `getScheduledPosts` (brand 2266272, Europe/Amsterdam, a date range around the publish date, `extendedRange: true`). A published post has `providers[0].status: "PUBLISHED"` and `publicUrl` (the YouTube link). The YouTube RSS feed and watch pages block WebFetch, so don't use them.

## A. Every day: link and schedule due Shorts (≈5 min)
Order of a run: A, then C, then B (Sundays and Wednesdays).
1. Read `studio/queue.json`. Take items with `status: "pending"` and `due` today or earlier.
2. For each item, find the long video whose title equals `long_title` in `getScheduledPosts` with status PUBLISHED and take its `publicUrl`. Not published yet: leave the item pending, retry tomorrow.
3. On a match, Metricool `createScheduledPost` (brand 2266272, `autoPublish: true`):
   - date = `due` (Europe/Amsterdam). If that time has passed or is less than 20 min away, use now + 30 min.
   - media = [`file`], provider youtube, `youtubeData {title, type: "short", privacy: "public", category: "EDUCATION", madeForKids: false, isAiGeneratedContent: true, tags (without #)}`.
   - text = `<hook>\n\nWatch the full video: <long video URL>\n\n<tags joined by spaces>`
4. Set `status: "scheduled"`, `long_url`, `metricool_id`. Then `bash studio/publish.sh --rm <id>.mp4` for those files (Metricool copied them when scheduling; the response's media URL starts with static.metricool.com).
5. Commit and push `studio/queue.json`.

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

## B. Sundays and Wednesdays: make the next videos (≈1.5 h)
Rhythm: 3 long videos a week (Mon, Wed, Fri at 17:00). 3 Shorts per long video (A hook, B study reveal, C practical tip), 9 a week: daily at 12:00, plus 20:00 on Mon/Wed/Fri. Max 2 Shorts a day, never 2 in a row from the same video.
Back catalog: from 10 published long videos on, add 2 extra Shorts a week cut from older videos, best performers first, never a segment already used (check shorts.json).
Scale every 3 weeks from insights.md: good retention/CTR -> 4 long a week or 2 Shorts every day; dropping -> back down. Each run makes 2 long videos, unless the next 7 days already have 3 scheduled; then make 1, or 0 and only do A and C.

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
- Add 3 Shorts per video to `videos/shorts.json` (A = hook segments, B = study reveal, C = a practical tip; each ≤ 58 s). Render only the new ones: put them in a temp JSON and run `python3 shorts.py <temp.json>`.

### B5. Schedule
- `bash studio/publish.sh renders/lfNN.mp4 renders/lfNN_thumb.png renders/shNNa.mp4 renders/shNNb.mp4` prints the public URLs.
- Thumbnail: add `videoThumbnailUrl` (the png URL) to the long-video post. If Metricool answers VIDEO_THUMBNAIL_NOT_APPLICABLE (channel not phone-verified yet), schedule again without it and mention "verify the channel by phone" once in the report.
- Long videos: Metricool `createScheduledPost` at 17:00 on the first free Monday, Wednesday or Friday after the last long video already scheduled (`getScheduledPosts`). Never 2 long videos on one day; never a gap longer than 3 days:
  - text = `renders/lfNN_description.txt`
  - `youtubeData {title, type: "video", privacy: "public", category: "EDUCATION", madeForKids: false, isAiGeneratedContent: true, tags}`
  - Afterwards: `publish.sh --rm lfNN.mp4`
- Shorts: do not schedule them now. Append them to `studio/queue.json` (status pending, due at 12:00, one per day, starting the day after their long video and never on a day that already has a Short in the queue). Part A links them to the long video once it is live. Aim for exactly 1 Short per day; if a day would stay empty, add a third Short (a strong tip or myth-vs-fact moment, ≤ 58 s) from the newest video.
- Check `getScheduledPosts` first so nothing collides.

### B6. Save and report
- Commit the new JSON files, `insights.md`, `series.json` and `queue.json`. Never commit renders/, audio wav or models.
- On the first Sunday of each month, shrink the media branch: recreate it as an orphan holding only files still pending in queue.json, then force-push.

## Always end with a short report
Say what was scheduled (titles and dates), the insight bullets (Sundays and Wednesdays), and anything that failed with what is needed. Never schedule something broken.

## Never
- Post the same video twice.
- Reuse a script and only swap the topic (YouTube's "inauthentic content" rule).
- Remove the AI disclosure.
- Use copyrighted music or clips, or quote song lyrics.
