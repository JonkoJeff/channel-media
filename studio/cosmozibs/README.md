# Cosmozibs engine

Hand-drawn doodle videos for @Cosmozibs. Space and cosmic history for curious kids, in English.

- `episodes/czNN.json`: one episode (contract: `studio/channels/cosmozibs/FORMAT.md`).
- `engine/build.sh czNN [workers]`: voice (Kokoro, `studio/voice`), procedural music and SFX, timeline, then a long video (1920x1080, 12 fps animated, 24 fps output), 4 Shorts (1080x1920), a thumbnail and 4 covers. Output goes to `engine/build/czNN/`.
- `engine/validate.py`: checks an episode before rendering.
- Drawing: SVG in headless Chromium. rough.js (boiling shapes) and perfect-freehand (pen strokes) are bundled in `libs/` and `pf-build/`, built from their GitHub sources (MIT). Poppins (OFL) is in `fonts/`.
- Code: `core.part` (helpers), `cast.part` (Cosmo, Zib, Bolt, Rocky), `scenes.part` (scene types and the frame renderer), `thumbs.part` (thumbnails). `build.sh` concatenates them into `engine.js` and `thumbs.js`.
- Speed: about 0.1 s per frame per worker. Avoid SVG filters per frame (they cost about 20x): the paper grain is pre-rendered once, and the boil comes from rough.js seeds plus per-character jitter.
- CI: `.github/workflows/cosmozibs.yml` (`ep=czNN`) renders the episode and publishes release `czNN` plus `studio/renders/czNN/result.json` for `zernio.yml`.
