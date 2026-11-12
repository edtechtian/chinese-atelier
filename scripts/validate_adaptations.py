#!/usr/bin/env python3
"""Validate app integration against the immutable source audit and editorial schema."""
from pathlib import Path
import sys,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.schema import validate_curriculum

def check():
 app=json.loads((ROOT/'data/curriculum.json').read_text());source=json.loads((ROOT/'curriculum/lessons.json').read_text());author=json.loads((ROOT/'curriculum/adaptations.json').read_text())
 errors=validate_curriculum(app);warnings=[];norm=lambda s:re.sub(r'\s+','',s)
 if [x['id'] for x in author['lessons']]!=[f'zt-{n:02d}' for n in range(1,21)]:errors.append('Adaptation specification must include all 20 lessons in order.')
 for l,orig in zip(app['lessons'],source['lessons']):
  name=l['id'];slides={s['id']:s for s in orig['slides']}; texts={sid:norm(s['text']) for sid,s in slides.items()}
  if l.get('adaptationVersion')!=2:errors.append(f'{name}: missing complete adaptation version')
  if l['originalTitle']!=orig['titleFromSourceSlide']:errors.append(f'{name}: original title changed')
  if len(l['sourceSlides'])!=len(orig['slides']):errors.append(f'{name}: original slide count changed')
  for slide in l['sourceSlides']:
   if slide['text']!=slides[slide['id']]['text']:errors.append(f'{name}: source text changed at {slide["id"]}')
  p=l.get('pedagogy',{})
  if {x.get('action') for x in p.get('decisions',[])}!={'retain','extend','scaffold','interactive'}:errors.append(f'{name}: incomplete adaptation decisions')
  if sum(x['minutes'] for x in p.get('sequence',[]))!=l['minutes']:errors.append(f'{name}: time budget mismatch')
  if len(l['questions'])<8 or len(l['tasks'])<3 or len(l['patterns'])<2:errors.append(f'{name}: incomplete teaching coverage')
  if not any(t['type']=='roleplay' for t in l['tasks']):errors.append(f'{name}: no speaking task')
  if not l.get('liveListening',{}).get('instructions'):errors.append(f'{name}: no live listening plan')
  if not {'comprehension','vocabulary','grammar'}.issubset({q.get('category') for q in l['questions']}):errors.append(f'{name}: missing objective practice category')
  for obj in l['questions']+l['tasks']+l['patterns']+l['vocabulary']+p.get('decisions',[])+[l.get('liveListening',{})]:
   for ref in obj.get('sourceRefs',[]):
    if ref not in slides:errors.append(f'{name}: invalid reference {ref}')
  for r in l['readings']:
   if not r.get('discussion'):errors.append(f'{name}: missing source-specific discussion')
   for paragraph in r['body']:
    if not any(norm(paragraph) in texts[x] for x in r['sourceRefs']):errors.append(f'{name}: non-source reading text {paragraph}')
  for p in l['patterns']:
   if not all(p.get(x) for x in ['explanation','pitfall','application']):errors.append(f'{name}: incomplete grammar development')
   if p.get('exampleOrigin')=='textbook':
    for ex in p['examples']:
     if not any(norm(ex) in texts[x] for x in p['sourceRefs']):errors.append(f'{name}: claimed source quotation missing: {ex}')
  for v in l['vocabulary']:
   word=norm(v['chinese'])
   if not any(word in texts[x] for x in v['sourceRefs']):errors.append(f'{name}: vocabulary absent from cited source: {word}')
   if '请结合课文' in v['example']:errors.append(f'{name}: placeholder vocabulary example')
   if v.get('exampleOrigin')=='textbook' and not any(norm(v['example']) in texts[x] for x in v.get('exampleSourceRefs',[])):errors.append(f'{name}: vocabulary example not in cited source: {word}')
  for q in l['questions']:
   if q['origin']!='supplementary':errors.append(f'{name}: new question misattributed')
   if q['type']=='choice' and len({o['text'] for o in q['options']})!=len(q['options']):errors.append(f'{q["id"]}: duplicate distractors')
   if q['type']=='text' and any(a in q['prompt'].split('____')[0] and len(a)>1 for a in q['acceptedAnswers']):warnings.append(f'{q["id"]}: inspect whether contextual hint is too revealing')
  for t in l['tasks']:
   count=len(re.findall(r'[\u3400-\u9fff]',t['model']))
   if count<t['minCharacters']:errors.append(f'{t["id"]}: model ({count}) below guidance ({t["minCharacters"]})')
   if not t.get('successCriteria') or not t.get('challenge') or not t.get('scaffold'):errors.append(f'{t["id"]}: missing differentiation or assessment')
   if t['origin']!='supplementary':errors.append(f'{t["id"]}: new model misattributed')
 report={'valid':not errors,'originalDatasetSha256':hashlib.sha256((ROOT/'curriculum/lessons.json').read_bytes()).hexdigest(),'counts':{'lessons':20,'readings':sum(len(x['readings']) for x in app['lessons']),'vocabulary':sum(len(x['vocabulary']) for x in app['lessons']),'patterns':sum(len(x['patterns']) for x in app['lessons']),'objectiveItems':sum(len(x['questions']) for x in app['lessons']),'communicationTasks':sum(len(x['tasks']) for x in app['lessons']),'liveListeningPlans':sum(bool(x.get('liveListening')) for x in app['lessons'])},'errors':errors,'warnings':warnings,'limitations':['Editorial adaptations require teacher approval; structural validation is not a teacher or official IB assessment.','No audio recordings or speech recognition. Listening requires a live partner/teacher.','Original visual/font and answer-mapping issues remain recorded in source_inventory.md.']}
 (ROOT/'curriculum/adaptation_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return report
if __name__=='__main__':
 r=check();print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(0 if r['valid'] else 1)
