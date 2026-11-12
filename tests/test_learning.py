"""Microlearning regression suite: actual HTTP persistence, scheduling and migration."""
import copy,json,time
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from test_application import AppTests
from app import learning as L
import unittest
UTC=timezone.utc
CURRICULUM=json.load(open(__import__('pathlib').Path(__file__).resolve().parents[1]/'data/curriculum.json'))
class SchedulingTests(unittest.TestCase):
 def setUp(self):
  self.state={'progress':{},'reviews':{}};self.l=L.initialize(self.state);self.items=L.catalog(CURRICULUM,self.l);self.item=self.items['zt-01-v01'];self.at=datetime(2026,10,30,3,tzinfo=UTC)
 def test_exact_day_0_1_3_7_14_30_ladder(self):
  r=L.enroll(self.l,self.item,self.at)
  self.assertEqual(L.local_day(r['nextReviewAt']).isoformat(),'2026-10-31')
  day0=L.local_day(self.at)
  for target in [3,7,14,30]:
   due=L.moment(r['nextReviewAt']);r=L.schedule(r,'good',at=due)
   self.assertEqual((L.local_day(r['nextReviewAt'])-day0).days,target)
 def test_four_ratings_and_mastery(self):
  r=L.enroll(self.l,self.item,self.at,due_now=True)
  again=L.schedule(r,'again',at=self.at);self.assertEqual(L.moment(again['nextReviewAt'])-self.at,timedelta(minutes=10));self.assertEqual(again['failedReviews'],1)
  hard=L.schedule(dict(r,interval=10),'hard',at=self.at);self.assertEqual(hard['interval'],6);self.assertLess(hard['easeFactor'],2.5)
  good=L.schedule(r,'good',at=self.at);easy=L.schedule(r,'easy',at=self.at);self.assertGreater(easy['interval'],good['interval']);self.assertGreater(easy['easeFactor'],2.5)
  for n in range(7):r=L.schedule(r,'good',at=L.moment(r['nextReviewAt']))
  self.assertEqual(r['mastery'],'mastered')
 def test_timezone_dst_and_boundary(self):
  # 2026-03-08 is the New York spring transition: calendar time remains 09:00.
  at=datetime(2026,3,7,16,tzinfo=UTC);due=L.next_date(at,1,'America/New_York');self.assertEqual(due.isoformat(),'2026-03-08T13:00:00+00:00')
  at=datetime(2026,10,30,17,1,tzinfo=UTC);self.assertEqual(str(L.local_day(at,'Asia/Bangkok')),'2026-10-31');self.assertEqual(str(L.local_day(at,'Europe/Berlin')),'2026-10-30')
 def test_queue_dates_overdue_support_and_recommendation(self):
  for i,offset in enumerate([-3,0,2]):
   item=list(self.items.values())[i];r=L.enroll(self.l,item,self.at);r['nextReviewAt']=L.iso(self.at+timedelta(days=offset))
  counts=L.review_counts(self.l,self.items,self.at);self.assertEqual((counts['due'],counts['overdue'],counts['upcoming']),(2,1,1))
  row=L.queue(self.l,self.items,at=self.at);self.assertLess(row[0]['record']['nextReviewAt'],row[1]['record']['nextReviewAt'])
  self.l['recommendations'][row[1]['id']]={'note':'Prioritize this','active':True};self.assertEqual(L.queue(self.l,self.items,at=self.at)[0]['id'],row[1]['id'])
 def test_migration_preserves_history_without_xp(self):
  state={'progress':{'zt-03':{'completed':True,'updatedAt':'2026-10-29T00:00:00Z','reflection':'能够应对客人的问题。'}},'reviews':{'zt-03-v01':{'lessonId':'zt-03','dueAt':'2026-10-31T00:00:00Z','repetitions':3,'lapses':1,'updatedAt':'2026-10-29T00:00:00Z'}}}
  l=L.initialize(state);self.assertEqual(len(l['steps']),5);self.assertEqual(l['xpLedger'],{});self.assertIsNone(l['srs']['zt-03-v01']['firstLearnedAt']);self.assertEqual(l['srs']['zt-03-v01']['successfulReviews'],2)
  L.initialize(state);self.assertEqual(len(l['steps']),5)
 def test_path_all_refs_and_original_titles(self):
  path=L.build_path(CURRICULUM);self.assertEqual(len(path['units']),20);ids=[]
  slides={s['id'] for l in CURRICULUM['lessons'] for s in l['sourceSlides']}
  for unit,original in zip(path['units'],CURRICULUM['lessons']):
   self.assertEqual(unit['title'],original['originalTitle']);self.assertEqual([s['stage'] for s in unit['steps']],L.STAGES)
   self.assertTrue(unit['steps'][0]['coreVocabularyIds'])
   for s in unit['steps']:
    ids.append(s['id']);self.assertTrue(s['sourceRefs']);self.assertLessEqual(set(s['sourceRefs']),slides)
    for field in ['questionIds','vocabularyIds','coreVocabularyIds','patternIds','taskIds']:
     self.assertLessEqual(set(s[field]),self.items.keys())
  self.assertEqual(len(set(ids)),100)
  for unit in path['units']:
   for s in unit['steps']:
    self.l['steps'][s['id']]={'completed':True}
    for iid in s['coreVocabularyIds']+s['patternIds']+s['questionIds']+s['taskIds']:self.l['srs'][iid]={'mastery':'mastered'}
  self.assertEqual(sum(s['state']=='mastered' for u in L.path_state(CURRICULUM,self.state)['units'] for s in u['steps']),100)
 def test_review_formats_use_real_source_and_hide_keys(self):
  kinds=set();formats=set()
  for item in self.items.values():
   kinds.add(item['kind'])
   for turn in range(3):
    p=L.review_prompt(item,{'successfulReviews':turn,'failedReviews':0});formats.add(p['format']);public=L.public_prompt(p)
    self.assertTrue(p['expected']);self.assertTrue(p['explanation'])
    for key in ['expected','accepted','explanation','check']:self.assertNotIn(key,public)
  self.assertLessEqual({'vocabulary','expression','reading','question','grammar','communication'},kinds)
  self.assertLessEqual({'Chinese → English recall','English → Chinese production','Sentence completion','Sentence reconstruction','Pattern production','Dialogue / situation response','Reading retrieval','Contextual question'},formats)
 def test_daily_recommendations_stable_challenge_and_streak(self):
  d=L.dashboard(CURRICULUM,self.state,self.at);first=d['dailyChallenge']['id'];L.award(self.l,'event',2,'question',self.at)
  for n in range(1,16):
   for i in range(1,6):self.l['steps'][f'zt-{n:02d}-step-{i}']={'completed':True}
  d=L.dashboard(CURRICULUM,self.state,self.at);self.assertEqual(d['dailyChallenge']['id'],first);self.assertEqual(d['streak'],1)
  self.assertEqual(L.dashboard(CURRICULUM,self.state,self.at+timedelta(days=1))['streak'],1)
  self.assertEqual(L.dashboard(CURRICULUM,self.state,self.at+timedelta(days=2))['streak'],0)
  for i,item in enumerate(list(self.items.values())[:8]):L.enroll(self.l,item,self.at-timedelta(days=4))
  d=L.dashboard(CURRICULUM,self.state,self.at);self.assertTrue(d['reviewFirst']);self.assertEqual(d['reviewLimit'],4)

