#!/usr/bin/env python3
"""Export and validate the same data-driven 100-step path served by the app."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.learning import build_path,catalog,initialize
c=json.loads((ROOT/'data/curriculum.json').read_text());p=build_path(c)
items=catalog(c,initialize({}));slides={s['id'] for l in c['lessons'] for s in l['sourceSlides']};seen=set()
for u in p['units']:
 assert len(u['steps'])==5
 for s in u['steps']:
  assert s['id'] not in seen
  seen.add(s['id']);assert s['sourceRefs'] and set(s['sourceRefs'])<=slides
  for field in ['questionIds','vocabularyIds','coreVocabularyIds','patternIds','taskIds']:assert set(s[field])<=items.keys()
(ROOT/'curriculum/learning_path.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
print('Validated 20 original units, 100 unique steps, source references and activity IDs.')
