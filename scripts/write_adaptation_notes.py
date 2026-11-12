#!/usr/bin/env python3
"""Render the completed editorial specifications as traceable teaching notes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = json.loads((ROOT / 'curriculum/lessons.json').read_text())
    app = json.loads((ROOT / 'data/curriculum.json').read_text())
    specs = json.loads((ROOT / 'curriculum/adaptations.json').read_text())
    by_id = {lesson['id']: lesson for lesson in app['lessons']}
    originals = {lesson['id']: lesson for lesson in source['lessons']}
    criteria = {criterion['id']: criterion['label'] for criterion in app['criteria']}
    lines = [
        '# Completed Grade 11 Chinese B adaptations', '',
        'As of 2026-10-29. All 20 editorial units are integrated and available for teacher review. ',
        'These adaptations are newly authored or editorial, not original textbook content and not teacher-approved. ',
        'The separate authoritative extraction is `curriculum/lessons.json`. The application dataset is `data/curriculum.json`.', '',
        '## Emmalyne’s learning design', '',
        'Begin with fluent Chinese reading, then diagnose listening, spoken formulation and writing independently. ',
        'English instructions and explanations support Chinese communication. Pinyin and source Thai glosses are optional. ',
        'Thai/German comparisons are selective tasks about meaning or register, not automatic trilingual translations. ',
        'Every unit follows Understand, Communicate and Apply professionally, with a subject-appropriate tourism connection. ',
        'Each unit has explicit retain, extend, scaffold and interactive decisions. All full source slides remain accessible.', '',
        '## Provenance and assessment', '',
        '- `textbook`: extracted original Chinese readings and source examples, with file/slide references.',
        '- `adaptation`: editorial explanations, glosses and teaching decisions linked to original language.',
        '- `supplementary`: newly authored questions, tasks, models, discussion guides, usage chunks and rubrics.',
        '- New objective questions have separate authored answer keys and explanations. They are not claimed as original textbook keys.',
        '- Writing and speaking use task-specific selections from six criterion dimensions. Automated writing feedback counts characters and prompts review; teacher assessment requires evidence.',
        '- Live listening needs a partner/teacher. No audio files, recording or speech recognition are claimed.',
        '- Course completion and teacher levels do not constitute an official IB grade.', '',
        '## Source review boundaries', '',
        'All 20 PPTX packages and 282 slides were extracted, including selectable Chinese and Thai. Full semantic verification of visuals and original exercise/answer mappings remains for teacher review. ',
        'Lesson 7 slide 12 is an image-only fruit collage. Some EMF placements and local preview font omissions remain documented in `source_inventory.md`. ',
        'Do not present old prices, schedules or rules as current travel information. Cultural descriptions are attributed and discussed with attention to individual choice.', '',
        '## Lesson adaptations', ''
    ]
    for spec in specs['lessons']:
        lesson = by_id[spec['id']]
        original = originals[spec['id']]
        lines += [f"### {lesson['number']:02d} — {original['titleFromSourceSlide']}", '',
                  f"Original source: **{original['sourceFile']['filename']}**, {original['sourceSlideCount']} slides. Stable lesson ID: `{spec['id']}`.", '',
                  f"**Teaching focus:** {spec['subtitle']}. Estimated time: {spec['minutes']} minutes.", '',
                  f"**Tourism/hospitality application:** {spec['hospitality']}", '',
                  f"**Diagnostic:** {spec['pedagogy']['diagnostic']}", '',
                  '**Learning objectives**', '']
        lines += ['- ' + objective for objective in spec['objectives']] + ['', '**Source decisions**', '']
        for decision in spec['pedagogy']['decisions']:
            lines.append(f"- **{decision['action'].title()}:** {decision['content']} Sources: {', '.join(decision['sourceRefs'])}.")
        lines += ['', '**Sequence**', '']
        for stage in spec['pedagogy']['sequence']:
            lines.append(f"- {stage['stage']} ({stage['minutes']} min): {stage['activity']}")
        lines += ['', f"**Reading and language coverage:** {len(lesson['readings'])} selected source texts, {len(lesson['vocabulary'])} vocabulary/expression cards, {len(spec['patterns'])} language patterns and {len(spec['questions'])} objective items.", '', '**Language development**', '']
        for pattern in spec['patterns']:
            lines.append(f"- **{pattern['title']}:** {pattern['explanation']} Distinction: {pattern['pitfall']} Application: {pattern['application']} Sources: {', '.join(pattern['sourceRefs'])}.")
        lines += ['', '**Newly authored tasks**', '']
        for task in spec['tasks']:
            lines += [f"**{task['title']}** (`{task['id']}`, {task['type']})", '', task['prompt'], '',
                      f"Success criteria: {'; '.join(task['successCriteria'])}", '',
                      f"Assessment dimensions: {', '.join(criteria[c] for c in task['criteria'])}.", '',
                      f"Optional scaffold: {'; '.join(task['scaffold'])}", '',
                      f"Extension: {task['challenge']}", '',
                      f"Source anchors: {', '.join(task['sourceRefs'])}. Model: {task['modelScope']}, newly authored and stored separately from the source.", '']
        lines += ['**Live listening and speaking**', '']
        lines += ['- ' + instruction for instruction in spec['liveListening']['instructions']]
        lines += ['', f"Focus: {spec['liveListening']['focus']} Sources: {', '.join(spec['liveListening']['sourceRefs'])}.", '',
                  f"**Multilingual support:** {spec['pedagogy']['multilingual']}", '',
                  f"**Reflection:** {spec['pedagogy']['reflection']}", '']
        for note in spec['culturalNotes']:
            lines += [f"**Editorial/source caution — {note['title']}:** {note['text']} Sources: {', '.join(note['sourceRefs'])}.", '']
    (ROOT / 'curriculum/adaptation_notes.md').write_text('\n'.join(lines) + '\n')
    print(f"Wrote completed adaptation notes for {len(specs['lessons'])} lessons.")


if __name__ == '__main__':
    main()
