#!/usr/bin/env python3
"""Deterministic validation of the original-only source audit."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def validate(path=ROOT/'curriculum/lessons.json'):
    data=json.loads(Path(path).read_text())
    errors=[];ids=set();counts={'files':len(data['files']),'lessons':len(data['lessons']),'slides':0,'textSlides':0,'visualPlacements':0,'renderedSlides':0}
    if [l['number'] for l in data['lessons']]!=list(range(1,21)):errors.append('Lesson numbers must be 1–20 in sequence.')
    hashes=[f['sha256'] for f in data['files']]
    if len(hashes)!=len(set(hashes)):errors.append('Duplicate source file hashes.')
    def checkid(value):
        if value in ids:errors.append('Duplicate identifier: '+value)
        ids.add(value)
    for lesson in data['lessons']:
        checkid(lesson['id'])
        file=lesson.get('sourceFile')
        if not file:errors.append('Missing source for '+lesson['id']);continue
        original=ROOT/file['workspacePath']
        if not original.exists():errors.append('Source file not found: '+str(original))
        elif hashlib.sha256(original.read_bytes()).hexdigest()!=file['sha256']:errors.append('Source hash mismatch: '+file['filename'])
        slides=lesson['slides'];slideids={s['id'] for s in slides}
        if [s['number'] for s in slides]!=list(range(1,lesson['sourceSlideCount']+1)):errors.append('Slide sequence mismatch: '+lesson['id'])
        for slide in slides:
            checkid(slide['id']);counts['slides']+=1;counts['textSlides']+=bool(slide['text'].strip());counts['visualPlacements']+=len(slide['visuals'])
            if slide['sourceRef']['fileId']!=file['id'] or slide['sourceRef']['slide']!=slide['number']:errors.append('Broken slide source reference: '+slide['id'])
            if slide.get('renderedSlide'):
                if not (ROOT/'public'/slide['renderedSlide'].lstrip('/')).is_file():errors.append('Missing rendered slide: '+slide['id'])
                else:counts['renderedSlides']+=1
            for visual in slide['visuals']:
                if visual['url'] and not (ROOT/'public'/visual['url'].lstrip('/')).is_file():errors.append('Missing image asset: '+str(visual['url']))
        for field in ['vocabulary','dialogues','grammar','exercises','answerDisplays','visuals']:
            for item in lesson[field]:
                checkid(item['id'])
                sr=item['sourceRef']
                if sr['slideId'] not in slideids or sr['fileId']!=file['id'] or sr['sha256']!=file['sha256']:errors.append('Broken source reference: '+item['id'])
                if 'origin' in item and item['origin']!='textbook':errors.append('Adaptation leaked into original source: '+item['id'])
        displays={x['id'] for x in lesson['answerDisplays']}
        for exercise in lesson['exercises']:
            if exercise['answerRef'] and exercise['answerRef'] not in displays:errors.append('Broken answer display link: '+exercise['id'])
        if any('acceptedAnswers' in q or 'answer' in q for q in lesson['exercises']):errors.append('Inferred answer key found in source exercises.')
    return {'valid':not errors,'counts':counts,'errors':errors,'unresolved':['L7 S12 image-only; no selectable text','Standalone EMF images at L7 S4/S6/S8','Teacher semantic verification of source visuals and answer/blank relationships pending']}


if __name__=='__main__':
    result=validate();print(json.dumps(result,ensure_ascii=False,indent=2))
    (ROOT/'curriculum/validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result['valid'] else 1)
