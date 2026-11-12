"""Isolated local API tests. Never writes the real student's state or teacher key."""
import copy,json,pathlib,shutil,tempfile,threading,unittest,urllib.request,urllib.error,http.cookiejar,time
import sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server import AppServer
from app.schema import validate_curriculum

class AppTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
  (self.root/'data').mkdir();shutil.copy(ROOT/'data/curriculum.json',self.root/'data/curriculum.json')
  (self.root/'public').mkdir();shutil.copy(ROOT/'public/index.html',self.root/'public/index.html')
  self.curriculum=json.loads((self.root/'data/curriculum.json').read_text());self.lesson=self.curriculum['lessons'][2]
  (self.root/'sources').mkdir();self.stored=self.curriculum['fileInventory'][0]['storedName'];(self.root/'sources'/self.stored).write_bytes(b'isolated-source-download-fixture')
  self.start();self.jar=http.cookiejar.CookieJar();self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
 def start(self):
  self.server=AppServer(('127.0.0.1',0),root=self.root,teacher_key='isolated-test-key')
  self.base='http://127.0.0.1:'+str(self.server.server_port);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def stop(self):self.server.shutdown();self.server.server_close();self.thread.join()
 def tearDown(self):self.stop();self.tmp.cleanup()
 def request(self,path,data=None,status=200):
  req=urllib.request.Request(self.base+path,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,headers={'Content-Type':'application/json','X-App-Request':'1'})
  try:response=self.client.open(req)
  except urllib.error.HTTPError as e:response=e
  self.assertEqual(response.code,status,(path,response.read().decode(errors='replace')) if response.code!=status else path)
  body=response.read();ctype=response.headers.get('Content-Type','');response.close()
  return json.loads(body) if 'application/json' in ctype else body
 def login(self):return self.request('/api/teacher/login',{'key':'isolated-test-key'})
 def response(self,submit=True):
  t=self.lesson['tasks'][0];return self.request('/api/response',{'lessonId':self.lesson['id'],'taskId':t['id'],'text':t['model'],'submit':submit})
 def test_all_twenty_units_and_no_private_keys_in_student_items(self):
  b=self.request('/api/bootstrap');self.assertEqual(len(b['lessons']),20)
  for l in self.curriculum['lessons']:
   out=self.request('/api/lessons/'+l['id']);self.assertEqual(out['adaptationVersion'],2)
   self.assertTrue(out['liveListening']['instructions']);self.assertTrue(out['readings'])
   for q in out['questions']:
    for k in ['answer','acceptedAnswers','explanation']:self.assertNotIn(k,q)
   for t in out['tasks']:self.assertNotIn('model',t)
 def test_every_objective_key_and_wrong_answer_feedback(self):
  count=0
  for l in self.curriculum['lessons']:
   for q in l['questions']:
    answer=q['answer'] if q['type']=='choice' else q['acceptedAnswers'][0]+'。'
    out=self.request('/api/attempt',{'lessonId':l['id'],'questionId':q['id'],'answer':answer});self.assertTrue(out['correct'],q['id']);self.assertEqual(out['explanation'],q['explanation']);count+=1
  self.assertEqual(count,162)
  q=self.lesson['questions'][0];wrong=next(o['id'] for o in q['options'] if o['id']!=q['answer'])
  out=self.request('/api/attempt',{'lessonId':'zt-03','questionId':q['id'],'answer':wrong});self.assertFalse(out['correct']);self.assertTrue(out['explanation'])
  bad=self.request('/api/practice?mode=mistakes');self.assertIn(q['id'],[x['id'] for x in bad['questions']])
  self.request('/api/attempt',{'lessonId':'zt-03','questionId':q['id'],'answer':q['answer']})
  self.assertNotIn(q['id'],[x['id'] for x in self.request('/api/practice?mode=mistakes')['questions']])
 def test_draft_model_gate_and_persistence_after_restart(self):
  t=self.lesson['tasks'][0];payload={'lessonId':'zt-03','taskId':t['id']}
  self.request('/api/model',payload,status=409)
  saved=self.response(False);self.assertFalse(saved['submitted']);self.assertFalse(saved['feedback']['officialGrade'])
  self.assertEqual(self.request('/api/model',payload)['model'],t['model'])
  self.stop();self.start()
  self.assertEqual(self.request('/api/bootstrap')['state']['responses'][t['id']]['text'],t['model'])
 def test_completion_gate_then_complete(self):
  self.request('/api/progress',{'lessonId':'zt-03','complete':True},status=409)
  for q in self.lesson['questions']:
   self.request('/api/attempt',{'lessonId':'zt-03','questionId':q['id'],'answer':q.get('answer') or q['acceptedAnswers'][0]})
  self.response(True)
  p=self.request('/api/progress',{'lessonId':'zt-03','section':'reflection','reflection':'现在我能清楚说明总额，下次要更自然地回应客人的拒绝。','complete':True})
  self.assertTrue(p['completed']);self.assertTrue(self.request('/api/bootstrap')['state']['progress']['zt-03']['completed'])
 def test_rejected_progress_does_not_change_state(self):
  for payload,status in [
   ({'lessonId':'zt-03','section':'reflection','mark':True,'reflection':[]},400),
   ({'lessonId':'zt-03','section':'reflection','mark':True,'reflection':'尚未完成练习，不应记录完成。','complete':True},409)
  ]:
   before=self.request('/api/bootstrap')['state'];saved=(self.root/'data/state.json').read_bytes()
   self.request('/api/progress',payload,status=status)
   self.assertEqual(self.request('/api/bootstrap')['state'],before)
   self.assertEqual((self.root/'data/state.json').read_bytes(),saved)
 def test_spaced_review_and_mixed_review(self):
  self.assertEqual(self.request('/api/practice')['startedCount'],0)
  v=self.lesson['vocabulary'][0];body={'lessonId':'zt-03','vocabularyId':v['id'],'rating':'again'}
  r=self.request('/api/review',body);self.assertEqual(r['lapses'],1);self.assertEqual(r['interval'],0)
  early=self.request('/api/review',dict(body,rating='good'));self.assertEqual(early['dueAt'],r['dueAt']);self.assertEqual(early['interval'],0)
  self.assertEqual(self.request('/api/practice')['startedCount'],1)
 def test_teacher_protection_source_cookie_and_export(self):
  self.request('/api/teacher',status=401);self.request('/source-file/'+self.stored,status=401)
  self.request('/api/teacher/login',{'key':'wrong'},status=401);self.login()
  self.assertEqual(next(iter(self.jar)).path,'/');self.assertEqual(self.request('/source-file/'+self.stored),b'isolated-source-download-fixture')
  self.assertEqual(self.request('/api/teacher')['validation'],[])
  self.assertIn('curriculum',self.request('/api/teacher/export'))
  self.assertNotIn('curriculum',self.request('/api/export'))
 def test_criterion_review_revision_and_reassessment(self):
  r=self.response();self.login();t=self.lesson['tasks'][0];scores={k:3 for k in t['criteria']}
  payload={'responseId':r['id'],'revision':r['revision'],'scores':scores,'comment':'Quote the total precisely, then identify the missing number of nights.'}
  out=self.request('/api/teacher/assessment',payload);self.assertFalse(out['teacherReview']['officialGrade']);self.assertEqual(set(out['teacherReview']['scores']),set(t['criteria']))
  self.request('/api/teacher/assessment',dict(payload,revision=0),status=409)
  changed=self.request('/api/response',{'lessonId':'zt-03','taskId':t['id'],'text':t['model']+'我还需要先确认入住晚数。','submit':False})
  self.assertIsNone(changed['teacherReview']);self.assertFalse(changed['submitted']);self.assertEqual(len(changed['reviewHistory']),1)
 def test_teacher_edits_validation_and_source_immutability(self):
  self.login();lesson=copy.deepcopy(self.lesson);lesson['subtitle']='Edited training subtitle'
  self.request('/api/teacher/lesson',{'lesson':lesson});self.assertEqual(self.request('/api/lessons/zt-03')['subtitle'],'Edited training subtitle')
  self.assertTrue(list((self.root/'data/backups').glob('*.json')))
  bad=copy.deepcopy(lesson);bad['questions'][0]['answer']='absent';self.request('/api/teacher/lesson',{'lesson':bad},status=422)
  bad=copy.deepcopy(lesson);bad['sourceSlides'][0]['text']='replacement';self.request('/api/teacher/lesson',{'lesson':bad},status=400)
  bad=copy.deepcopy(lesson);bad['questions']='broken';self.request('/api/teacher/lesson',{'lesson':bad},status=422)
  for field in ['pedagogy','liveListening']:
   bad=copy.deepcopy(lesson);bad[field]='broken';self.request('/api/teacher/lesson',{'lesson':bad},status=422)
  bad=copy.deepcopy(lesson);bad['pedagogy']['sequence'][0]['minutes']=0;self.request('/api/teacher/lesson',{'lesson':bad},status=422)
  bad=copy.deepcopy(lesson);bad['readings'][0]['discussion'][0]['guide']='';self.request('/api/teacher/lesson',{'lesson':bad},status=422)
 def test_invalid_answers_and_csv_export(self):
  q=self.lesson['questions'][0]
  self.request('/api/attempt',{'lessonId':'zt-03','questionId':q['id'],'answer':'unknown-option'},status=400)
  self.request('/api/response',{'lessonId':'zt-03','taskId':self.lesson['tasks'][0]['id'],'text':'','submit':True},status=400)
  self.request('/api/progress',{'lessonId':'zt-03','reflection':'=HYPERLINK("example")'})
  csv=self.request('/api/export?format=csv').decode('utf-8-sig');self.assertIn("'=HYPERLINK",csv)
  self.assertIsInstance(self.request('/api/export')['state']['progress'],dict)

if __name__=='__main__':unittest.main(verbosity=2)
