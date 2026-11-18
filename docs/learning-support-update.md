# Learning support update · 18 November 2026

## Changes

- All 20 units and all 100 learning cards open immediately. The original sequence remains the suggested route. Card captions and circles are both links. Every unit workspace also links directly to its five steps.
- Actual practice requirements determine completion and XP. Completing APPLY before other steps no longer incorrectly completes the whole unit. Out-of-order progress is displayed accurately and survives reload.
- Chinese teaching text across readings, vocabulary, questions, options, explanations, patterns, model responses, visual activities and saved work offers optional pinyin. Dotted underlines indicate support; click to open, click again or Escape to close. Native controls retain their semantics; Alt+P reveals Chinese on a focused card/answer. Native dropdowns offer a pronunciation helper. Editing fields remain editable.
- Source vocabulary pronunciation takes priority over automatic readings. Supplementary and sentence pronunciation is generated locally using bundled pinyin-pro 3.29.5 (MIT). Contextual overrides cover common hospitality readings such as 还给 and 同行的游客. Automatic readings are labelled; unfamiliar names and ambiguous readings still require teacher checking. Words embedded only in image pixels cannot be individually clicked; extracted source text supports pinyin.
- Completion, recall, writing submissions, corrected answers and repeat practice give encouragement. Completion gets a lasting on-page acknowledgement and the dashboard recognizes actual completed steps. Repeated practice never creates duplicate XP or an official grade.
- Static builds tag module, style and course URLs by release hash to avoid mixing cached old and new code. Browser student records remain in the existing IndexedDB store.

## Verification

- 43 isolated Python/JavaScript regression tests passed, including the all-100-step completion test, immediate access to every step, out-of-order completion and restart persistence.
- Browser-engine WebAssembly tests passed: 20 lessons, 100 steps, 162 correct objective keys, 124 incorrect choices with exact explanations, writing, teacher view, export and error states.
- Pronunciation checks cover all 268 source vocabulary entries, all source reading paragraphs, and selected contextual polyphones.
- Actual browser checks: opened unit 20 BUILD without preceding steps, revealed title and sentence pinyin by mouse and keyboard, saved a Chinese draft, answered incorrectly then correctly, completed the step and observed encouragement. Reload preserved the exact writing and 1/5 unit progress. At 390 × 844, the page had no horizontal overflow and long pinyin stayed within the viewport above mobile navigation.

This is developer QA, not a classroom trial or a complete human audit of every automatically generated pronunciation.
