# Script format (ChatGPT writes it, the machine only parses it: no thinking needed)
One file per episode: `NN.txt` (NN = number in episode_list.md, e.g. 01.txt). ~60 min, ~7,800 spoken words at 130 wpm.
Header lines, then scenes. A scene = one block of narration with its start time and a visual cue.

```
TITLE: The Creation of the Universe
DESC: <=4000 chars, YouTube description, neutral, with chapter list
TAGS: bible, creation, genesis, religion
SOURCES: plain strings (books, scholars, museums), no invented DOIs
SHORTS: 4 lines of  START-END | hook title   (each 35-58 s, on scene boundaries, from different parts of the video)
---
[00:00:00] NARRATION: <spoken text, 1-6 sentences, plain English, no stage directions>
VISUAL: <what to show: e.g. "Creation of Adam, Michelangelo, Sistine Chapel" or "map: Mesopotamia 2000 BCE">
SOURCE: wikimedia | met | smithsonian | rijksmuseum | loc | map | text-card
[00:00:14] NARRATION: ...
```
Rules: timestamps rise, scenes of 6-20 s of speech; first scene is the 20 s hook; last scene ends softly; separate scripture / tradition / historians / uncertain in the wording; paraphrase scripture; never depict Prophet Muhammad; scripts for Hindu/Buddhist/Christian figures follow each tradition's norms. Add `CHAPTER: <name>` lines before the scene where a chapter starts.

VISUAL must be SPECIFIC and searchable in museum archives: name the artwork + artist or the exact place/object, in English (e.g. "The Deluge, Gustave Dore", "Kaaba Mecca", "Ziggurat of Ur", "Michelangelo Creation of Adam"). Avoid vague lines like "ancient scene". The picture is found by that text and its file title must contain a word of it; if nothing matches, a gold text card is used.
