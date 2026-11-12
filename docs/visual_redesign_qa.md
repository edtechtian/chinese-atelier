# Visual redesign — QA results

Date: 30 October 2026. This is developer/Chinese-teacher simulation, not an observed study with a real Grade 11 student. Automated and browser tests use isolated temporary records at localhost:8004. No QA writing, ratings or XP were inserted into real student records.

## Automated coverage

The full suite passes **41 tests**. The final log is docs/qa/visual-redesign-2026-10-30/automated-tests.log. These include the prior 100-step completion/SRS/privacy/source regressions plus new visual tests.

| Actual check | Result |
| --- | --- |
| 20 original titles/order, 20 source files, 282 slides, source hashes and references | Pass; original extraction hash unchanged |
| All 100 step renderers and completion gates, unlock/mastery rules | Pass by renderer and actual HTTP tests |
| SRS ratings, due dates, early recall, replay restrictions, migration, time-zone boundaries, active-time overlap protection | Pass |
| All 92 visual renderers and all 268 vocabulary mapping records | Pass |
| All 72 visual objective keys/explanations, wrong answer, repeated XP cap, public key hiding | Pass by real HTTP requests |
| Visual drafts, submission minimum, teacher access, criteria, revision invalidation and restart persistence | Pass by real HTTP requests |
| Invalid visual requests leave prior records unchanged | Pass |
| Source/adaptation/visual validators, Python compilation and seven frontend module syntax checks | Pass |

Stored-key consistency is not a claim that every distractor and pedagogical judgement has been approved by a teacher. All editorial material remains labelled pending teacher review.

## Browser workflows actually exercised

| Action | Observed result |
| --- | --- |
| Open fresh Today dashboard | Real zero-state statistics and next action; later actual QA XP/review status updates |
| Enter first Discover step | Real original vocabulary, source references, contextual illustration and optional pinyin/meaning |
| Picture choice: deliberately choose 房卡 for 入住, then correct it | Gentle explanation, correct Chinese key, two XP on first success; retained after reload |
| Picture matching and cloze | Actual selections and Chinese entry accepted with explanations; live completion count updates |
| Check-in picture sequence | Welcome → confirm → explain → check accepted; explanation distinguishes fictional role-play from legal procedure |
| Room-object picture challenge | Room key card identified correctly; feedback distinguishes it from passport |
| Sentence order | 您好，我们要办理入住。 accepted and explained; checked against the cited original dialogue |
| Open visual writing | Exact Chinese text saved, equality checked after refresh, then submitted |
| Teacher review of visual writing | Protected entry; saved four levels of 3/4 plus concrete feedback; exact comment and scores retained in form |
| Student portfolio | Exact saved writing and teacher feedback visible; four teacher evidence averages include this review |
| Hotel exploration and phrase saving | Object changes definition; 房卡 saved to real personal phrasebook/review queue |
| SRS after phrase saving | Own response required; compare shows meaning/example; Good earns three XP and schedules 31 Oct 2026 09:00 Asia/Bangkok; refresh preserves date and Upcoming count |
| Thailand map | Selecting 普吉岛 changes source photograph, guide task and links to Units 11 and 20 |
| Visual dialogue | One exchange revealed, all four revealed, words hidden for rehearsal; honest no-audio wording |
| Teacher Daily learning / Student work / Source collection | Visual evidence and response available; source table has 20 ordered original files with slide counts and pending-review status |
| 100-node path | DOM contains 100 nodes and 20 original unit titles; first available node opens the actual lesson |
| Controlled missing image | QA-only missing passport asset produces an Image unavailable fallback, not a blank/broken layout; fixture removed afterward |
| Unknown activity | Clear Visual activity not found message with a clearly labelled unit-return link |

The two scene-dialogue/professional-response choice activities were exercised by API and renderer tests, not separately clicked in the browser. All 92 activities were rendered automatically; a human browser walkthrough of every activity is not claimed. The earlier complete first-unit browser walkthrough is separately documented in docs/upgrade_qa_report.md.

## Responsive and visual checks

375×812, 768×1024 and 1366×900 viewports were used. Today, Path, Review, focused room activity, visual hub, hotel exploration, map, dialogue, teacher work and teacher analytics were checked on representative sizes. The measured pages had document scroll width equal to viewport width. Mobile bottom navigation was clicked to reach Path. The last path caption clears the milestone reward; all desktop units had approximately 33 pixels between them. Large alternative hotel controls remain available on phones.

Measurements and screenshots are in docs/qa/visual-redesign-2026-10-30/. Screenshots with progress are QA records. The final live-dashboard image is the separate personal-use app. Viewport overrides were reset. No browser console errors were returned by the final QA log inspection.

## Defects corrected during this redesign

1. New visual attempts initially updated completion only on reload; the focused progress bar now updates on answer.
2. Visual teacher reviews were absent from portfolio evidence averages; criterion labels now map to the existing IDs.
3. A hanging-lantern drawing was unsuitable for 孔明灯; the drawing now shows a floating paper sky lantern with open base and flame.
4. Hotel markers were too small for phone use; larger equivalent controls were added. Passport and key card have distinct visible features.
5. The last path caption could crowd its milestone reward; track spacing was increased and measured again.
6. Original-lesson empty states could imply no work existed despite saved visual writing; labels now identify the original-lesson section.
7. Teacher-sidebar picture navigation used a teacher-relative hash; the link now returns to the student visual route.
8. Large source photos loaded the full files; responsive local derivatives now reduce transfer size while preserving originals and source attribution.

## Remaining limits

- 38 of 268 source vocabulary records have literal picture mappings. The remaining 230 explicitly use context/no verified picture; coverage is not claimed complete.
- L7 S12 remains image-only, and L7 S4/S6/S8 contain standalone EMF placements. Preview glyph omissions and ambiguous original answer/blank relationships still need teacher review. No missing labels were invented.
- Supplemental material and image interpretations need teacher approval. There is no official IB scoring, automated speaking assessment, recorded listening audio or real-student usability study.
- Thailand map positions are schematic; photographs do not prove exact locations. Historical tourism facts are not live travel advice. Third-party image rights are not independently cleared.
- Persistence is local, with browser draft recovery; there is no cloud sync, push reminder, shared-device student isolation or public deployment security claim.
