# Chinese Atelier

A personal Chinese learning adventure for a Grade 11 Chinese B learner, focused on tourism and hospitality. Built with Python standard-library HTTP APIs and vanilla JavaScript/CSS. No paid service, API key, database or package installation is needed.

## Use online

**Open https://edtechtian.github.io/chinese-atelier/ to start learning in your browser.** No installation or local server is required. Progress and writing stay in this browser on this device; export portfolio backups before clearing site data. The online teaching view sees the same browser records and is not authenticated or cloud-synced. See [browser edition details](docs/browser_edition.md).

## Run locally

Python 3.10+ is required.

```sh
git clone https://github.com/edtechtian/chinese-atelier.git
cd chinese-atelier
python3 server.py --port 8001
```

Open http://localhost:8001/#/home. Teacher view: http://localhost:8001/teacher. The first launch generates a private teacher key and empty student records; the key is shown in the local terminal. Stop with Control-C.

**GitHub Pages runs the browser edition using WebAssembly. The repository URL is the source code; the Pages URL is the usable app. The original Python HTTP server remains a separate local application.** The server deliberately accepts localhost requests only. Do not expose it publicly without adding appropriate authentication, per-student data separation and production hosting.

## Included features

- 20 original source-linked units × 5 daily learning steps (100 nodes).
- Daily missions, actual XP/streak tracking, active-time goals and adaptive spaced review.
- 268 vocabulary records, source readings, language development, objective exercises and open writing/role-play.
- 92 supplementary visual activities, hotel exploration, schematic Thailand map and visual dialogue.
- Persistent writing and progress, personal phrasebook, portfolio and protected teacher review/editor tools.
- Responsive desktop, tablet and mobile layouts; reduced-motion support.

All 20 curriculum units remain in order. Original source text, editorial adaptations and supplementary activities are labelled separately. Image coverage is partial: 38 vocabulary records have direct mappings, and 230 use context support. No supplied audio, recording, speech recognition or official IB grading is claimed.

## Publication boundaries

The repository includes application code, structured curriculum, supplementary illustrations and optimized visual-learning images. Original PPTX files, the full source-image archive, personal student records, teacher keys, backups and private QA screenshots are excluded. Some original-archive images/downloads will show unavailable until the original archive is installed. Read NOTICE.md for attribution and content rights.

Machine-local folder metadata is redacted in this publication copy. Source wording, lesson order and stable lesson/slide IDs are preserved; its extracted dataset hash consequently differs from the private original audit. Metadata redaction does not constitute a new source extraction.

## Check and maintain

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_adaptations.py
python3 scripts/validate_visual_learning.py
```

Full original-source validation, import and render tools require the separately supplied PPTX/asset archive. Their absence must not be reported as verified original files. The source inventory documents the earlier local audit and unresolved slide review; it is not proof that the originals are included here.

For ordinary teaching edits, use Teacher desk → Curriculum editor. The runtime course is data/curriculum.json. Visual activities/images are configured in curriculum/visual_learning.json. Original extraction is curriculum/lessons.json. Back up and reconcile teacher edits before rerunning generation scripts, which replace generated curriculum fields.

See docs/microlearning_upgrade.md and docs/visual_redesign.md for architecture, scheduling and editing details. The historical QA report describes the local development version, not a live study with a student. All educational adaptations remain subject to teacher approval.

## Privacy

Student records and the teacher key are generated locally and ignored by Git. No analytics or assessment data is sent to a third-party service. Keep local records and exports private. This is a single-student local app, without cross-device sync or shared-computer account isolation.