class LearningAPITests(AppTests):
 # Reuses isolated HTTP fixtures without duplicating inherited baseline test runs.
 def test_review_reveal_rating_replay_and_early_practice(self):
  iid='zt-01-v01';p=self.request('/api/learning/review/start',{'itemId':iid})
  self.assertNotIn('expected',p);self.request('/api/learning/review/rate',{'token':p['token'],'rating':'good'},status=409)
  a=self.request('/api/learning/review/answer',{'token':p['token'],'answer':'Thailand; a travel destination.'});self.assertIsNone(a['correct'])
  r=self.request('/api/learning/review/rate',{'token':p['token'],'rating':'good'});self.assertEqual(r['xpEarned'],3);self.assertEqual(r['record']['interval'],1)
  self.request('/api/learning/review/rate',{'token':p['token'],'rating':'good'},status=409)
  before=copy.deepcopy(r['record']);p=self.request('/api/learning/review/start',{'itemId':iid});self.assertTrue(p['practiceOnly'])
  a=self.request('/api/learning/review/answer',{'token':p['token'],'answer':'错误'});self.assertFalse(a['correct'])
  self.request('/api/learning/review/rate',{'token':p['token'],'rating':'easy'},status=400)
  r=self.request('/api/learning/review/rate',{'token':p['token'],'rating':'again'});self.assertEqual(r['record'],before);self.assertEqual(r['xpEarned'],0)
  for rating,target in [('hard','zt-01-v02'),('easy','zt-01-v03')]:
   p=self.request('/api/learning/review/start',{'itemId':target});self.request('/api/learning/review/answer',{'token':p['token'],'answer':'My attempted meaning, compared with the source.'})
   out=self.request('/api/learning/review/rate',{'token':p['token'],'rating':rating})
   self.assertEqual(out['xpEarned'],3);self.assertEqual(out['record']['lastRating'],rating)
   self.assertEqual(out['record']['interval'],1 if rating=='hard' else 3)
  self.stop();self.start();self.assertEqual(self.request('/api/bootstrap')['state']['learning']['srs'][iid],before)
 def test_concurrent_retrievals_and_recommend_invalidate(self):
  iid='zt-01-v01';a=self.request('/api/learning/review/start',{'itemId':iid});b=self.request('/api/learning/review/start',{'itemId':iid})
  for p in [a,b]:self.request('/api/learning/review/answer',{'token':p['token'],'answer':'Thailand'})
  self.request('/api/learning/review/rate',{'token':a['token'],'rating':'good'})
  self.request('/api/learning/review/rate',{'token':b['token'],'rating':'good'},status=409)
  p=self.request('/api/learning/review/start',{'itemId':iid});self.request('/api/learning/review/answer',{'token':p['token'],'answer':'泰国'});self.login()
  self.request('/api/teacher/learning/recommend',{'itemId':iid,'note':'Use this in a connected response.'})
  self.request('/api/learning/review/rate',{'token':p['token'],'rating':'good'},status=409)
 def test_phrasebook_persistence_duplicate_and_teacher_review(self):
  p=self.request('/api/learning/phrases',{'chinese':'请问您希望什么时候入住？','english':'Ask for the arrival date politely.','theme':'Reservations'})
  self.assertEqual(p['origin'],'personal_unverified');self.assertEqual(self.request('/api/learning/reviews')['counts']['due'],1)
  a=self.request('/api/learning/phrases',{'itemId':'zt-01-v01'});b=self.request('/api/learning/phrases',{'itemId':'zt-01-v01'});self.assertEqual(a['id'],b['id'])
  w=self.request('/api/learning/work',{'kind':'challenge','id':'hospitality-welcome','text':'您好，欢迎来到酒店。请问您一路上还顺利吗？我先帮您确认房间是否准备好了，然后向您说明可以入住的时间。请问您需要先寄存行李吗？','submit':True})
  self.assertEqual(w['xpEarned'],12);self.assertEqual(self.request('/api/learning/work',{'kind':'challenge','id':'hospitality-welcome','text':w['work']['text'],'submit':True})['xpEarned'],0)
  self.request('/api/teacher/learning',status=401);self.login();r=w['work']
  assessed=self.request('/api/teacher/learning/assessment',{'responseId':r['id'],'revision':r['revision'],'scores':{k:3 for k in r['criteria']},'comment':'Clear next action; add an explicit check-back time only once confirmed.'})
  self.assertFalse(assessed['teacherReview']['officialGrade'])
  revised=self.request('/api/learning/work',{'kind':'challenge','id':'hospitality-welcome','text':r['text']+'我会再向您确认。','submit':False})['work'];self.assertIsNone(revised['teacherReview']);self.assertEqual(len(revised['reviewHistory']),1)
  self.stop();self.start();self.assertEqual(len(self.request('/api/learning/phrases')['items']),2);self.assertIn(r['id'],self.request('/api/bootstrap')['state']['learning']['work'])
 def test_all_100_steps_complete_unlock_and_xp_idempotence(self):
  self.request('/api/learning/step',{'stepId':'zt-01-step-2'},status=409)
  # Perform all objective, retrieval, response and completion gates over real HTTP.
  for lesson in self.curriculum['lessons']:
   unit=next(u for u in self.request('/api/learning')['path']['units'] if u['id']==lesson['id'])
   for s in unit['steps']:
    self.request('/api/learning/step',{'stepId':s['id']})
    if s['stage']=='discover':
     for iid in s['coreVocabularyIds']:
      p=self.request('/api/learning/review/start',{'itemId':iid});self.request('/api/learning/review/answer',{'token':p['token'],'answer':'Recall attempt; comparing the source meaning.'});self.request('/api/learning/review/rate',{'token':p['token'],'rating':'good'})
    for q in lesson['questions']:
     if q['id'] in s['questionIds'] or s['stage']=='apply':self.request('/api/attempt',{'lessonId':lesson['id'],'questionId':q['id'],'answer':q.get('answer') or q['acceptedAnswers'][0]})
    for t in lesson['tasks']:
     if t['id'] in s['taskIds']:self.request('/api/response',{'lessonId':lesson['id'],'taskId':t['id'],'text':t['model'],'submit':True})
    if s['stage']=='build':self.request('/api/learning/work',{'id':s['id'],'kind':'build','text':'我可以根据客人的问题先确认实际情况，然后清楚地解释下一步安排。','submit':True})
    result=self.request('/api/learning/step',{'stepId':s['id'],'complete':True,'acknowledge':True,**({'text':'现在我能用中文确认客人的需要，下次要更自然地说明理由。'} if s['stage']=='apply' else {})})
    self.assertEqual(result['xpEarned'],25);self.assertEqual(self.request('/api/learning/step',{'stepId':s['id'],'complete':True,'acknowledge':True})['xpEarned'],0)
  d=self.request('/api/learning');self.assertEqual((d['completedSteps'],d['completedUnits']),(100,20));self.assertIsNone(d['nextStep'])
  self.assertEqual(sum(e['xp'] for k,e in self.server.store.state['learning']['xpLedger'].items() if k.startswith('step:')),2500)
 def test_choice_feedback_and_teacher_edits_preserve_path(self):
  q=self.curriculum['lessons'][0]['questions'][0];p=self.request('/api/learning/review/start',{'itemId':q['id']})
  a=self.request('/api/learning/review/answer',{'token':p['token'],'answer':q['answer']})
  self.assertTrue(a['correct']);self.assertEqual(a['expected'],next(o['text'] for o in q['options'] if o['id']==q['answer']))
  self.login();lesson=copy.deepcopy(self.curriculum['lessons'][0]);lesson['questions'][0]['explanation']+=' Teacher correction.'
  self.request('/api/teacher/lesson',{'lesson':lesson})
  self.request('/api/learning/review/rate',{'token':p['token'],'rating':'good'},status=409)
  bad=copy.deepcopy(lesson);bad['tasks'][0]['id']='changed-task-id'
  self.request('/api/teacher/lesson',{'lesson':bad},status=422)
  bad=copy.deepcopy(lesson);bad['originalTitle']='Invented original title'
  self.request('/api/teacher/lesson',{'lesson':bad},status=422)
  self.assertEqual(len(self.request('/api/learning')['path']['units']),20)
 def test_completion_validation_and_objective_xp_cap(self):
  original_save=self.server.store.save_state;finished=[]
  def delayed_save():
   time.sleep(.05);original_save();finished.append(True)
  with patch.object(self.server.store,'save_state',side_effect=delayed_save):
   self.request('/api/learning');self.assertEqual(finished,[True],'Dashboard response must follow a completed disk save')
  self.request('/api/learning/step',{'stepId':'zt-01-step-1','complete':True,'acknowledge':True},status=409)
  self.assertNotIn('zt-01-step-1',self.request('/api/bootstrap')['state']['learning']['steps'])
  self.request('/api/learning/work',{'kind':'challenge','id':'hospitality-welcome','text':'欢迎','submit':True},status=400)
  self.assertEqual(self.request('/api/bootstrap')['state']['learning']['work'],{})
  q=self.curriculum['lessons'][0]['questions'][0]
  for i in range(4):self.request('/api/attempt',{'lessonId':'zt-01','questionId':q['id'],'answer':q['answer']})
  ledger=self.request('/api/bootstrap')['state']['learning']['xpLedger'];self.assertEqual(sum(v['xp'] for v in ledger.values()),2)
 def test_timer_settings_date_boundary_and_multiple_windows(self):
  self.request('/api/learning/settings',{'timeZone':'Invalid/Zone'},status=400)
  self.request('/api/learning/settings',{'dailyGoal':15,'weeklyGoal':5,'timeZone':'Asia/Bangkok'})
  at=datetime(2026,10,30,16,59,50,tzinfo=UTC)
  with patch('app.learning_api.L.moment',wraps=L.moment) as clock:
   clock.side_effect=lambda value=None: at if value is None else datetime.fromisoformat(str(value).replace('Z','+00:00')).astimezone(UTC) if isinstance(value,str) else value.astimezone(UTC)
   s=self.request('/api/learning/session',{'kind':'review'});t=self.request('/api/learning/session',{'kind':'review'});at+=timedelta(seconds=20)
   a=self.request('/api/learning/session',{'sessionId':s['sessionId'],'active':True});b=self.request('/api/learning/session',{'sessionId':t['sessionId'],'active':True})
   self.assertEqual(a['creditedSeconds'],20);self.assertEqual(b['creditedSeconds'],0)
  days=self.server.store.state['learning']['daily'];self.assertEqual(days['2026-10-30']['activeSeconds'],10);self.assertEqual(days['2026-10-31']['activeSeconds'],10)
  public=self.request('/api/bootstrap')['state']['learning'];self.assertNotIn('sessions',public);self.assertNotIn('clockLastAt',public)

# Avoid inherited fixtures being discovered twice; only new microlearning tests here.
for name in list(AppTests.__dict__):
 if name.startswith('test_'):setattr(LearningAPITests,name,None)
del AppTests
if __name__=='__main__':unittest.main(verbosity=2)
