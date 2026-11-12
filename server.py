#!/usr/bin/env python3
"""Emmalyne's Chinese Atelier: a dependency-free, localhost-only learning app."""
import argparse
import copy
import csv
from datetime import datetime, timedelta, timezone
import hashlib
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import sys
import time
import unicodedata
from urllib.parse import unquote, urlsplit, parse_qs

from app.storage import Store
from app import visual
from app.schema import validate_curriculum
from app.extract import extract_file
from app import learning as learning_engine
from app import learning_api

ROOT = Path(__file__).resolve().parent
MAX_JSON = 5 * 1024 * 1024
MAX_SOURCE = 100 * 1024 * 1024
SECTIONS = {'overview','vocabulary','reading','language','practice','challenge','reflection','sources'}
LEARNABLE = {'available','published'}


def now(): return datetime.now(timezone.utc).isoformat()


def normalize(value):
    return re.sub(r'[\s，。！？,.!?、；;：:]', '', unicodedata.normalize('NFKC', str(value))).casefold()


def char_count(value): return len(re.findall(r'[\u3400-\u9fff]', value))


def public_lesson(lesson):
    item = copy.deepcopy(lesson)
    for q in item.get('questions', []):
        q.pop('answer', None)
        q.pop('acceptedAnswers', None)
        q.pop('explanation', None)
    for t in item.get('tasks', []): t.pop('model', None)
    return item


def summary(lesson):
    keys = ['id','number','kind','title','originalTitle','subtitle','status','minutes','approval']
    item = {k: lesson.get(k) for k in keys}
    item.update({'vocabularyCount': len(lesson['vocabulary']), 'questionCount': len(lesson['questions']), 'taskCount': len(lesson['tasks']), 'slideCount': len(lesson['sourceSlides'])})
    return item


def writing_feedback(text, task):
    count = char_count(text)
    return {'kind': 'automated_practice', 'characters': count, 'guidance': task['minCharacters'], 'messages': [
        f'{count} Chinese characters. Suggested minimum for this task: {task["minCharacters"]}. Character count is a practice check, not a quality score.',
        'Read your answer as the intended audience: is the requested next step clear?',
        'Underline one lesson pattern, check its word order, and verify your response addresses each part of the brief.',
        'Check tone and assumptions. A teacher must assess accuracy, meaning, cultural understanding and professional appropriateness.'
    ], 'officialGrade': False}


class AppServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    def __init__(self, address, root=ROOT, teacher_key=None):
        self.root = Path(root)
        self.store = Store(root)
        errors = validate_curriculum(self.store.curriculum)
        if errors: raise RuntimeError('Invalid curriculum: ' + '; '.join(errors[:10]))
        self.sessions = {}
        self.failures = []
        key_path = self.root / 'data/teacher-key'
        if teacher_key:
            self.teacher_key = teacher_key
        elif os.getenv('TEACHER_KEY'):
            self.teacher_key = os.environ['TEACHER_KEY']
        elif key_path.exists():
            self.teacher_key = key_path.read_text().strip()
        else:
            self.teacher_key = secrets.token_urlsafe(18)
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as f: f.write(self.teacher_key)
        super().__init__(address, Handler)


class APIError(Exception):
    def __init__(self, status, message, details=None):
        self.status, self.message, self.details = status, message, details


