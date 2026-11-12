# 《走遍泰国》 source-material audit

Audit date: 2026-10-29. Source directory: /path/to/走遍泰国/. Original copies are preserved read-only by convention in the workspace sources/ folder under hash-based filenames. The original filenames and full SHA-256 hashes are recorded in curriculum/lessons.json.

## Inventory

**20 of 20 numbered lessons found. 20 readable PPTX files. No missing lessons, unreadable packages or exact duplicate files.** All original slide orders were read from presentation.xml, rather than sorting slide filenames.

| Lesson | Exact original filename | Title on source slide | Slides | Extraction | Issues |
|---:|---|---|---:|---|---|
| 1 | 第1课 落地签太方便了！.pptx | 落地签太方便了! | 17 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 2 | 第2课 泰国我来啦！.pptx | 泰国我来啦！ | 13 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 3 | 第3课 到酒店了.pptx | 到酒店了 | 13 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 4 | 第4课 请问，大皇宫怎么走？.pptx | 请问，大皇宫怎么走？ | 10 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 5 | 第5课 我们去银行换钱.pptx | 我们去银行换钱 | 11 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 6 | 第6课  坐嘟嘟车还是出租车？.pptx | 坐嘟嘟车还是出租车？ | 11 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 7 | 第7课 清迈有很多寺庙.pptx | 清迈有很多寺庙。 | 15 | Source text/tables/images extracted; rendered | S4: unsupported_embedded_format; S6: unsupported_embedded_format; S8: unsupported_embedded_format; S12: image_only |
| 8 | 第8课 爬山累不累.pptx | 爬山累不累？ | 11 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 9 | 第9课 尝一尝泰式炒面吧！.pptx | 尝一尝泰式炒面吧！ | 11 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 10 | 第10课  我们几点去机场？.pptx | 我们几点去机场？ | 12 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 11 | 第11课 这里真漂亮PPTX.pptx | 这里真漂亮 ! | 13 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 12 | 第12课 这件衣服多少钱？.pptx | 这件衣服多少钱？ | 15 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 13 | 第13课  街上变得热闹了.pptx | 街上变得热闹了 | 13 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 14 | 第14课 一起去看日出，怎么样？.pptx | 一起去看日出，怎么样？ | 14 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 15 | 第15课   这家比那家近一点儿.pptx | 这家比那家近一点儿。 | 20 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 16 | 第16课  泰国的水灯节浪漫极了!.pptx | 泰国的水灯节浪漫极了! | 16 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 17 | 第17课    泰国的见面礼和中国一样吗？.pptx | 泰国的见面礼和中国一样吗？ | 16 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 18 | 第18课 泼水的人越来越多了！.pptx | 泼水的人越来越多了！ | 17 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 19 | 第19课 把这个花篮送给老师.pptx | 把这个花篮送给老师 | 17 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |
| 20 | 第20课 不要穿鞋进佛殿.pptx | 不要穿鞋进佛殿 | 17 | Source text/tables/images extracted; rendered | Teacher verification of visuals and extracted layout pending |

## Coverage and limits

- 282 slides; 281 contain selectable text; one is image-only (L7 S12).
- 93 table objects; 280 original numeric vocabulary rows (including intentional repetition). Non-tabular phrases, names and labels are preserved in slide text/text blocks.
- 847 embedded picture placements, including repeated/decorative pictures. This is not a count of unique educational images.
- No native chart objects or embedded audio/video files were found in any of the 20 PPTX packages. No listening audio or transcript is fabricated.
- Three EMF picture placements in L7 S4, S6 and S8 cannot be displayed as standalone browser images; the original package retains them. Full-slide renders preserve their appearance if conversion succeeds.
- Six slides contain extracted speaker-note text. Hidden slides, if any, remain in source sequence.
- Exact text, pinyin, Thai glosses, original table cells, shape text runs and layout coordinates are kept. No missing English translations or objectives are invented in the original-only dataset.
- Source exercise slides and displayed completions / word banks are preserved separately. Where text order cannot reliably pair a blank and an answer, the mapping is explicitly unverified; no answer is guessed.
- Lesson 8 includes both 素帖山 and 素贴山, and an example calls the Grand Palace a temple. Original wording is retained and flagged for teacher review.
- Lesson 19 summarizes 把 in terms of position change but also gives 翻译成, a transformation example. The adaptation notes identify this teaching clarification.
- Source visa procedures, fares, entrance fees, travel durations, store layouts, festival schedules and activity descriptions are historical learning context. They have not been verified as current operational information.
- Cultural comparisons are descriptions in the source, not universal claims about every person. Review national generalizations, greeting practices, ceremony participation and site-specific rules before teaching or applying them.

## Integrity and separation

- curriculum/lessons.json contains original source content only. Every slide, vocabulary table row, dialogue, exercise, answer display and visual placement has a filename, file hash, lesson and slide reference.
- curriculum/adaptation_notes.md contains proposed editorial adaptations. They are not labeled teacher-approved.
- data/curriculum.json is the separate application integration dataset containing clearly labeled source extracts, editorial translations/explanations and newly authored activities.
- No source file was modified. Run python3 scripts/build_source_audit.py to regenerate these records after extraction / visual rendering.

## Preview font issue (important)

All 282 slides have preview images, but the local LibreOffice renderer omits some selectable Chinese and Thai glyphs. These previews are **not faithful text renderings** and are used only to inspect retained pictures / diagrams. The original OOXML extraction contains both languages. A readable PDF export would improve final layout verification and answer-to-blank checks. No missing preview glyph has been guessed.

Per-lesson direct visual observations are stored separately in curriculum/visual_observations.json. They are editorial descriptions, not textbook quotations.
