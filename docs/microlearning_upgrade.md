# Daily microlearning upgrade — 2026-10-30

## Delivered application

The existing dependency-free Python/JavaScript app now opens on a personalized daily dashboard. It preserves all 20 original 《走遍泰国》 titles, their order, Chinese and Thai source extraction, full source slides, original lesson workspaces, portfolio records and teacher access. No source file or original-only extraction was replaced.

Navigation offers Today, Learning path, Review Centre, Phrasebook, Hospitality challenges, Portfolio and Source library. Student pages do not display teacher controls.

### 100 purposeful steps

The export curriculum/learning_path.json uses the same data-driven path served by the app: 20 units with exactly five steps, rather than equal slide chunks.

1. Discover — curated useful vocabulary, attempted recall and contextual checks; the full vocabulary remains available.
2. Understand — original selected dialogues/readings, source-specific discussion and an evidence-based interpretation response.
3. Build — source patterns, controlled grammar checks and an independent 20+ Chinese-character response.
4. Communicate — live partner/teacher listening, role-play, clarification and a saved transcript/reflection. Self-rehearsal is explicitly labelled.
5. Apply — the original lesson's longer integrated writing task, formative checks and a Chinese reflection.

Most steps allow 8–15 minutes; later extended Apply tasks allow 18. Estimates never create study-time credit. Longer original material remains accessible. Source-specific tasks, models, differentiation and criteria remain in data/curriculum.json.

Steps unlock in sequence. Completed steps stay accessible and reviews are never locked. Completion checks assigned answers, source acknowledgement, real saved/submitted work and reflection. These are practice requirements, not proof of proficiency. Older completed units migrate to five marked steps, with no invented XP. Future archive completion remains an archive record; the new path uses its stricter five-step gates.

### Daily rhythm and rewards

- Editable 10/15-minute goals and 1–7-day weekly rhythm, calendar and forgiving streak. Missed days never erase progress or XP.
- Actual active time: server-measured heartbeats, capped at 30 seconds, with visible-page/recent-interaction checks. Long gaps are excluded; overlapping windows cannot double-credit; midnight intervals split across local dates. This approximates activity, not attention or offline study.
- Review sets of three, four or six items; review-first recommendations when eight or more are overdue. A daily challenge remains stable for its local date as progress changes. A draft is not labelled completed.
- XP: 25 once per step, 2 once per correctly answered objective item, 3 per due/new retrieval scheduling revision, 12 maximum per day for submitted hospitality challenges. Early practice never changes schedule or XP; one zero-XP participation event per item/day may record it.
- Achievements cover first completion, 5/20/50/100 steps, consistency, retrieval mastery and communication challenges. No hearts/lives or punitive notifications.

## Actual SRS rules

This is an explicit **SM-2-inspired adaptive ladder**, not exact SM-2, FSRS or a fitted Ebbinghaus forgetting-curve model. It does not estimate a student's retention probability.

Every record stores ID, first learned/last reviewed/next review timestamps, successful/failed counts, interval, ease, ladder position, mastery and revision. UTC timestamps persist. Calendar reviews use 09:00 in the selected IANA zone; Again uses elapsed ten minutes. Displayed dates use the selected zone and include the year.

- Initial learning without recall schedules day 1 and starts at the next ladder interval. An initial recall on day 0 can instead schedule the first one-day interval.
- At ease 2.5, on-time Good intervals 1, 2, 4, 7 and 16 days produce day 0 → 1 → 3 → 7 → 14 → 30. Good scales the next ladder interval by ease / 2.5; after the ladder it multiplies the previous interval by ease. Cap: 365 days.
- Again retries in ten minutes, increments failures, lowers ease by 0.2 (floor 1.3), resets the ladder and marks relearning.
- Hard uses 60% of the previous interval, rounded, minimum one day; ease decreases 0.15 (floor 1.3); the ladder does not advance.
- Easy uses 1.6 times the larger of the next normal interval and previous interval, rounded, minimum three days; ease increases 0.15 (cap 3.2); the ladder advances.
- Mastered means five or more successful recalls and an interval of at least 30 days. It is a retrieval signal, not a teacher-certified skill.

Overdue items remain due. Active teacher recommendations precede oldest due items; failures identify support needs. Exact/choice errors require Again. Meaning and open production are explicitly self-compared. Models/keys appear after an attempted response. Single-use, expiring, revision-checked tokens prevent stale or replayed schedule updates, including after teacher corrections. Early practice leaves scheduling unchanged, also in archive flashcards.

Formats rotate among Chinese-to-English recall, English-to-Chinese exact production, sentence completion, reconstruction, contextual questions, pattern production and situation responses. Reconstruction uses character pairs labelled as recall scaffolds, not word boundaries. Vocabulary, expressions, grammar, keyed questions, reading, communication and personal phrases are supported. Unknown historical first-learned dates remain unknown on migration.

## Phrasebook and teacher evidence

Source expressions/patterns can be saved and moved among practical themes. Personal sentences need a meaning/usage note, remain labelled unverified and join retrieval. Search and theme filtering work.

Nine supplementary briefs cover welcome/check-in readiness, check-out, reservations, facilities/accessibility, destinations, food enquiries, airport transfer, complaints and a changed plan. They cite a language foundation, state fictional context and provide criteria/extension. They are not textbook material. Existing professional studios remain available.

Build responses and challenges have server saves, browser recovery, submission/revision history and teacher criterion review. Original task autosave/model/portfolio workflows remain. Teacher feedback from both generations contributes to portfolio evidence. Daily learning analytics show 100-step progress, weekly time/activity, retention, objective versus self-rated recalls, grammar difficulties, enrolled items and submissions. Teachers can recommend specific practice and assess a submitted revision. Edits protect stable IDs, required path tasks and original source titles. JSON exports include the full learning state; CSV adds completed/total steps and review/mastery counts per unit. No score is an official IB grade.

## Run and maintain

~~~sh
cd '/path/to/chinese-atelier'
python3 server.py --port 8001
~~~

Open http://localhost:8001; teacher access is http://localhost:8001/teacher. Reload after an upgrade. The local teacher key appears at startup and is stored privately in data/teacher-key. No package install, paid API or external credentials are needed. The listener is 127.0.0.1; this is a single-student local application, not a public multi-user service.

Use Teacher desk → Curriculum editor → Validate & save for lesson corrections; Source collection holds slide review notes. Existing IDs/extraction are protected. The live path derives from current lesson content. Run python3 scripts/build_learning_path.py to update the inspectable export. Core vocabulary selection and the nine supplementary brief definitions live in app/learning.py. README.md documents the existing adaptation-authoring pipeline; back up and reconcile teacher edits before rebuilding.

Learning records remain in atomic private data/state.json. First migration retains data/backups/state-before-microlearning-*.json. Back up state, curriculum, teacher key and source assets; keep student exports private. No student data is sent to external services.

## Verified results and limits

See docs/upgrade_qa_report.md and docs/qa/upgrade-2026-10-30/ for observed evidence. The original extraction SHA-256 remains fb184650b9314a43da0a908acfa61e3a8d66715be262a8d537a8ba28b0c5b771.

No supplied/recorded audio, speech recognition or automated language-quality scoring is claimed. Listening needs a partner/teacher and speaking needs observed evidence. Reminders are in-app, with no background delivery. A live Grade 11 student usability study has not occurred. Source visual/font omissions and uncertain original exercise-answer mappings still need teacher review, especially L7 S12 and standalone EMF placements on S4/S6/S8. Editorial adaptations and new activities remain pending teacher approval.
