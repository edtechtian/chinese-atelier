#!/usr/bin/env python3
"""Validate every visual reference and key against the retained source dataset."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate():
 c=json.loads((ROOT/'data/curriculum.json').read_text());d=json.loads((ROOT/'curriculum/visual_learning.json').read_text());errors=[]
 publication=ROOT/'publication-assets.json'
 manifest=json.loads(publication.read_text()) if publication.is_file() else {}
 slides={s['id']:s for l in c['lessons'] for s in l['sourceSlides']};items={v['id'] for l in c['lessons'] for v in l['vocabulary']};ids=set();images=d['images']
 def check(ok,message):
  if not ok:errors.append(message)
 check([u['id'] for u in d['units']]==[l['id'] for l in c['lessons']],'20 original units must remain in order.')
 for i,image in images.items():
  check(bool(image.get('alt')),i+': missing alt')
  check(image['src'].startswith('/assets/'),i+': nonlocal path')
  original=(ROOT/'public'/image['src'].lstrip('/')).is_file()
  derivatives=image.get('responsive',{})
  published_derivatives=manifest.get('optimizedVisualImagesIncluded') is True and image['origin']=='textbook_asset' and bool(derivatives) and all((ROOT/'public'/url.lstrip('/')).is_file() for url in derivatives.values())
  check(original or published_derivatives,i+': missing file or declared publication derivative')
  for url in image.get('responsive',{}).values():check((ROOT/'public'/url.lstrip('/')).is_file(),i+': missing responsive derivative')
  if image['origin']=='textbook_asset':
   check(bool(image['sourceRefs']),i+': no source attribution')
   for ref in image['sourceRefs']:
    check(ref in slides,i+': broken slide')
    if ref in slides:check(image['src'] in [v.get('url') for v in slides[ref]['visuals']],i+': source image not on referenced slide')
 for u,l in zip(d['units'],c['lessons']):
  check(u['title']==l['originalTitle'],u['id']+': title changed')
  check(u['sceneId'] in images,u['id']+': missing scene')
  check({v['itemId'] for v in u['vocabulary']}=={v['id'] for v in l['vocabulary']},u['id']+': incomplete vocabulary mapping inventory')
  for v in u['vocabulary']:check(v['imageId'] is None or v['imageId'] in images,v['itemId']+': broken picture')
  for a in u['activities']:
   check(a['id'] not in ids,a['id']+': duplicate');ids.add(a['id']);check(a['origin']=='supplementary',a['id']+': missing separation')
   check(bool(a['sourceRefs']) and set(a['sourceRefs'])<=set(slides),a['id']+': broken source references')
   check(bool(a['prompt']) and bool(a['explanation']),a['id']+': empty instructions or explanation')
   for image_id in [a.get('imageId')]+[p.get('imageId') for p in a.get('panels',[])]+[p.get('imageId') for p in a.get('pairs',[])]:
    check(image_id is None or image_id in images,a['id']+': unknown image')
   if a['type'] in {'picture_choice','scene_dialogue','situation_response','hotspot_choice'}:check(a['answer'] in [o['id'] for o in a['options']],a['id']+': invalid choice key')
   if a['type']=='picture_match':check(len(a['answer'])==len(a['pairs']) and set(a['answer'])<={o['id'] for o in a['options']},a['id']+': invalid matching key')
   if a['type'] in {'picture_sequence','sentence_order'}:check(len(a['answer'])==len(a['panels']) and set(a['answer'])=={p['id'] for p in a['panels']},a['id']+': invalid sequence key')
   if a['type']=='picture_cloze':check(bool(a['accepted']) and a['expected'] in a['accepted'],a['id']+': invalid cloze key')
   if a.get('vocabularyId'):check(a['vocabularyId'] in items,a['id']+': unknown source vocabulary')
 return errors
if __name__=='__main__':
 errors=validate()
 if errors:raise SystemExit('\n'.join(errors))
 d=json.loads((ROOT/'curriculum/visual_learning.json').read_text());print('Visual validation passed:',len(d['units']),'units;',sum(len(u['activities']) for u in d['units']),'activities;',len(d['images']),'images.')
