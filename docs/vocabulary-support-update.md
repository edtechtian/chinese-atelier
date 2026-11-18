# Vocabulary and language support update

Release: 68969ca6a5a3. Public entry: https://edtechtian.github.io/chinese-atelier/site/#/flashcards

- Dedicated deck contains all 268 vocabulary/expression records from the verified 20-lesson dataset, in original lesson order. This is the verified vocabulary dataset, not a claim to enumerate every distinct word occurring in the slides.
- Search, per-lesson filters, new/due/support/learning/spaced-recall views, Chinese-to-meaning and meaning-to-Chinese directions, reveal-before-rating, and per-lesson coverage.
- Ratings share the existing spaced repetition schedule. Early practice preserves the due date, earns no XP, and is recorded separately. Teacher analytics distinguishes self-ratings from objectively checked answers. Self-ratings do not certify mastery.
- Pinyin is revealed for individual words/phrases. Original vocabulary pinyin takes priority; contextual automatic pronunciation is labelled.
- Selecting a stored course sentence displays English and Thai from a local 2,725-entry cache. No selected text or student writing is sent to a runtime translation service. Translations are supplementary machine translations pending teacher review; several sampled errors were corrected editorially. Unmatched selections show an explicit unavailable state. Image-pixel text is not interactive.
- Every unfinished learning-path node is grey, including available/in-progress/suggested nodes. Completed and spaced-recall milestone nodes are green. All 100 nodes remain clickable. The unit header step markers follow the same rule.
- All assigned vocabulary card pictures now come from original PPT assets: 19 verified mappings. The remaining 249 records use text and source sentences because a suitable picture has not been verified. Picture attribution identifies the actual image's lesson/slide, including cross-lesson reuse. Existing supplementary scene illustrations and activities remain labelled and preserve their stable IDs.

## Verification performed

- Full Python/HTTP/frontend suite: 45 tests passed. Uses isolated temporary student data and localhost test servers.
- WebAssembly edition: all 20 lessons/100 steps, 162 correct answers, 124 incorrect-answer explanations, vocabulary endpoint and late-lesson rating, writing, teacher view, exports and invalid requests passed.
- Browser at local static preview: lesson 20 direct entry, phrase pinyin, Again/Good rating, refresh persistence of review coverage and current card, real sentence drag-selection with both translations, empty search, original PPT sky-lantern image load, and teacher self-rating analytics checked.
- Path DOM: 100 clickable nodes; 98 available and one in-progress node grey (rgb 228,231,229), one completed node green (rgb 88,204,2).
- Mobile 390×844: deck, original image and empty state fit without horizontal overflow (scrollWidth 390).

## Editing

Vocabulary and examples: `data/curriculum.json` (preserve IDs and source references). Original extraction remains separate in `curriculum/lessons.json`.
PPT image mappings: `scripts/source_vocabulary_images.py` and `curriculum/visual_learning.json`. Rebuilding image derivatives requires Pillow and the original extracted images. Original PPTs are not bundled in the public release.
Translations: `public/language-support.json`. A teacher may correct the English/Thai and set `reviewStatus` to `teacher_reviewed`. Rebuild with `scripts/build_language_support.py`; translation generation uses a best-effort public endpoint only when explicitly run with `--translate`.
Public build: `python3 scripts/build_browser_site.py` in the release directory. Browser storage is device-specific; export a portfolio backup before clearing site data or changing devices.
