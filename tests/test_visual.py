"""Visual curriculum and actual HTTP regression tests; isolated student records."""
import copy,json,unittest
from pathlib import Path
import test_application as baseline
from app import visual
from scripts.validate_visual_learning import validate
ROOT=Path(__file__).resolve().parents[1]
class VisualDatasetTests(unittest.TestCase):
 def test_all_source_assets_and_visual_answer_keys(self):
  self.assertEqual(validate(),[])
  d=visual.load();self.assertEqual(len(d['units']),20);self.assertEqual(sum(len(u['vocabulary']) for u in d['units']),268)
  types={a['type'] for u in d['units'] for a in u['activities']}
  self.assertGreaterEqual(len(types),8)
 def test_public_visual_catalog_never_reveals_keys(self):
  for u in visual.public_config(visual.load())['units']:
   for a in u['activities']:
    for field in ['answer','accepted','expected','explanation','model']:self.assertNotIn(field,a)
class VisualAPITests(unittest.TestCase):
 setUp=baseline.AppTests.setUp
 start=baseline.AppTests.start
 stop=baseline.AppTests.stop
 tearDown=baseline.AppTests.tearDown
 request=baseline.AppTests.request
 login=baseline.AppTests.login
 def test_every_visual_key_wrong_feedback_and_repeat_xp(self):
  d=visual.load();self.request('/api/teacher/visual',status=401)
  public=self.request('/api/visual');self.assertEqual(len(public['units']),20)
  count=0
  for u in d['units']:
   for a in u['activities']:
    if a['type']=='photo_description':continue
    key=a.get('answer') or a['accepted'][0]
    r=self.request('/api/visual/attempt',{'activityId':a['id'],'answer':key})
    self.assertTrue(r['correct'],a['id']);self.assertEqual(r['expected'],a['expected']);self.assertTrue(r['explanation']);self.assertEqual(r['xpEarned'],2);count+=1
    self.assertEqual(self.request('/api/visual/attempt',{'activityId':a['id'],'answer':key})['xpEarned'],0)
  self.assertEqual(count,72)
  a=d['units'][0]['activities'][0];wrong=next(o['id'] for o in a['options'] if o['id']!=a['answer'])
  r=self.request('/api/visual/attempt',{'activityId':a['id'],'answer':wrong});self.assertFalse(r['correct']);self.assertEqual(r['xpEarned'],0);self.assertEqual(r['explanation'],a['explanation'])
  self.stop();self.start();self.assertTrue(self.request('/api/bootstrap')['state']['visualLearning']['attempts'])
 def test_visual_writing_review_revision_and_privacy(self):
  aid='zt-03-visual-description';text='图片中可以看到酒店前台和服务人员，这是我能直接观察到的信息。我会先用礼貌的中文向客人问好，再确认客人的需要，不会根据图片猜测房间的价格或入住规定。'
  self.request('/api/visual/response',{'activityId':aid,'text':'太短','submit':True},status=400)
  r=self.request('/api/visual/response',{'activityId':aid,'text':text,'submit':False})['work'];self.assertFalse(r['submitted'])
  r=self.request('/api/visual/response',{'activityId':aid,'text':text,'submit':True})['work']
  payload={'responseId':aid,'revision':r['revision'],'scores':{k:3 for k in r['criteria']},'comment':'Clear observations. Make the follow-up question more specific.'}
  self.request('/api/teacher/visual/assessment',payload,status=401);self.login()
  reviewed=self.request('/api/teacher/visual/assessment',payload);self.assertFalse(reviewed['teacherReview']['officialGrade'])
  changed=self.request('/api/visual/response',{'activityId':aid,'text':text+'请问您有预订吗？','submit':True})['work'];self.assertIsNone(changed['teacherReview']);self.assertEqual(len(changed['reviewHistory']),1)
  self.request('/api/teacher/visual/assessment',payload,status=409)
  self.stop();self.start();self.assertEqual(self.request('/api/bootstrap')['state']['visualLearning']['responses'][aid]['text'],changed['text'])
 def test_visual_activity_uses_existing_real_time_clock(self):
  r=self.request('/api/learning/session',{'kind':'visual'});self.assertTrue(r['sessionId'])
  self.request('/api/learning/session',{'sessionId':r['sessionId'],'active':True})
 def test_invalid_inputs_leave_existing_state_unchanged(self):
  before=self.request('/api/bootstrap')['state']
  self.request('/api/visual/attempt',{'activityId':'not-real','answer':'a'},status=404)
  self.request('/api/visual/attempt',{'activityId':'zt-01-visual-word-v02','answer':'invented-option'},status=400)
  self.request('/api/visual/response',{'activityId':'zt-03-visual-description','text':['not text']},status=400)
  self.assertEqual(self.request('/api/bootstrap')['state'],before)
