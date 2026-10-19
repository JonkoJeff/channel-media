# Opdracht voor Claude Code: zet de Cosmozibs-fabriek op

Plak alles onder de streep in Claude Code, gestart in een herdr-pane in de map van `channel-media`
(`pwsh -File studio/factory/hq.ps1` draait al, of start het eerst). Werk op branch `cosmozibs`; merge naar `main` pas als stap 7 groen is.

---

Je zet een derde kanaal op in onze bestaande kanaalfabriek: **Cosmozibs** (@Cosmozibs), Engelstalige ruimte- en kosmische-geschiedenisvideo's voor nieuwsgierige kinderen van 9 tot 15. Alles wat je nodig hebt staat al op branch `cosmozibs`. Lees eerst, in deze volgorde:
`studio/channels/cosmozibs/STYLE.md`, `FORMAT.md`, `config.json`, `series.json`, `studio/cosmozibs/episodes/cz01.json` (het voorbeeld), `studio/factory/README.md`, `studio/factory/config.json`, `studio/factory/agents.json`.
Werk met de ponytail-skill: kleinste complete wijziging, hergebruik wat er is. Geen nieuwe fabriek: Cosmozibs wordt een extra kanaal in dezelfde factory, hetzelfde dashboard en dezelfde Zernio-route.

## Rolverdeling (vast, eigenaar 19 okt 2026)
| Werk | Wie | Taaktype |
|---|---|---|
| Marktonderzoek: trends, outliers, eigen cijfers → volgende 7 afleveringen in `series.json` | Claude | `cz_research` (prompt staat klaar) |
| Script: complete aflevering-JSON met bronnen, beschrijving, tags, thumbnail- en cover-specs | Codex | `cz_episode` (prompt staat klaar) |
| Redactie: validator + feitencheck + toon, max. 1 fix-ronde | Claude (haiku) | `cz_audit` (prompt staat klaar) |
| Fix na een afgekeurde audit | Codex | `cz_fix` (maak naar het voorbeeld van `rel_fix`) |
| Thumbnail (16:9) en 4 Short-covers (9:16) schilderen, stijl van `refs/thumb_example.jpg` | Codex | `cz_thumb`, `cz_cover` (prompts staan klaar) |
| Renderen: video en 4 Shorts | GitHub Actions | `cosmozibs.yml` (staat klaar, nul tokens) |
| QC, inplannen en posten via Zernio | channel-operator (Claude) | bestaande route |

## Stappen
1. **Factory-config.** Voeg in `studio/factory/config.json` het kanaal `cosmozibs` toe en de taaktypes `cz_research` (prefer claude, model sonnet), `cz_episode` (prefer codex, fallback claude), `cz_audit` (prefer claude, model haiku), `cz_fix` (prefer codex). Neem de timeouts en watermarks over van `rel_*` en stel de buffer zo in dat er altijd 3 afleveringen klaarstaan. Voeg aan `factory.ps1` alleen toe wat nodig is om de context pack voor cosmozibs te bouwen (STYLE + FORMAT + learned_cosmozibs.md + lessons + insights + series + het voorbeeld cz01.json). Elke deliverable begint met `STYLE <hash>`, net als bij de andere kanalen.
2. **Keten.** `cz_research` (wekelijks, en zodra `series.json` < 7 open afleveringen heeft) → `cz_episode` per afleverings-id → `python3 studio/cosmozibs/engine/validate.py` → `cz_audit` → bij slagen: schrijf het JSON-bestand naar `studio/cosmozibs/episodes/<id>.json`, push, start `cosmozibs.yml` met `ep=<id>`. Bij afkeuren: één `cz_fix`, daarna neemt Claude het over.
3. **Herdr.** Geef Cosmozibs een eigen tab in workspace "CrazyFacts HQ" (of hernoem die naar "Channel HQ"): dashboard-regel met buffer, laatste render, laatste post en tokens per agent. Geen extra agents nodig; de bestaande codex1/codex2/claude1 pakken cz-taken via het pull-model.
4. **Zernio.** De key staat als GitHub-secret: `ZERNIO_API_KEY_3`, of `ZERNIO_API_KEY` als het hetzelfde Zernio-account is (vraag het de eigenaar als het niet duidelijk is). Draai `zernio.yml cmd=accounts` en zet de YouTube-account-id onder `youtube.cosmozibs` in `studio/yt/zernio.json`. Pas in `studio/yt/zernio.py` alleen aan wat kanaalspecifiek is: de key-keuze voor cosmozibs, de Short-tekst "Full episode on the channel" (niet "calm 2.5-hour video"), playlist "Cosmozibs Shorts", en `madeForKids` volgens `config.json`. Maak de 8 playlists uit het account-setup-document aan met `zernio.py playlist`. **TikTok:** de eigenaar koppelt het TikTok-account in Zernio. Zet de account-id na `cmd=accounts` onder `tiktok.cosmozibs` in `zernio.json`. `zernio.py shorts` stuurt dan elke Short in dezelfde post ook naar TikTok: publiek, AI-label aan, maximaal 15 per dag. Dat is al gebouwd, en de andere kanalen merken er niets van zolang zij geen TikTok-id hebben.
5. **Planning (US Eastern, `config.json` cadence).** Doordeweeks de lange video om 14:00 ET, in het weekend om 08:00 ET. De Shorts komen 270, 420, 660 en 1020 minuten na de lange video: `zernio.yml cmd=shorts b=YYYY-MM-DDTHH:MM@270,420,660,1020`. Zernio krijgt de tijdzone America/New_York. Na 28 dagen herijk je het ritme op YouTube Studio → Doelgroep → "Wanneer je kijkers op YouTube zijn". Nooit twee lange video's op één dag, en nooit iets dubbel posten.
6. **Leren.** Dagelijks: de cijfers van Cosmozibs naar `studio/channels/cosmozibs/insights.md`, gecontroleerde video's en regels naar `lessons.md`. Een stijlwijziging komt alleen als `PROPOSAL:` binnen en wordt alleen door de Claude-analist naar `studio/factory/learned_cosmozibs.md` gepromoveerd. Voeg in `studio/trends/topics.json` drie regels toe voor cosmozibs (space facts for kids long · space facts short · what if space).
7. **Testen vóór main.** GitHub start een workflow pas als die op `main` staat. Zet daarom eerst alleen `.github/workflows/cosmozibs.yml` op main; dat raakt de andere kanalen niet. Start dan `cosmozibs.yml` met `ep=cz01` en ref `cosmozibs`, en controleer de release: een lange video van 8:05-8:20, 4 Shorts onder de 58 seconden, `thumb.jpg` en 4 covers in `studio/covers/`. Laat daarna één volledige ronde `cz_episode` → `cz_audit` → render lopen voor `cz02`. Pas als beide goed zijn: merge `cosmozibs` naar `main` en zet de dagelijkse taak aan.
8. **Doorlopen zonder einde.** Het kanaal stopt niet: zodra de buffer onder 3 komt, genereert de controller nieuwe afleveringen. Zodra `series.json` minder dan 7 open afleveringen heeft, plant `cz_research` de volgende week.

