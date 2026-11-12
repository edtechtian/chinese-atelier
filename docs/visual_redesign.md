# Chinese Atelier — visual learning adventure

Implemented 30 October 2026, on the existing Python/vanilla JavaScript application. The brand, 20 original lessons, 100 daily steps, source archive, SRS scheduler, student records and teacher tools are retained. There is no new service, account system, paid API or dependency required to run the app.

## What changed

- Today is a compact daily mission centre: real streak, XP, active study goal, due reviews, next step, challenge, weekly activity and achievements. No demonstration statistics are inserted.
- Learning Path contains 20 themed units and 100 connected winding nodes, preserving the existing Discover → Understand → Build → Communicate → Apply stages, unlock rules and mastery states.
- Exercises have focused progress bars, larger controls, immediate explanations, subtle rewards and reduced-motion support. Mobile navigation stays at the bottom.
- Picture Practice adds 92 supplementary activities across all 20 units: 37 picture choices, 12 matching tasks, 18 cloze tasks, 20 open descriptions, and one each of picture sequence, scene-dialogue choice, professional-response choice, room-object identification and sentence ordering.
- Explore the Hotel provides seven illustrated objects, large alternative controls, Chinese/pinyin/meaning/examples and actual personal-phrasebook saving. Explore Thailand links four approximate map locations to source units. Visual Dialogue reveals four newly authored exchanges, then hides the words for rehearsal.
- Visual writing saves to the local server, recovers browser drafts, supports submission and revision-specific teacher feedback, and appears in the portfolio. Teacher evidence summaries include these reviews.

## Content and image scope

The original source extraction, curriculum/lessons.json, remains unchanged: SHA-256 fb184650b9314a43da0a908acfa61e3a8d66715be262a8d537a8ba28b0c5b771. All 20 PPTX files and 282 slides remain accounted for. Chinese and Thai text are retained.

curriculum/visual_learning.json inventories image decisions for all 268 source vocabulary records. **38 records currently have a direct picture mapping; 230 use source context without a literal picture.** The latter include abstract expressions and concrete words for which no accurate image has yet been assigned. They are not presented as fully illustrated. This avoids teaching a SIM card with a phone picture, a bank card with a banknote, or a named attraction with an unidentified photograph. Further image coverage is teacher-editable.

There are 50 reusable image configurations: 16 retained textbook assets (15 photographs and one illustration) and 34 newly authored SVG illustrations. The room exploration has a separate full-scene SVG. Source photographs have local 480/960-pixel WebP derivatives and responsive loading; the original files remain intact. The 15 original photographs total 61,844,698 bytes; their 960-pixel derivatives total 1,260,158 bytes.

Every source image retains its lesson/slide reference and institution attribution. Descriptions distinguish visible features from inferred identity; generic beach/market pictures are not asserted to show a particular venue. Embedded third-party rights have not been independently cleared; these supplied assets are retained for local educational use.

All new prompts, examples, illustrations, hotel objects, dialogue scripts and activities are labelled supplementary and pending teacher review. Original content is separately accessible. Picture recognition does not certify speaking. Open writing receives length checks, not an AI language-quality score or official IB grade. The 40–90-character observations are short supplementary tasks; the existing longer writing, interpretation and communication tasks remain available.

## Learning and persistence

Visual objective answers are checked on the server. Public prompts omit keys/explanations until an attempt. A first correct answer earns two XP per activity; repeat answers cannot farm XP. Image attempts do not advance the SRS schedule or falsely record unaided recall. Saving an object to the phrasebook makes it available for the existing attempt → compare → self-rate retrieval workflow.

Progress and writing use data/state.json through the existing atomic persistence mechanism. Visual records live in visualLearning.attempts and visualLearning.responses. New writing revisions invalidate the current teacher review and retain review history. Teacher review requires the teacher session and current submitted revision. Visual study time uses the existing active-time heartbeat.

The app remains a private, single-student local application. There is no cross-device sync or shared-computer account isolation. Keep the computer, browser profile, data folder, key and exports private.

## Run and use

From /path/to/chinese-atelier:

    python3 server.py --port 8001

Open http://localhost:8001/#/home, then Start Learning or Explore with pictures. Visual modes are at /#/visual. The teacher desk is /teacher; use the locally stored key shown by the normal startup command. No audio, recording or speech-recognition controls are claimed.

## Maintain the content

| File | Responsibility |
| --- | --- |
| curriculum/visual_learning.json | Stable activity IDs, image references/alt text, source references, keys, explanations, criteria, map and dialogue |
| curriculum/visual_source_candidates.json | Retained original-image candidate inventory |
| scripts/build_visual_learning.py | Reusable SVGs and generated visual dataset |
| scripts/validate_visual_learning.py | IDs, source titles/order, vocabulary inventory, assets, slide references and keys |
| public/visual.js | Visual activities, exploration, portfolio and teacher review UI |
| public/adventure-ui.js and public/adventure.css | Dashboard, path and visual styles |
| app/visual.py | Protected keys, attempts, writing and teacher assessment API |

For small corrections, edit visual_learning.json, keep stable IDs/source references, validate and reload the browser. The server reads this config per request; the frontend caches it until a full reload. Changing an answer should also be considered when interpreting earlier attempt history.

The builder regenerates the visual JSON and SVG assets. Reconcile manual visual edits before running it; it does not change original source extraction or SRS logic. Existing WebP derivatives are reused if present. Do not run the earlier source/adaptation authoring pipeline just to change a picture.

    python3 scripts/validate_sources.py
    python3 scripts/validate_adaptations.py
    python3 scripts/validate_visual_learning.py
    python3 -m unittest discover -s tests -v

See docs/visual_redesign_qa.md for tested workflows, evidence and limits.