class Handler(BaseHTTPRequestHandler):
    server_version = 'ChineseAtelier/1.0'

    def log_message(self, format, *args):
        # Avoid logging student answers, teacher credentials or query strings.
        if len(args) > 1 and str(args[1]).startswith(('4','5')):
            sys.stderr.write('HTTP ' + str(args[1]) + ' ' + urlsplit(self.path).path + '\n')

    @property
    def store(self): return self.server.store

    def teacher(self):
        cookie = SimpleCookie()
        try: cookie.load(self.headers.get('Cookie', ''))
        except Exception: return False
        token = cookie.get('atelier_teacher')
        return bool(token and self.server.sessions.get(token.value, 0) > time.time())

    def require_teacher(self):
        if not self.teacher(): raise APIError(401, 'Open the teacher desk and enter the local teacher key.')

    def send(self, value, status=200, content_type='application/json; charset=utf-8', extra=None):
        body = json.dumps(value, ensure_ascii=False).encode() if content_type.startswith('application/json') else value if isinstance(value, bytes) else value.encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store' if self.path.startswith('/api') else 'no-cache')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        for k,v in (extra or {}).items(): self.send_header(k,v)
        self.end_headers()
        self.wfile.write(body)

    def guard(self, mutation=False):
        host = self.headers.get('Host','')
        allowed = {'localhost:'+str(self.server.server_port), '127.0.0.1:'+str(self.server.server_port)}
        if host not in allowed: raise APIError(403,'This app accepts localhost requests only.')
        if mutation:
            origin = self.headers.get('Origin')
            if origin and origin not in {'http://'+h for h in allowed}: raise APIError(403,'Cross-origin requests are not allowed.')
            if self.headers.get('X-App-Request') != '1': raise APIError(403,'A same-origin app request is required.')

    def read_body(self, maximum=MAX_JSON):
        try: length = int(self.headers.get('Content-Length',0))
        except ValueError: raise APIError(400,'Invalid content length.')
        if length < 1 or length > maximum: raise APIError(413, f'Request must be between 1 byte and {maximum//1024//1024} MB.')
        body = self.rfile.read(length)
        if len(body) != length: raise APIError(400,'Incomplete request body.')
        return body

    def json_body(self):
        if not self.headers.get('Content-Type','').startswith('application/json'): raise APIError(415,'JSON content is required.')
        try: value=json.loads(self.read_body())
        except (ValueError, UnicodeError): raise APIError(400,'The JSON could not be read. Check its syntax and try again.')
        if not isinstance(value,dict): raise APIError(400,'Expected a JSON object.')
        return value

    def event(self, title, lesson_id=None):
        self.store.state['activity'].insert(0, {'id': secrets.token_hex(8),'title':title,'lessonId':lesson_id,'at':now()})
        self.store.state['activity'] = self.store.state['activity'][:100]

    def progress(self, lesson_id):
        return self.store.state['progress'].setdefault(lesson_id, {'sections':[], 'completed':False, 'reflection':'', 'lastSection':'overview', 'updatedAt':now()})

    def find_item(self, lesson, field, id):
        item=next((i for i in lesson[field] if i['id']==id),None)
        if not item: raise APIError(404,'That learning item no longer exists. Reload the lesson.')
        return item

    def get_lesson(self, lesson_id):
        lesson=self.store.lesson(lesson_id)
        if not lesson: raise APIError(404,'Lesson not found.')
        return lesson

    def do_GET(self): self.handle_request(False)
    def do_POST(self): self.handle_request(True)

    def handle_request(self, mutation):
        try:
            self.guard(mutation)
            path=urlsplit(self.path).path
            if path.startswith('/api/'):
                with self.store.lock:
                    self.api_post(path) if mutation else self.api_get(path)
            elif mutation:
                raise APIError(404,'Endpoint not found.')
            else: self.static(path)
        except (learning_api.LearningError, visual.VisualError) as e:
            self.send({"error":e.message},e.status)
        except APIError as e:
            self.send({'error':e.message, 'details': e.details}, e.status)
        except (BrokenPipeError, ConnectionResetError): pass
        except Exception as e:
            sys.stderr.write('Request failed: '+type(e).__name__+'\n')
            self.send({'error':'The request could not be completed. Existing saved files have not been replaced with empty data.'},500)

    def api_get(self,path):
        if visual.get(self,path): return
        if learning_api.get(self,path): return
        if path=='/api/bootstrap':
            curriculum=self.store.curriculum
            self.send({'student':{'name':'Emmalyne','grade':'Grade 11 · Chinese B','goal':'Hospitality Management'}, 'attribution':curriculum['attribution'],'criteria':curriculum['criteria'],'lessons':[summary(l) for l in curriculum['lessons']], 'supplementary':[summary(l) for l in curriculum['supplementary']], 'state':learning_api.public_state(self.store.state), 'teacher': self.teacher(), 'sourceStats': {'files':len(curriculum['fileInventory']),'slides':sum(len(l['sourceSlides']) for l in curriculum['lessons']), 'visuals':sum(len(s['visuals']) for l in curriculum['lessons'] for s in l['sourceSlides']), 'vocabulary':sum(len(l['vocabulary']) for l in curriculum['lessons'])}})
        elif path.startswith('/api/lessons/'):
            l=self.get_lesson(path.rsplit('/',1)[1])
            if l['status'] not in LEARNABLE and not self.teacher():
                out=summary(l)
                out['processing']=l.get('processing',{})
                self.send(out)
            else: self.send(public_lesson(l))
        elif path=='/api/practice':
            query=parse_qs(urlsplit(self.path).query)
            mode=query.get('mode',['mixed'])[0]
            all_lessons=[l for l in self.store.curriculum['lessons']+self.store.curriculum['supplementary'] if l['status'] in LEARNABLE]
            # Mixed review is restricted to started lessons; the UI explicitly offers a first-lesson start otherwise.
            started=[l for l in all_lessons if l['id'] in self.store.state['progress'] or any(a['lessonId']==l['id'] for a in self.store.state['attempts'])]
            selected=started
            questions=[dict(q,lessonId=l['id'],lessonTitle=l['title']) for l in selected for q in public_lesson(l)['questions']]
            if mode=='mistakes':
                latest={}
                for a in self.store.state['attempts']: latest[a['questionId']]=a
                missed={q for q,a in latest.items() if not a['correct']}
                questions=[q for q in questions if q['id'] in missed]
            elif mode in {'accuracy','comprehension','audience'}:
                questions=[q for q in questions if q['skill']==mode or (mode=='audience' and q['skill'] in {'communication','intercultural'})]
            vocabulary=[dict(v,lessonId=l['id'],lessonTitle=l['title']) for l in selected for v in l['vocabulary']]
            self.send({'questions':questions,'vocabulary':vocabulary, 'startedCount':len(started)})
        elif path=='/api/teacher':
            self.require_teacher()
            self.send({'curriculum':self.store.curriculum,'state':self.store.state, 'validation':validate_curriculum(self.store.curriculum)})
        elif path in {'/api/export','/api/teacher/export'}:
            if 'teacher' in path: self.require_teacher()
            query=parse_qs(urlsplit(self.path).query)
            if query.get('format',['json'])[0]=='csv':
                out=io.StringIO()
                writer=csv.writer(out)
                writer.writerow(['lesson_id','title','completed','sections_completed','reflection','updated_at','completed_steps','total_steps','review_items','retrieval_mastered_items'])
                def safe(v):
                    v=str(v)
                    return "'"+v if v.startswith(('=','+','-','@','\t','\r')) else v
                for l in self.store.curriculum['lessons']+self.store.curriculum['supplementary']:
                    p=self.store.state['progress'].get(l['id'],{})
                    learning=learning_engine.initialize(self.store.state)
                    steps=sum(bool(learning['steps'].get(l['id']+'-step-'+str(i),{}).get('completed')) for i in range(1,6)) if l['kind']=='textbook' else 0
                    records=[r for r in learning['srs'].values() if r.get('lessonId')==l['id']]
                    writer.writerow([safe(l['id']),safe(l['title']),p.get('completed',False),len(p.get('sections',[])),safe(p.get('reflection','')),p.get('updatedAt',''),steps,5 if l['kind']=='textbook' else 0,len(records),sum(r['mastery']=='mastered' for r in records)])
                self.send('\ufeff'+out.getvalue(),content_type='text/csv; charset=utf-8',extra={'Content-Disposition':'attachment; filename="emmalyne-progress.csv"'})
            else:
                value={'schemaVersion':1,'exportedAt':now(),'student':'Emmalyne','state':learning_api.public_state(self.store.state)}
                if 'teacher' in path: value['curriculum']=self.store.curriculum
                self.send(value,extra={'Content-Disposition':'attachment; filename="emmalyne-portfolio.json"'})
        else: raise APIError(404,'Endpoint not found.')

    def api_post(self,path):
        if path=='/api/teacher/source':
            self.require_teacher()
            self.upload_source()
            return
        body=self.json_body()
        if path=='/api/teacher/login':
            self.server.failures=[t for t in self.server.failures if t>time.time()-60]
            if len(self.server.failures)>=6: raise APIError(429,'Too many attempts. Wait one minute before trying again.')
            if not secrets.compare_digest(str(body.get('key','')),self.server.teacher_key):
                self.server.failures.append(time.time())
                raise APIError(401,'The teacher key is not correct. Find the local key in the server terminal or data/teacher-key.')
            token=secrets.token_urlsafe(32)
            self.server.sessions[token]=time.time()+8*3600
            self.send({'ok':True},extra={'Set-Cookie':'atelier_teacher='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'})
            return
        if path=='/api/teacher/logout':
            cookie=SimpleCookie(); cookie.load(self.headers.get('Cookie',''))
            if cookie.get('atelier_teacher'): self.server.sessions.pop(cookie['atelier_teacher'].value,None)
            self.send({'ok':True},extra={'Set-Cookie':'atelier_teacher=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
            return
        if visual.post(self,path,body): return
        if learning_api.post(self,path,body): return
        if path.startswith('/api/teacher/'):
            self.require_teacher()
            self.teacher_post(path,body)
            return
        if path=='/api/preferences':
            gloss=body.get('gloss','en')
            if gloss not in {'en','th','de'}: raise APIError(400,'Unknown gloss preference.')
            self.store.state['preferences'].update({'gloss':gloss,'pinyin':bool(body.get('pinyin',False))})
            self.store.save_state(); self.send(self.store.state['preferences']); return
        l=self.get_lesson(body.get('lessonId',''))
        if l['status'] not in LEARNABLE: raise APIError(409,'This lesson is not ready for student practice.')
        if path=='/api/progress':
            section=body.get('section','overview')
            if section not in SECTIONS: raise APIError(400,'Unknown lesson section.')
            # Prepare an independent record. A rejected request must not change
            # in-memory progress or activity and later leak into a saved state.
            p=copy.deepcopy(self.store.state['progress'].get(l['id'], {'sections':[], 'completed':False, 'reflection':'', 'lastSection':'overview', 'updatedAt':now()}))
            p.update({'lastSection':section,'updatedAt':now()})
            marked=bool(body.get('mark')) and section not in p['sections']
            if marked:
                p['sections'].append(section)
            if 'reflection' in body:
                reflection=body['reflection']
                if not isinstance(reflection,str) or len(reflection)>4000: raise APIError(400,'Reflection must be under 4,000 characters.')
                p['reflection']=reflection
            if body.get('complete'):
                latest={a['questionId']:a for a in self.store.state['attempts'] if a['lessonId']==l['id']}
                has_questions=all(q['id'] in latest for q in l['questions'])
                has_work=any(r['lessonId']==l['id'] and r['submitted'] and bool(r['text'].strip()) for r in self.store.state['responses'].values())
                if not has_questions or not has_work or not p['reflection'].strip():
                    raise APIError(409,'Attempt every formative question, submit one communication task and save a reflection before completing the lesson.')
                p['completed']=True
            self.store.state['progress'][l['id']]=p
            if marked:
                self.event('Completed '+section,l['id'])
            if body.get('complete'):
                self.event('Completed '+l['title'],l['id'])
            self.store.save_state(); self.send(p)
        elif path=='/api/attempt':
            q=self.find_item(l,'questions',body.get('questionId'))
            answer=str(body.get('answer','')).strip()
            if not answer or len(answer)>1000: raise APIError(400,'Enter an answer first (maximum 1,000 characters).')
            if q['type']=='choice' and answer not in {o['id'] for o in q['options']}: raise APIError(400,'Choose one of the displayed options.')
            correct=answer==q['answer'] if q['type']=='choice' else normalize(answer) in {normalize(x) for x in q['acceptedAnswers']}
            a={'id':secrets.token_hex(10),'questionId':q['id'],'lessonId':l['id'],'answer':answer,'correct':correct,'skill':q['skill'],'at':now()}
            self.store.state['attempts'].append(a)
            self.store.state['attempts']=self.store.state['attempts'][-20000:]
            self.progress(l['id'])
            self.event('Practised '+l['title'],l['id'])
            learning=learning_engine.initialize(self.store.state)
            item=learning_engine.catalog(self.store.curriculum,learning)[q['id']]
            review=learning_engine.enroll(learning,item)
            if not correct: review.update(nextReviewAt=now(),mastery='relearning',failedReviews=review['failedReviews']+1,revision=review.get('revision',0)+1)
            if correct: learning_engine.award(learning,'question:'+q['id'],2,'question')
            self.store.save_state(); self.send(dict(a,explanation=q['explanation'],correctAnswer=q.get('answer'),acceptedAnswers=q.get('acceptedAnswers')))
        elif path=='/api/response':
            t=self.find_item(l,'tasks',body.get('taskId'))
            text=body.get('text','')
            if not isinstance(text,str) or len(text)>12000: raise APIError(400,'A response must be text, up to 12,000 characters.')
            if body.get('submit') and not text.strip(): raise APIError(400,'Write a response before submitting.')
            old=self.store.state['responses'].get(t['id'],{})
            changed=old.get('text')!=text
            revision=old.get('revision',0)+(1 if changed else 0)
            review=old.get('teacherReview')
            history=old.get('reviewHistory',[])
            if changed and review:
                history=(history+[dict(review,reviewedText=old.get('text',''),revision=old.get('revision',0))])[-10:]
                review=None
            record={'id':t['id'],'lessonId':l['id'],'taskId':t['id'],'taskTitle':t['title'],'text':text,'revision':revision,'submitted':bool(body.get('submit')) or (old.get('submitted',False) and not changed), 'updatedAt':now(),'teacherReview':review,'reviewHistory':history,'feedback':writing_feedback(text,t)}
            self.store.state['responses'][t['id']]=record
            self.progress(l['id'])
            if body.get('submit'): self.event('Submitted '+t['title'],l['id'])
            self.store.save_state(); self.send(record)
        elif path=='/api/model':
            t=self.find_item(l,'tasks',body.get('taskId'))
            r=self.store.state['responses'].get(t['id'])
            if not r or not r['text'].strip(): raise APIError(409,'Save your own draft before opening the model response.')
            self.send({'model':t['model'],'origin':t['origin'],'notice':'Newly authored model; one possible response, not a textbook answer key or official IB standard.'})
        elif path=='/api/review':
            v=self.find_item(l,'vocabulary',body.get('vocabularyId'))
            rating=body.get('rating')
            if rating not in {'again','hard','good','easy'}: raise APIError(400,'Choose Again, Hard, Good or Easy.')
            learning=learning_engine.initialize(self.store.state)
            item=learning_engine.catalog(self.store.curriculum,learning)[v['id']]
            existing=learning['srs'].get(v['id'])
            record=learning_engine.enroll(learning,item,due_now=True)
            if existing is None or learning_engine.moment(record['nextReviewAt'])<=learning_engine.moment():
                record=learning_engine.schedule(record,rating,learning['settings']['timeZone'])
            # Archive flashcards share the same schedule; early clicks never move due dates.
            learning['srs'][v['id']]=record
            r={'vocabularyId':v['id'],'lessonId':l['id'],'interval':record['interval'],'repetitions':record['successfulReviews']+record['failedReviews'],'lapses':record['failedReviews'],'dueAt':record['nextReviewAt'],'lastRating':rating,'updatedAt':now()}
            self.store.state['reviews'][v['id']]=r
            self.progress(l['id']); self.event('Reviewed '+v['chinese'],l['id'])
            self.store.save_state(); self.send(r)
        else: raise APIError(404,'Endpoint not found.')

    def teacher_post(self,path,body):
        if path=='/api/teacher/lesson':
            proposed=body.get('lesson')
            if not isinstance(proposed,dict): raise APIError(400,'Provide a lesson object.')
            old=self.get_lesson(proposed.get('id',''))
            if proposed.get('number')!=old.get('number') or proposed.get('kind')!=old['kind']: raise APIError(400,'Stable lesson number and kind cannot change.')
            if proposed.get('sourceSlides')!=old.get('sourceSlides') or proposed.get('processing')!=old.get('processing'):
                raise APIError(400,'Source extraction records are immutable here. Use the slide verification controls, or upload a new source.')
            candidate=copy.deepcopy(self.store.curriculum)
            field='lessons' if old['kind']=='textbook' else 'supplementary'
            index=next(i for i,l in enumerate(candidate[field]) if l['id']==old['id'])
            candidate[field][index]=proposed
            try: errors=validate_curriculum(candidate)
            except (TypeError,AttributeError,KeyError): raise APIError(422,'The lesson structure is invalid. Check array, object and field types.')
            if errors: raise APIError(422,'The edit failed curriculum validation.',errors)
            if old.get('kind')=='textbook':
                if proposed.get('originalTitle')!=old.get('originalTitle'):
                    raise APIError(422,'Preserve the original source title; edit the display title or subtitle instead.')
                for name in ['vocabulary','readings','patterns','questions','tasks']:
                    if not {x['id'] for x in old[name]}<={x['id'] for x in proposed[name]}:
                        raise APIError(422,'Preserve existing learning IDs and saved-work references; edit content in place or add new items.')
                try:
                    learning_engine.build_path(candidate);learning_engine.challenge_catalog(candidate)
                except (StopIteration,KeyError,IndexError,AssertionError):
                    raise APIError(422,'Preserve the interpretation and writing task IDs, at least one role-play, and source-linked patterns for the 100-step path.')
            self.backup_curriculum()
            self.store.save_curriculum(candidate)
            # A teacher correction invalidates open retrieval prompts using the old content.
            pending=getattr(self.server,'learning_pending',{})
            changed_ids={i['id'] for field in ['vocabulary','patterns','questions','tasks'] for i in old[field]}
            for token in list(pending):
                if pending[token]['itemId'] in changed_ids:pending.pop(token)
            self.send({'ok':True,'lesson':proposed})
        elif path=='/api/teacher/verify-slide':
            l=self.get_lesson(body.get('lessonId',''))
            slide=self.find_item(l,'sourceSlides',body.get('slideId'))
            notes=body.get('notes','')
            if not isinstance(notes,str) or len(notes)>4000: raise APIError(400,'Review notes must be under 4,000 characters.')
            slide.update({'reviewStatus':'verified' if body.get('verified') else 'pending','reviewNotes':notes,'reviewedAt':now()})
            self.store.save_curriculum(); self.send(slide)
        elif path=='/api/teacher/assessment':
            r=self.store.state['responses'].get(body.get('responseId'))
            if not r or not r['submitted']: raise APIError(409,'Only a submitted response can receive a teacher review.')
            if body.get('revision')!=r['revision']: raise APIError(409,'The student changed this response. Reload before assessing the current version.')
            scores=body.get('scores',{})
            task=self.find_item(self.get_lesson(r['lessonId']),'tasks',r['taskId'])
            criteria=set(task['criteria'])
            if set(scores)!=criteria or any(type(v)!=int or v not in range(1,5) for v in scores.values()): raise APIError(400,'Provide a teacher level of 1–4 for each criterion selected by this task.')
            comment=body.get('comment','')
            if not isinstance(comment,str) or not comment.strip() or len(comment)>6000: raise APIError(400,'Add actionable teacher feedback (up to 6,000 characters).')
            r['teacherReview']={'scores':scores,'comment':comment,'at':now(),'kind':'teacher_verified','officialGrade':False,'revision':r['revision']}
            self.event('Teacher reviewed '+r['taskTitle'],r['lessonId'])
            self.store.save_state(); self.send(r)
        else: raise APIError(404,'Teacher endpoint not found.')

    def backup_curriculum(self):
        folder=self.server.root/'data/backups'
        folder.mkdir(exist_ok=True)
        target=folder/('curriculum-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
        target.write_text(json.dumps(self.store.curriculum,ensure_ascii=False,indent=2))
        target.chmod(0o600)

    def upload_source(self):
        query=parse_qs(urlsplit(self.path).query)
        try: n=int(query.get('lesson',['0'])[0])
        except ValueError: raise APIError(400,'Select a lesson number from 1 to 20.')
        if n not in range(1,21): raise APIError(400,'Select a lesson number from 1 to 20.')
        name=Path(unquote(self.headers.get('X-Filename',''))).name
        suffix=Path(name).suffix.lower()
        if suffix not in {'.ppt','.pptx'}: raise APIError(415,'Choose an original PPT or PPTX file.')
        body=self.read_body(MAX_SOURCE)
        sha=hashlib.sha256(body).hexdigest()
        existing=next((f for f in self.store.curriculum['fileInventory'] if f['sha256']==sha),None)
        if existing: raise APIError(409,'Duplicate file: already inventoried as '+existing['filename'])
        l=self.store.curriculum['lessons'][n-1]
        if l['sourceSlides']: raise APIError(409,'This lesson already has a source. Keep its stable slide references; use a separate working copy for replacement sources.')
        filename=sha[:16]+suffix
        dest=self.server.root/'sources'/filename
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(body)
        record={'id':'file-'+sha[:20],'filename':name,'sha256':sha,'bytes':len(body),'lessonNumber':n,'storedName':filename,'importedAt':now(),'issues':[]}
        try:
            result=extract_file(dest,n,self.server.root/'public/assets/source')
            record.update({'status':'extracted','slides':len(result['slides']),'issues':result['issues']})
            l.update({'sourceSlides':result['slides'],'sourceRefs':[s['id'] for s in result['slides']],'status':'review','approval':'pending_review'})
            l['processing']={'status':'extracted','files':[record['id']],'issues':result['issues']}
        except Exception as e:
            record.update({'status':'unreadable','issues':[str(e)]})
            l['status']='unreadable'; l['processing']={'status':'unreadable','files':[record['id']],'issues':[str(e)]}
        self.store.curriculum['fileInventory'].append(record)
        self.store.save_curriculum(); self.send(record,201)

    def static(self,path):
        if path in {'/','/teacher'}: path='/index.html'
        if path.startswith('/source-file/'):
            self.require_teacher()
            filename=path.rsplit('/',1)[1]
            record=next((f for f in self.store.curriculum['fileInventory'] if f.get('storedName')==filename),None)
            if not record: raise APIError(404,'Source file not found.')
            target=self.server.root/'sources'/filename
            self.send(target.read_bytes(),content_type='application/octet-stream',extra={'Content-Disposition':"attachment; filename*=UTF-8''"+__import__('urllib.parse',fromlist=['quote']).quote(record['filename'])})
            return
        public=(self.server.root/'public').resolve()
        target=(public/unquote(path).lstrip('/')).resolve()
        if not target.is_relative_to(public) or not target.is_file(): raise APIError(404,'File not found.')
        self.send(target.read_bytes(),content_type=(mimetypes.guess_type(target)[0] or 'application/octet-stream')+('; charset=utf-8' if target.suffix in {'.js','.css','.html','.svg'} else ''))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=int,default=8000)
    args=p.parse_args()
    server=AppServer(('127.0.0.1',args.port))
    print(f'Chinese Atelier: http://localhost:{server.server_port}',flush=True)
    print(f'Teacher desk: http://localhost:{server.server_port}/teacher',flush=True)
    print('Teacher key: '+server.teacher_key,flush=True)
    print('Private local data: data/state.json. Keep this machine and exports private.',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nServer stopped.')
    finally: server.server_close()


if __name__=='__main__': main()