## Thumbnails (eigenaar 19 okt 2026, vervangt de getekende thumbnails)
- Codex schildert met zijn image-tool elke lange thumbnail (`cz_thumb` → `studio/channels/cosmozibs/thumbs/czNN.jpg`) en elke Short-cover (`cz_cover` → `studio/covers/czNN_<seg>.jpg`). Voeg ze in `studio/factory/config.json` toe zoals `rel_thumb`/`cf_cover` (prefer codex, geen fallback, `nopack`) en zet ze in `$ImageTypes` in `factory.ps1`.
- Stijlbron: `studio/channels/cosmozibs/refs/thumb_example.jpg` (16:9, 1672x941). Platte handgetekende doodle, één groot thema-object met gezicht, klein reagerend crewlid, tekst met de hand getekend in de tekening (bubbelletters wit + geel). Nooit geplakte tekst of tekstvakken.
- Volgorde: `cz_episode` → `cz_audit` → `cz_thumb` + 4× `cz_cover` → commit de jpg's → pas dan `cosmozibs.yml`. De workflow gebruikt de geschilderde versies; de getekende zijn alleen nog de nood-fallback.
- Claude controleert elk beeld (spelling, max 3 woorden, stijl, niets in de gecropte rand) en keurt één keer af; daarna maakt Codex het opnieuw.
- Voor een al ingeplande post: commit de nieuwe jpg en draai `zernio.yml cmd=rethumb a=czNN`. Een al gepubliceerde video krijgt de thumbnail via YouTube Studio.
- Kanaal is (nog) niet geverifieerd (eigenaar 19 okt): YouTube toont dan geen eigen thumbnail bij lange video's. Upload ze toch via Zernio; zodra het kanaal ooit geverifieerd is, draai `rethumb` voor wat nog gepland staat. Shorts: de cover gaat mee als post-thumbnail (ook TikTok).

## Harde regels
- Keys alleen als GitHub Actions-secret, nooit in de repo, CLAUDE.md of een log. De repo is publiek.
- Elk getal in een script heeft een bron-URL. NASA, ESA en JPL eerst.
- Geen stemeffecten: geen robotstemmen. Stemmen staan vast in `config.json`.
- Nooit titels, thumbnails of teksten van andere kanalen kopiëren, alleen het patroon. Nooit een oud script hergebruiken met alleen een ander onderwerp (YouTube-beleid "inauthentic content").
- Kindvriendelijk: geen enge ongelukken, geen doden.
- Een nieuw scènetype voegt Claude toe in `studio/cosmozibs/engine/scenes.part` en in de lijst in `FORMAT.md` en `validate.py`. Codex mag alleen bestaande scènetypes gebruiken.
- Werk `CLAUDE.md` bij: drie actieve kanalen (Brain After Dark, Belief Through Time, Cosmozibs).
- Sluit elke run af met een kort rapport: wat is gemaakt en ingepland, wat faalde, wat de eigenaar moet doen.
