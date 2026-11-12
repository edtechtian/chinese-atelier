"""Supplementary visual practice; independent from source data and SRS scheduling."""
import copy,json,re,unicodedata
from pathlib import Path
from . import learning as L
CONFIG=Path(__file__).resolve().parents[1]/'curriculum/visual_learning.json'
class VisualError(Exception):
 def __init__(self,status,message):self.status=status;self.message=message

def require(ok,message,status=400):
 if not ok:raise VisualError(status,message)
def load(root=None):
 candidate=Path(root)/'curriculum/visual_learning.json' if root else CONFIG
 return json.loads((candidate if candidate.is_file() else CONFIG).read_text())
def activities(config):return {a['id']:dict(a,unitId=u['id'],unitTitle=u['title']) for u in config['units'] for a in u['activities']}
def state(h):return h.store.state.setdefault('visualLearning',{'attempts':[],'responses':{}})
def clean(value):return re.sub(r'[\s，。！？、,.!?：:；;“”"\u200b]','',unicodedata.normalize('NFKC',value)).casefold()
def public_config(config):
 c=copy.deepcopy(config)
 for u in c['units']:
  for a in u['activities']:
   for k in ['answer','accepted','expected','explanation','model']:a.pop(k,None)
 return c

def get(h,path):
 if path not in {'/api/visual','/api/teacher/visual'}:return False
 config=load(h.server.root)
 if path.startswith('/api/teacher/'):
  h.require_teacher();h.send({'config':config,'progress':h.store.state.get('visualLearning',{'attempts':[],'responses':{}})})
 else:h.send(public_config(config))
 return True

def post(h,path,b):
 if path not in {'/api/visual/attempt','/api/visual/response','/api/teacher/visual/assessment'}:return False
 config=load(h.server.root);items=activities(config)
 if path=='/api/teacher/visual/assessment':
  h.require_teacher();v=state(h);r=v['responses'].get(b.get('responseId'))
  require(r and r['submitted'],'Choose a submitted visual response.',404)
  require(b.get('revision')==r['revision'],'The student revised this work. Reload before reviewing.',409)
  scores=b.get('scores');comment=b.get('comment')
  require(isinstance(scores,dict) and set(scores)==set(r['criteria']) and all(type(x)is int and 1<=x<=4 for x in scores.values()),'Score each criterion from 1 to 4.')
  require(isinstance(comment,str) and 5<=len(comment.strip())<=4000,'Give specific feedback and one next step.')
  r['teacherReview']={'scores':scores,'comment':comment.strip(),'at':L.iso(L.moment()),'revision':r['revision'],'officialGrade':False}
  h.store.save_state();h.send(r);return True
 aid=b.get('activityId');require(isinstance(aid,str) and aid in items,'Visual activity not found. Open a verified unit.',404);a=items[aid]
 if path=='/api/visual/attempt':
  require(a['type']!='photo_description','Use Save response for open writing.')
  answer=b.get('answer');require(isinstance(answer,(str,list)),'Choose or enter your own response first.')
  if isinstance(answer,list):require(1<=len(answer)<=10 and all(isinstance(v,str) and 0<len(v)<=1000 for v in answer),'Complete each picture response.')
  else:require(0<len(answer.strip())<=1000,'Enter a response of 1–1000 characters.')
  if a['type'] in {'picture_sequence','picture_match','sentence_order'}:correct=answer==a['answer']
  elif a['type']=='picture_cloze':correct=isinstance(answer,str) and clean(answer) in [clean(x) for x in a['accepted']]
  else:
   require(isinstance(answer,str) and answer in {x['id'] for x in a['options']},'Choose one of the available answers.')
   correct=answer==a['answer']
  learning=L.initialize(h.store.state);earned=L.award(learning,'visual:'+aid,2,'visual_question') if correct else 0
  out={'id':aid,'unitId':a['unitId'],'answer':answer,'correct':correct,'expected':a['expected'],'explanation':a['explanation'],'at':L.iso(L.moment()),'xpEarned':earned,'origin':'supplementary','sourceRefs':a['sourceRefs']}
  v=state(h);v['attempts'].append(out);v['attempts']=v['attempts'][-500:]
  h.event(('Visual practice: ' if correct else 'Visual practice to revisit: ')+a['title'],a['unitId'])
  h.store.save_state();h.send(out);return True
 require(a['type']=='photo_description','Choose a writing activity.')
 text=b.get('text');submit=b.get('submit',False);require(type(submit)is bool,'Submission must be true or false.')
 require(isinstance(text,str) and 0<len(text.strip())<=12000,'Write a response before saving (maximum 12,000 characters).')
 require(not submit or len(re.findall(r'[\u3400-\u9fff]',text))>=a['minimum'],'Use at least '+str(a['minimum'])+' Chinese characters before submitting.')
 v=state(h);previous=v['responses'].get(aid);changed=not previous or previous['text']!=text
 r=copy.deepcopy(previous) if previous else {'id':aid,'unitId':a['unitId'],'title':a['title'],'unitTitle':a['unitTitle'],'revision':0,'reviewHistory':[],'teacherReview':None}
 if changed:
  if r.get('teacherReview'):r['reviewHistory'].append(r['teacherReview'])
  r['teacherReview']=None;r['revision']+=1
 r.update(text=text,submitted=submit,updatedAt=L.iso(L.moment()),criteria=a['criteria'],sourceRefs=a['sourceRefs'],origin='supplementary')
 v['responses'][aid]=r;h.event('Saved visual writing',a['unitId']);h.store.save_state();h.send({'work':r,'notice':'Saved. Only length was checked; language quality requires teacher review.','model':a['model']});return True
