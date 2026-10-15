# GAP: Brain After Dark (standard) vs Belief Through Time (catching up)

Evidence = current code and renders (15 Oct 2026). One line per point: BAD does / BTT does / change. Order = biggest quality win first.

| # | Point | BAD (standard) | BTT (now) | Change |
|---|---|---|---|---|
| 1 | Voice | longform.py `voice()`: 1-2 sentences per take (<170 chars, not across a "?"), speed 0.93 ±3% repeatable, pause by length/question with jitter, 12 ms fades, trimmed silence | build.py `speak()`: one sentence per take, fixed 0.92, fixed 0.32 s pause, no trim/fades -> robotic | Shared `studio/voice/flow.py` (same logic), build.py uses it; voice stays bm_lewis (CHARACTER IDENTITIES). Test 1 block, owner listens before re-rendering. |
| 2 | Long thumbnail | longform `thumbnail()`: big 2-line text block, accent colour, mirror layout, rotated per upload (VARIETY) | static owner JPG from thumbs/ (bible_NN, QNN), no text, same look per tradition | build.py renders a thumbnail: owner image (or best scene image) + 3-4 word headline from a `THUMB:` header, high contrast, rotating accent + side; saved in studio/renders/relNN/thumb.jpg (host_thumb uploads it). |
| 3 | Music bed | `music()`: soft chord bed ~24 dB under the voice | none (voice only) | Same quiet bed in build.py, dropped ~0.8 s before chapter reveals. |
| 4 | Editing rhythm | scene types change every 60-90 s (list/study/stat/bars/curve/photo/char), drifting backgrounds, 0.7 s crossfades, warm grade | Ken Burns stills, a cut every ~7 s, dip-to-black fades, chapter label only | Crossfade instead of dip, vary zoom/pan direction per sentence, hold a short silence before a reveal (chapter start). |
| 5 | Captions | word-by-word burned captions (shorts.captions) | none | Not now (stills + gold text style); revisit after growth data. |
| 6 | Scripts and hooks | STYLE.md + learned.md, audits, hook = surprising claim | STYLE_religion.md + audits; hook rule older | Add the BAD hook rule (one concrete surprise in the first 15 s) to STYLE_religion.md; never invent facts. |
| 7 | Shorts | learned.md rule: one study + one twist + hard numbers, 40-50 s, no intros, hook text = the claim; 1.5 s frame thumbnail with text | SHORTS header 35-58 s, any moment; title drawn 5 s (so the 1.5 s frame has text) | rel_shorts prompt: one surprising fact + concrete detail, 40-50 s, never the intro, hook = the claim. |
| 8 | Variety | 15 formats (F01-F15), rotating title patterns, thumbnail layouts/accents | fixed 60 min documentary, fixed look | Rotate title form, thumbnail accent/side and hook type per episode (thumbnail step). |
| 9 | Growth loop | stats.yml -> status.json daily, cf_analyze, cf_strategy twice daily | no stats (no YouTube token for the BTT account), no analysis | Add BTT to cf_strategy; stats need a BTT YouTube refresh token (secret YT_REFRESH_TOKEN_RELIGION) - missing. |
| 10 | Localization | localize.json, 12 languages via YouTube API | none (Zernio-only account) | Needs the same BTT YouTube token; until then titles stay English. |
| 11 | Schedule | long 20:00, Shorts 15:00/18:00/21:00/23:30 | long 19:00, Shorts 10/13/16/22 | Same times as BAD; channel-aware `reslot c=rel`. |
