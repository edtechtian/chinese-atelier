"""Endpoints for the daily learning layer; original lesson APIs remain supported."""
from urllib.parse import urlsplit,parse_qs
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
import copy
import secrets
from datetime import timedelta, datetime, time as daytime
from . import learning as L
class LearningError(Exception):
    def __init__(self,status,message):self.status=status;self.message=message

def require(test,message,status=400):
    if not test:raise LearningError(status,message)
def public_state(state):
    s=copy.deepcopy(state)
    if 'learning' in s:s['learning'].pop('sessions',None);s['learning'].pop('pending',None);s['learning'].pop('clockLastAt',None)
    return s

def activity(h,title,lid=None):h.event(title,lid)
def context(h):
    l=L.initialize(h.store.state);return l,L.catalog(h.store.curriculum,l)
def step(h,sid):
    return next((s for u in L.path_state(h.store.curriculum,h.store.state)['units'] for s in u['steps'] if s['id']==sid),None)
def analytics(h):
    l,items=context(h);d=L.dashboard(h.store.curriculum,h.store.state);history=l['reviewHistory'];scored=[r for r in history if not r.get('practiceOnly')];good=[r for r in scored if r['rating']!='again'];known=[r for r in scored if r.get('objectiveCorrect') is not None]
    return {'dashboard':d,'reviewAttempts':len(scored),'reviewSuccessRate':round(len(good)/len(scored)*100) if scored else None,'objectiveSuccessRate':round(sum(r['objectiveCorrect'] for r in known)/len(known)*100) if known else None,'selfRated':len(scored)-len(known),'retention':{k:sum(r['mastery']==k for r in l['srs'].values()) for k in ['new','learning','reviewing','relearning','mastered']},'support':L.queue(l,items,'support')[:20],'work':sorted(l['work'].values(),key=lambda r:r['updatedAt'],reverse=True),'reviews':scored[-30:][::-1],'recommendations':l['recommendations'],'items':L.queue(l,items,'all'),'grammarErrors':[dict(id=i,label=items[i]['label'],failures=r['failedReviews'],nextReviewAt=r['nextReviewAt']) for i,r in l['srs'].items() if i in items and (items[i]['kind']=='grammar' or items[i]['data'].get('category')=='grammar') and r['failedReviews']]}

def get(h,path):
    if path not in {'/api/learning','/api/learning/reviews','/api/learning/phrases','/api/learning/challenges','/api/teacher/learning'}:return False
    l,items=context(h);query=parse_qs(urlsplit(h.path).query)
    if path=='/api/learning':
        result=L.dashboard(h.store.curriculum,h.store.state);h.store.save_state();h.send(result)
    elif path=='/api/learning/reviews':
        mode=query.get('mode',['due'])[0];require(mode in {'due','overdue','upcoming','mastered','support','all'},'Unknown review view.')
        rows=L.queue(l,items,mode);h.send({'counts':L.review_counts(l,items),'items':rows[:100],'total':len(rows),'limit':L.dashboard(h.store.curriculum,h.store.state)['reviewLimit']})
    elif path=='/api/learning/phrases':h.send({'themes':L.THEMES,'items':list(l['phrases'].values())})
    elif path=='/api/learning/challenges':h.send({'items':L.challenge_catalog(h.store.curriculum),'work':l['work']})
    else:h.require_teacher();h.send(analytics(h))
    return True

