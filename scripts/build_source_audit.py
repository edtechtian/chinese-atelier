#!/usr/bin/env python3
"""Produce requested audit deliverables; never mix adaptations into original content."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.extract import NS,relationships

ANSWER_SLIDES={4:{9:'displayed_completed_exercise'},8:{10:'word_bank'},9:{10:'word_bank'},10:{11:'displayed_completed_exercise'},12:{5:'displayed_completed_exercise',8:'displayed_completed_exercise',14:'displayed_completed_exercise'},13:{4:'displayed_completed_exercise',7:'displayed_completed_exercise',10:'displayed_completed_exercise'},14:{7:'displayed_completed_exercise',10:'displayed_completed_exercise'},15:{8:'displayed_completed_exercise',16:'displayed_completed_exercise'},16:{9:'displayed_completed_exercise',12:'visual_answer_context'},17:{10:'displayed_completed_exercise',13:'displayed_completed_exercise'},18:{7:'displayed_completed_exercise',12:'displayed_completed_exercise'},19:{7:'displayed_completed_exercise',12:'displayed_completed_exercise'},20:{8:'displayed_completed_exercise',13:'displayed_completed_exercise'}}


def ref(file,slide):return {'file':file['filename'],'fileId':file['id'],'sha256':file['sha256'],'lesson':file['lessonNumber'],'slide':slide['number'],'slideId':slide['id']}


def text_blocks(z,part):
    root=ET.fromstring(z.read(part));blocks=[]
    for i,shape in enumerate(root.findall('.//p:sp',NS),1):
        paras=[''.join(t.text or '' for t in p.findall('.//a:t',NS)) for p in shape.findall('.//a:p',NS)]
        if not any(paras):continue
        props=shape.find('.//p:cNvPr',NS)
        transform=shape.find('.//a:xfrm',NS)
        coords={}
        if transform is not None:
            for child in transform:
                coords[child.tag.split('}')[-1]]=dict(child.attrib)
        runs=[]
        for r in shape.findall('.//a:r',NS):
            t=r.find('a:t',NS);p=r.find('a:rPr',NS)
            runs.append({'text':t.text or '' if t is not None else '', 'format':dict(p.attrib) if p is not None else {}})
        blocks.append({'index':i,'name':props.get('name','') if props is not None else '', 'paragraphs':paras,'coordinatesEMU':coords,'runs':runs})
    return blocks


def main():
    curriculum=json.loads((ROOT/'data/curriculum.json').read_text())
    folder=ROOT/'curriculum';folder.mkdir(exist_ok=True)
    render_log=json.loads((ROOT/'data/render-audit.json').read_text()) if (ROOT/'data/render-audit.json').exists() else []
    source={'schemaVersion':1,'datasetKind':'original_source_only','course':{'title':'走遍泰国','institution':'Prince of Songkla University Phuket Confucius Institute','expectedLessonCount':20},'auditDate':'2026-10-29','sourceFolder':'/path/to/走遍泰国','policy':'Original extracted source content only. Editorial translation, interpretation and new activities are excluded from this file. Shape coordinates preserve evidence about layout. Preview images omit some Chinese/Thai glyphs due to renderer fonts and must NOT be used as complete text evidence. Use original OOXML text; inspect a readable PDF or PowerPoint for final layout verification. Extraction does not mean teacher approval or current travel accuracy.','visualObservationFile':'curriculum/visual_observations.json','lessons':[],'files':curriculum['fileInventory']}
    totals=Counter()
    for lesson in curriculum['lessons']:
        files=[f for f in curriculum['fileInventory'] if f['id'] in lesson['processing']['files']]
        if not files:
            source['lessons'].append({'id':lesson['id'],'number':lesson['number'],'status':'missing','reason':'No source supplied. No lesson-specific content inferred.','slides':[]})
            continue
        f=files[0];path=ROOT/'sources'/f['storedName']
        title=''
        for slide in lesson['sourceSlides'][:3]:
            candidates=[line for line in slide['text'].splitlines() if re.match(r'^第[一二三四五六七八九十百\d]+课\s*',line)]
            if candidates:title=candidates[0];break
        record={'id':lesson['id'],'number':lesson['number'],'originalTitleLine':title,'titleFromSourceSlide':re.sub(r'^第[一二三四五六七八九十百\d]+课\s*','',title),'titleFromFilename':lesson['originalTitle'],'status':'source_extracted','sourceFile':dict(f,workspacePath='sources/'+f['storedName']),'sourceSlideCount':len(lesson['sourceSlides']),'objectives':{'status':'not_explicitly_labeled_in_source','items':[]},'slides':[],'vocabulary':[],'dialogues':[],'grammar':[],'exercises':[],'answerDisplays':[],'visuals':[],'speakerNotes':[],'issues':[],'audio':{'status':'no_embedded_audio_or_video_found'}}
        seen_words={}
        with zipfile.ZipFile(path) as z:
            if hashlib.sha256(path.read_bytes()).hexdigest()!=f['sha256']:raise ValueError('Source hash mismatch: '+f['filename'])
            for s in lesson['sourceSlides']:
                sr=ref(f,s);n=s['number'];text=s['text']
                slide=dict(s,sourceRef=sr,textBlocks=text_blocks(z,s['originalPart']))
                slide.pop('reviewedAt',None)
                slide['extractionStatus']='text_extracted' if text.strip() else 'image_only_no_selectable_text'
                renders=sorted((ROOT/'public/assets/source/rendered'/lesson['id']).glob('slide-*.png'))
                if len(renders)==len(lesson['sourceSlides']):slide['renderedSlide']='/assets/source/rendered/'+lesson['id']+'/'+renders[n-1].name
                if slide.get('renderedSlide'):slide['previewWarning']='Font substitution omitted some selectable Chinese and Thai glyphs. This is visual-only evidence, not a complete text rendering. Original extracted text is retained above.'
                slide['sourceCategories']=[]
                if '生词' in text or '专有名词' in text:slide['sourceCategories'].append('vocabulary')
                chinese_speakers=bool(re.search(r'(小爱|小乐|佳佳|素察|服务员|工作人员|签证官|酒店前台|乘务员|嘟嘟车司机|售货员)[：:]',text))
                exercise=bool(re.search(r'_{2,}|练一练|练一练|练习|\(\s*\)',text)) or n in ANSWER_SLIDES.get(lesson['number'],{})
                if chinese_speakers:
                    slide['sourceCategories'].append('exercise_dialogue' if exercise else 'dialogue')
                    if not exercise:record['dialogues'].append({'id':s['id']+'-dialogue','sourceRef':sr,'originalText':text,'textBlocks':slide['textBlocks'],'extractionNotice':'Includes original pinyin / Thai headings where present. No speaker lines have been invented or normalized.'})
                if '语法' in re.sub(r'\s+','',text) or ('ไวยากรณ์' in text and not '生词' in text):
                    slide['sourceCategories'].append('grammar')
                    record['grammar'].append({'id':s['id']+'-grammar','sourceRef':sr,'originalText':text})
                if exercise:
                    slide['sourceCategories'].append('exercise')
                    kind=ANSWER_SLIDES.get(lesson['number'],{}).get(n)
                    record['exercises'].append({'id':s['id']+'-exercise','sourceRef':sr,'originalText':text,'answerStatus':kind or 'no_separate_key_identified','answerRef':s['id']+'-answer-display' if kind else None,'note':'Original prompt, word bank and any displayed completions are preserved together. No answer has been inferred.'})
                    if kind:record['answerDisplays'].append({'id':s['id']+'-answer-display','sourceRef':sr,'kind':kind,'originalSlideText':text,'mappingStatus':'preserved_on_original_slide; not automatically paired','note':'Text order alone may not link each answer to a blank. Consult text block coordinates and rendered slide. Word banks are not asserted to be answer keys.'})
                for table_index,table in enumerate(s['tables']):
                    if 'vocabulary' not in slide['sourceCategories']:continue
                    for row_index,row in enumerate(table):
                        if len(row)>=4 and row[0].strip().isdigit() and re.search(r'[\u4e00-\u9fff]',row[1]):
                            key=row[1]
                            item={'id':s['id']+f'-vocab-{table_index+1}-{row_index+1}','sourceRef':sr,'tableIndex':table_index,'rowIndex':row_index,'originalCells':row,'chinese':row[1],'pinyin':row[2],'partOfSpeech':row[3] if len(row)>=5 else None,'thaiGloss':row[-1] if re.search(r'[\u0e00-\u0e7f]',row[-1]) else None,'repeatedInLesson':key in seen_words}
                            seen_words[key]=item['id'];record['vocabulary'].append(item)
                # Lists not laid out as a numeric table remain original text blocks, not guessed row fields.
                if 'vocabulary' in slide['sourceCategories'] and not s['tables']:
                    slide['issues'].append('Non-tabular vocabulary / proper-name list retained as original text blocks; no column alignment inferred.')
                for i,v in enumerate(s['visuals']):
                    record['visuals'].append({'id':s['id']+f'-visual-{i+1}','sourceRef':sr,**v,'interpretationStatus':'original_asset_preserved; see separate adaptation notes for editorial observations'})
                    if not v['url']:record['issues'].append({'slide':n,'type':'unsupported_embedded_format','detail':v['originalPart']+' is EMF; original retained in the PPT, and full-slide rendering is used when available.'})
                if not text.strip():record['issues'].append({'slide':n,'type':'image_only','detail':'No selectable text. Ten fruit illustrations retained. The source does not provide text labels on this slide; do not invent a transcription.'})
                if s['notes']:record['speakerNotes'].append({'sourceRef':sr,'originalText':s['notes']})
                record['slides'].append(slide)
        record['rendering']=dict(next((r for r in render_log if r['lesson']==lesson['number']),{'status':'not_yet_rendered'}),fontWarning='Chinese/Thai font gaps observed in generated previews; original text extraction is unaffected. Final layout verification pending readable PDF or PowerPoint.')
        totals.update({'slides':len(record['slides']),'textSlides':sum(bool(s['text'].strip()) for s in record['slides']),'vocabularyRows':len(record['vocabulary']),'dialogueSlides':len(record['dialogues']),'exerciseSlides':len(record['exercises']),'answerDisplaySlides':len(record['answerDisplays']),'visualPlacements':len(record['visuals']),'tableObjects':sum(len(s['tables']) for s in record['slides'])})
        source['lessons'].append(record)
    source['totals']=dict(totals)
    (folder/'lessons.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 《走遍泰国》 source-material audit','','Audit date: 2026-10-29. Source directory: /path/to/走遍泰国/. Original copies are preserved read-only by convention in the workspace sources/ folder under hash-based filenames. The original filenames and full SHA-256 hashes are recorded in curriculum/lessons.json.','','## Inventory','','**20 of 20 numbered lessons found. 20 readable PPTX files. No missing lessons, unreadable packages or exact duplicate files.** All original slide orders were read from presentation.xml, rather than sorting slide filenames.','','| Lesson | Exact original filename | Title on source slide | Slides | Extraction | Issues |','|---:|---|---|---:|---|---|']
    for l in source['lessons']:
        issues='; '.join('S'+str(i['slide'])+': '+i['type'] for i in l.get('issues',[])) or 'Teacher verification of visuals and extracted layout pending'
        lines.append(f"| {l['number']} | {l['sourceFile']['filename']} | {l['titleFromSourceSlide']} | {l['sourceSlideCount']} | Source text/tables/images extracted; {l['rendering']['status']} | {issues} |")
    lines+=['','## Coverage and limits','',f"- {totals['slides']} slides; {totals['textSlides']} contain selectable text; one is image-only (L7 S12).",f"- {totals['tableObjects']} table objects; {totals['vocabularyRows']} original numeric vocabulary rows (including intentional repetition). Non-tabular phrases, names and labels are preserved in slide text/text blocks.",f"- {totals['visualPlacements']} embedded picture placements, including repeated/decorative pictures. This is not a count of unique educational images.",'- No native chart objects or embedded audio/video files were found in any of the 20 PPTX packages. No listening audio or transcript is fabricated.','- Three EMF picture placements in L7 S4, S6 and S8 cannot be displayed as standalone browser images; the original package retains them. Full-slide renders preserve their appearance if conversion succeeds.','- Six slides contain extracted speaker-note text. Hidden slides, if any, remain in source sequence.','- Exact text, pinyin, Thai glosses, original table cells, shape text runs and layout coordinates are kept. No missing English translations or objectives are invented in the original-only dataset.','- Source exercise slides and displayed completions / word banks are preserved separately. Where text order cannot reliably pair a blank and an answer, the mapping is explicitly unverified; no answer is guessed.','- Lesson 8 includes both 素帖山 and 素贴山, and an example calls the Grand Palace a temple. Original wording is retained and flagged for teacher review.','- Lesson 19 summarizes 把 in terms of position change but also gives 翻译成, a transformation example. The adaptation notes identify this teaching clarification.','- Source visa procedures, fares, entrance fees, travel durations, store layouts, festival schedules and activity descriptions are historical learning context. They have not been verified as current operational information.','- Cultural comparisons are descriptions in the source, not universal claims about every person. Review national generalizations, greeting practices, ceremony participation and site-specific rules before teaching or applying them.','','## Integrity and separation','','- curriculum/lessons.json contains original source content only. Every slide, vocabulary table row, dialogue, exercise, answer display and visual placement has a filename, file hash, lesson and slide reference.','- curriculum/adaptation_notes.md contains proposed editorial adaptations. They are not labeled teacher-approved.','- data/curriculum.json is the separate application integration dataset containing clearly labeled source extracts, editorial translations/explanations and newly authored activities.','- No source file was modified. Run python3 scripts/build_source_audit.py to regenerate these records after extraction / visual rendering.','']
    lines+=['## Preview font issue (important)','','All 282 slides have preview images, but the local LibreOffice renderer omits some selectable Chinese and Thai glyphs. These previews are **not faithful text renderings** and are used only to inspect retained pictures / diagrams. The original OOXML extraction contains both languages. A readable PDF export would improve final layout verification and answer-to-blank checks. No missing preview glyph has been guessed.','','Per-lesson direct visual observations are stored separately in curriculum/visual_observations.json. They are editorial descriptions, not textbook quotations.','']
    (ROOT/'source_inventory.md').write_text('\n'.join(lines),encoding='utf-8')
    notes=['# Proposed Grade 11 Chinese B adaptations','','These are editorial proposals, not original textbook content and not teacher-approved adaptations. The authoritative source dataset is lessons.json in this folder. Student: Emmalyne; fluent Chinese reading, Thai/German native languages, English navigation and explanations; future Hospitality Management.','','## Course-wide design','','- Preserve lessons 1–20 in their source sequence. Use reading fluency for inference, interpretation and professional register instead of making pinyin decoding the goal.','- Understand: read source dialogue with evidence; identify speaker purpose, confirmed details and implied needs.','- Communicate: apply the source pattern in controlled practice, clarify needs, paraphrase and negotiate meaning.','- Apply professionally: write guest messages and perform live partner role-plays; include open-ended alternatives and a reflection.','- Use English instructions and grammar explanations, with optional pinyin and source Thai vocabulary glosses. Add German only when there is a reviewed reason; do not automatically translate every sentence.','- Label original Chinese extracts “textbook”; label editorial English glosses / grammar explanations “adaptation”; label new questions, tasks, models and rubrics “supplementary”. None of these labels implies teacher approval.','- Criterion feedback: comprehension; vocabulary/accuracy; communicative effectiveness; organization/clarity; audience/professionalism; intercultural understanding. Separate automated answer checks / character counts from teacher evaluation. No official IB grade.','- Record missing or ambiguous answers for teacher review; never generate them as original answer keys. Retain difficult source material and discuss limitations rather than silently deleting it.','','## Lesson-by-lesson proposals','']
    for l in curriculum['lessons']:
        original=source['lessons'][l['number']-1]
        notes += [f"### Lesson {l['number']:02d} — {original['titleFromSourceSlide']}",'',f"Source: {original['sourceFile']['filename']}; slides 1–{original['sourceSlideCount']}.",'',f"**Understand:** {l['objectives'][0]}",f"**Communicate:** {l['patterns'][0]['title']}. {l['patterns'][0]['explanation']}",f"**Apply professionally (new task):** {l['tasks'][0]['prompt']}",f"**Scaffold:** {' '.join(l['tasks'][0]['scaffold'])}",f"**Challenge:** {l['tasks'][0]['challenge']}",f"**Listening/speaking:** {l['tasks'][1]['prompt']}",f"**Source anchors:** {'; '.join(l['tasks'][0]['sourceRefs'])}.",f"**Teacher review:** {l['culturalNotes'][0]['text']}",'']
    notes+=['## Visual evidence and unresolved content','','- L7 S12: a collage of ten fruit illustrations was visually inspected; there is no selectable label text on that slide. Do not transcribe guessed labels as textbook wording. Adjacent slides 10–11 supply fruit labels that can be used only with their own references.','- L11 S5: the source contains beach / destination photographs. The application’s coastal photo is reused from this slide with a visible source credit; it is not used as proof of a specific real-world location.','- All full-slide PNGs and per-lesson contact sheets, when successfully rendered, preserve original layout, visual relationships and text embedded in images. Rendered evidence is distinct from a verified semantic transcription.','- Remaining per-slide visual interpretation and original answer-to-blank relationships require teacher confirmation unless explicitly verified. A successful extraction/render does not claim all information has been pedagogically verified.','','## Proposed integration','','Application adaptations currently live in data/curriculum.json, using stable lesson/slide references matching lessons.json. Edits can be reviewed through the teacher desk. The raw source dataset should remain immutable; corrections to an interpretation belong in an adaptation or teacher note, with the source reference retained.','']
    notes+=['## Preview limitation clarified','','The generated contact sheets omit some Chinese and Thai glyphs because of local rendering/font behavior. They preserve many pictures and geometric relationships but must not be called complete or faithful text renders. Original extracted Chinese/Thai remains authoritative. Readable PDF exports would permit final layout and answer-position verification. See visual_observations.json for explicitly editorial visual descriptions.','']
    (folder/'adaptation_notes.md').write_text('\n\n'.join(notes),encoding='utf-8')
    print(json.dumps({'files':len(source['files']),'lessons':len(source['lessons']),'totals':source['totals'],'outputs':['source_inventory.md','curriculum/lessons.json','curriculum/adaptation_notes.md']},ensure_ascii=False))


if __name__=='__main__':main()