def post(h,path,b):
    if not path.startswith('/api/learning/') and path not in {'/api/teacher/learning/recommend','/api/teacher/learning/assessment'}:return False
    l,items=context(h);at=L.moment();day=str(L.local_day(at,l['settings']['timeZone']));out={}
    if path=='/api/learning/settings':
        goal=b.get('dailyGoal',l['settings']['dailyGoal']);weekly=b.get('weeklyGoal',l['settings']['weeklyGoal']);zone=b.get('timeZone',l['settings']['timeZone'])
        require(type(goal)==int and goal in {10,15},'Choose a 10- or 15-minute daily goal.');require(type(weekly)==int and weekly in range(1,8),'Choose 1–7 learning days each week.')
        try:ZoneInfo(zone)
        except (ValueError,TypeError,ZoneInfoNotFoundError):raise LearningError(400,'Use a valid IANA time zone, such as Asia/Bangkok.')
        l['settings']={'dailyGoal':goal,'weeklyGoal':weekly,'timeZone':zone};out=l['settings']
    elif path=='/api/learning/session':
        sid=b.get('sessionId');sessions=l['sessions']
        if sid:
            require(sid in sessions,'Study session expired. Reopen the activity.',409)
            s=sessions[sid];last=L.moment(s['lastAt']);elapsed=(at-last).total_seconds();credited=0
            if 0<elapsed<=90 and b.get('active') is True:
                begin=max(last,at-timedelta(seconds=30),L.moment(l.get('clockLastAt',s['lastAt'])))
                cursor=begin
                while cursor<at:
                    current=L.local_day(cursor,l['settings']['timeZone'])
                    midnight=datetime.combine(current+timedelta(days=1),daytime(0),ZoneInfo(l['settings']['timeZone'])).astimezone(L.UTC)
                    end=min(at,midnight);seconds=max(0,int((end-cursor).total_seconds()))
                    l['daily'].setdefault(str(current),{'activeSeconds':0,'events':[]})['activeSeconds']+=seconds
                    credited+=seconds;cursor=end
                l['clockLastAt']=L.iso(at)
            s['lastAt']=L.iso(at)
            out={'sessionId':sid,'creditedSeconds':credited,'activeSeconds':l['daily'].get(day,{}).get('activeSeconds',0)}
        else:
            require(b.get('kind') in {'step','review','challenge','visual'},'Open a learning activity to start time tracking.')
            sid=secrets.token_urlsafe(18);sessions[sid]={'startedAt':L.iso(at),'lastAt':L.iso(at),'kind':b['kind']};out={'sessionId':sid,'creditedSeconds':0}
            # Keep recent sessions; elapsed time is never supplied by the client.
            for old in list(sessions)[:-20]:sessions.pop(old)
    elif path=='/api/learning/step':
        s=step(h,b.get('stepId'));require(s is not None,'Learning step not found.',404);require(s['state']!='locked','Complete the preceding step first. Reviews and source materials remain available.',409)
        r=copy.deepcopy(l['steps'].get(s['id'],{}));r.setdefault('startedAt',L.iso(at));lesson=h.get_lesson(s['lessonId']);require(lesson['status'] in {'available','published'},'This source lesson needs teacher preparation before learning.',409);r['updatedAt']=L.iso(at)
        if 'text' in b:
            text=b['text'];require(isinstance(text,str) and len(text)<=4000,'Use text up to 4,000 characters.');r['text']=text
        if b.get('complete'):
            require(b.get('acknowledge') is True,'Confirm that you studied the source context before completing.')
            attempts={a['questionId']:a for a in h.store.state['attempts']}
            require(all(attempts.get(q,{}).get('correct') for q in s['questionIds']),'Try each short check and use its feedback to reach a correct response.',409)
            if s['stage']=='discover':require(all(l['srs'].get(i,{}).get('lastReviewedAt') for i in s['coreVocabularyIds']),'Recall each core expression and rate your retrieval first.',409)
            if s['stage']=='build':require(L.chinese_count(r.get('text',''))>=20,'Save at least 20 Chinese characters using a target pattern.',409)
            for tid in s['taskIds']:
                task=next(t for t in lesson['tasks'] if t['id']==tid);work=h.store.state['responses'].get(tid,{})
                require(work.get('submitted') and L.chinese_count(work.get('text',''))>=task['minCharacters'],f'Submit your response to “{task["title"]}” (guidance: {task["minCharacters"]}+ Chinese characters).',409)
            if s['stage']=='apply':
                require(L.chinese_count(r.get('text',''))>=10,'Save a short Chinese reflection (10+ characters).',409)
                require(all(attempts.get(q['id'],{}).get('correct') for q in lesson['questions']),'Revisit the formative checks that still need correction.',409)
            first=not r.get('completed');r.update(completed=True,completedAt=r.get('completedAt',L.iso(at)));out['xpEarned']=L.award(l,'step:'+s['id'],25,'step',at) if first else 0
            for iid in s['patternIds']+s['taskIds']:L.enroll(l,items[iid],at)
            if s['stage']=='apply':
                p=h.progress(lesson['id']);p.update(completed=True,reflection=r['text'],updatedAt=L.iso(at))
            if first:activity(h,'Completed '+s['stage'].upper()+' · '+lesson['title'],lesson['id'])
        l['steps'][s['id']]=r;h.progress(lesson['id']);out.update(record=r,stepId=s['id'],completedUnits=sum(u['completed'] for u in L.path_state(h.store.curriculum,h.store.state)['units']))
    elif path=='/api/learning/phrases':
        theme=b.get('theme','Tourism');require(theme in L.THEMES,'Choose a phrasebook theme.')
        pid=b.get('phraseId')
        if pid:
            require(pid in l['phrases'],'Saved phrase not found.',404);l['phrases'][pid]['theme']=theme;h.store.save_state();h.send(l['phrases'][pid]);return True
        target=b.get('itemId');existing=next((p for p in l['phrases'].values() if target and p.get('targetId')==target),None)
        if existing:out=existing
        else:
            if target:
                require(target in items,'Source item not found.',404);item=items[target];d=item['data'];chinese=d.get('chinese',(d.get('examples') or [d.get('title','')])[0]);english=d.get('meaning',d.get('explanation',''));refs=item['sourceRefs'];origin=item['origin']
            else:
                chinese=b.get('chinese','');english=b.get('english','');require(isinstance(chinese,str) and 0<L.chinese_count(chinese) and len(chinese)<=600,'Enter a Chinese phrase up to 600 characters.');require(isinstance(english,str) and 0<len(english.strip())<=2000,'Add a meaning or usage note, up to 2,000 characters.');refs=[];origin='personal_unverified'
            pid='phrase-'+secrets.token_hex(8);p={'id':pid,'targetId':target,'chinese':chinese,'english':english,'theme':theme,'sourceRefs':refs,'origin':origin,'createdAt':L.iso(at)};l['phrases'][pid]=p
            newitems=L.catalog(h.store.curriculum,l);L.enroll(l,newitems[target or pid],at,due_now=True);out=p
    elif path=='/api/learning/review/start':
        iid=b.get('itemId')
        if not iid:
            due=L.queue(l,items);require(bool(due),'No due reviews. Your existing work is safe.',409);iid=due[0]['id']
        require(iid in items,'Review item not found.',404);item=items[iid]
        if item.get('lessonId'):
            require(h.get_lesson(item['lessonId'])['status'] in {'available','published'},'This item needs teacher preparation.',409)
        record=copy.deepcopy(l['srs'].get(iid,{'successfulReviews':0,'failedReviews':0,'revision':0}));prompt=L.review_prompt(item,record);token=secrets.token_urlsafe(24)
        if not hasattr(h.server,'learning_pending'):h.server.learning_pending={}
        pending=h.server.learning_pending
        for key in list(pending):
            if (at-L.moment(pending[key]['startedAt'])).total_seconds()>7200:pending.pop(key)
        require(len(pending)<200,'Too many open retrievals. Finish one or restart the app.',409)
        pending[token]={'itemId':iid,'prompt':prompt,'startedAt':L.iso(at),'revision':record.get('revision',0),'answered':False,'wasDue':iid not in l['srs'] or L.moment(l['srs'][iid]['nextReviewAt'])<=at}
        out=dict(L.public_prompt(prompt),token=token,practiceOnly=not pending[token]['wasDue'])
    elif path in {'/api/learning/review/answer','/api/learning/review/rate'}:
        pending=getattr(h.server,'learning_pending',{});p=pending.get(b.get('token'));require(p is not None,'This retrieval expired or was already saved. Start another item.',409);iid=p['itemId'];require(iid in items,'The content changed. Reopen review.',409);prompt=p['prompt']
        if path.endswith('/answer'):
            answer=b.get('answer','');require(isinstance(answer,str) and 0<len(answer.strip())<=12000,'Enter your own recall response before revealing feedback.')
            if prompt['format'] in {'Pattern production','Contextual production','Dialogue / situation response'}:require(L.chinese_count(answer)>=prompt['minimum'],f'Write at least {prompt["minimum"]} Chinese characters for this recall.')
            correct=None if prompt['check']=='self' else answer==prompt['expected'] if prompt['check']=='choice' else L.norm(answer) in {L.norm(a) for a in prompt.get('accepted',[]) or [prompt['expected']]}
            p.update(answered=True,answer=answer,objectiveCorrect=correct);out={'correct':correct,'expected':next((o['text'] for o in prompt.get('options',[]) if o['id']==prompt['expected']),prompt['expected']),'explanation':prompt['explanation'],'selfAssessed':correct is None,'criteria':prompt.get('criteria',[]),'notice':'Self-compare meaning and usage. This is not an automated language-quality or teacher score.' if correct is None else 'Exact source-expression practice. Discuss valid alternatives with your teacher.'}
        else:
            require(p['answered'],'Attempt recall before choosing a rating.',409);rating=b.get('rating');require(rating in {'again','hard','good','easy'},'Choose Again, Hard, Good or Easy.');require(not(p['objectiveCorrect'] is False and rating!='again'),'This exact recall needs another attempt. Choose Again and use the explanation.')
            old=l['srs'].get(iid);require(old is None or old.get('revision',0)==p['revision'],'This item was reviewed in another window. Reopen it.',409)
            record=L.enroll(l,items[iid],at,due_now=old is None);xp=0
            if p['wasDue']:
                record=L.schedule(record,rating,l['settings']['timeZone'],at);l['srs'][iid]=record;xp=L.award(l,'review:'+iid+':'+str(record['revision']),3,'review',at)
                if iid in l['recommendations']:l['recommendations'][iid]['active']=False
            event={'itemId':iid,'label':items[iid]['label'],'kind':items[iid]['kind'],'answer':p['answer'],'rating':rating,'objectiveCorrect':p['objectiveCorrect'],'practiceOnly':not p['wasDue'],'at':L.iso(at),'sourceRefs':items[iid]['sourceRefs']};L.award(l,'practice:'+day+':'+iid,0,'practice',at) if not p['wasDue'] else None;l['reviewHistory'].append(event);l['reviewHistory']=l['reviewHistory'][-10000:];pending.pop(b['token'])
            if items[iid]['kind'] in {'vocabulary','expression'}:
                h.store.state['reviews'][iid]={'vocabularyId':iid,'lessonId':items[iid]['lessonId'],'interval':record['interval'],'repetitions':record['successfulReviews']+record['failedReviews'],'lapses':record['failedReviews'],'dueAt':record['nextReviewAt'],'lastRating':rating,'updatedAt':L.iso(at)}
            out={'record':record,'xpEarned':xp,'practiceOnly':not p['wasDue'],'notice':'Early practice: schedule and XP unchanged.' if not p['wasDue'] else 'Recall saved. Your next review date has changed.'}
    elif path=='/api/learning/work':
        kind=b.get('kind');require(kind in {'challenge','build'},'Unknown learning task.');id=b.get('id');text=b.get('text','');require(isinstance(text,str) and len(text)<=12000,'Use text up to 12,000 characters.');submitted=b.get('submit') is True
        if kind=='challenge':
            task=next((c for c in L.challenge_catalog(h.store.curriculum) if c['id']==id),None);require(task is not None,'Challenge not found.',404);key=day+':'+id;minimum=task['minCharacters'];title=task['title']
        else:
            s=step(h,id);require(s is not None and s['stage']=='build','Build step not found.',404);require(s['state']!='locked','Open the preceding step first.',409);key=id;minimum=20;title=s['title']
        require(not submitted or L.chinese_count(text)>=minimum,f'Write at least {minimum} Chinese characters before submission.')
        old=l['work'].get(key,{});changed=old.get('text')!=text;review=old.get('teacherReview');history=old.get('reviewHistory',[])
        if changed and review:history=(history+[review])[-10:];review=None
        r={'id':key,'taskId':id,'kind':kind,'title':title,'text':text,'revision':old.get('revision',0)+int(changed),'submitted':submitted or (old.get('submitted',False) and not changed),'updatedAt':L.iso(at),'teacherReview':review,'reviewHistory':history,'criteria':['accuracy','communication','audience'] if kind=='challenge' else ['accuracy','organization']};l['work'][key]=r
        if kind=='build':l['steps'].setdefault(id,{})['text']=text
        xp=L.award(l,'daily-challenge:'+day,12,'challenge',at) if submitted and kind=='challenge' else 0
        if submitted:activity(h,'Submitted '+title)
        out={'work':r,'xpEarned':xp,'notice':'Saved locally. Character count is not a language-quality score; teacher review is available.'}
    elif path=='/api/teacher/learning/recommend':
        h.require_teacher();iid=b.get('itemId');note=b.get('note','');require(iid in items,'Select an existing learning item.',404);require(isinstance(note,str) and 0<len(note.strip())<=2000,'Add a specific recommendation up to 2,000 characters.');r=L.enroll(l,items[iid],at,due_now=True);r['nextReviewAt']=L.iso(at);r['revision']=r.get('revision',0)+1;l['recommendations'][iid]={'note':note,'at':L.iso(at),'active':True};out={'ok':True}
    elif path=='/api/teacher/learning/assessment':
        h.require_teacher();r=l['work'].get(b.get('responseId'));require(r and r['submitted'],'Select a submitted learning response.',409);require(b.get('revision')==r['revision'],'The learner revised this work. Reload before reviewing.',409);scores=b.get('scores',{});require(isinstance(scores,dict) and set(scores)==set(r['criteria']) and all(type(v)==int and 1<=v<=4 for v in scores.values()),'Use levels 1–4 for exactly the selected criteria.');comment=b.get('comment','');require(isinstance(comment,str) and 0<len(comment.strip())<=6000,'Add evidence and a practical next step.');r['teacherReview']={'scores':scores,'comment':comment,'at':L.iso(at),'revision':r['revision'],'kind':'teacher_verified','officialGrade':False};out=r
    else:raise LearningError(404,'Learning endpoint not found.')
    h.store.save_state();h.send(out);return True
