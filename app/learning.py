"""Persistent microlearning and an explicitly documented SM-2-inspired review ladder."""
from datetime import datetime, timedelta, timezone, time as daytime
from zoneinfo import ZoneInfo
import copy
import re
import unicodedata
UTC=timezone.utc
STAGES=['discover','understand','build','communicate','apply']
THEMES=['Tourism','Hotel reception','Reservations','Food and beverage','Transportation','Attractions','Customer service','Complaints and problem-solving']
CORE=[['马上','等','您','请','办','落地签','护照','登机牌','方便'],['好久不见','来','想','还','离','都','酒店'],['办理','入住','一共','房卡','进来','行李'],['怎么','打车','叫','先……,然后……','左转','门票','收费'],['换','银行','没有','用','人民币','换钱','泰铢'],['附近','还是','从','分钟','骑','危险'],['热闹','夜市','好听','有趣','觉得','寺庙'],['爬山','累','开心','天气','冷','大衣'],['菜单','特色','尝','份','需要','账单','买单'],['号','小时','大概','点','出发','登机'],['真','吧','试','逛','舒服','旁边'],['衣服','件','售货员','合适','多少','新鲜'],['快','开始','变','已经','该','回'],['打算','时候','有空儿','一起','怎么样','日出'],['近','家','推荐','好吃','椰子汁','芒果汁'],['庆祝','浪漫','水灯','孔明灯','听说','最','飘'],['过','见面礼','鞠躬','合十','教','举'],['活动','打水仗','泼','湿','呢','带'],['表示','感谢','祝福','送','给','礼物','花篮'],['以前','发现','参观','现在','但是','佛殿','不要']]
def moment(value=None):
    if value is None:return datetime.now(UTC)
    if isinstance(value,str):value=datetime.fromisoformat(value.replace('Z','+00:00'))
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
def iso(value=None):return moment(value).isoformat()
def norm(value):return re.sub(r'[\s，。！？,.!?、；;：:]','',unicodedata.normalize('NFKC',str(value))).casefold()
def chinese_count(value):return len(re.findall(r'[\u3400-\u9fff]',value))
def local_day(value,zone='Asia/Bangkok'):return moment(value).astimezone(ZoneInfo(zone)).date()
def next_date(at,days,zone):
    local=moment(at).astimezone(ZoneInfo(zone))
    return datetime.combine(local.date()+timedelta(days=days),daytime(9),ZoneInfo(zone)).astimezone(UTC)
def build_path(curriculum):
    units=[]
    for l in curriculum['lessons']:
        n=l['number'];groups={s:[] for s in STAGES}
        for q in l['questions']:
            c=q.get('category',q['skill']);stage='discover' if c=='vocabulary' else 'build' if c=='grammar' else 'understand' if c=='comprehension' else 'communicate'
            groups[stage].append(q['id'])
        writing=next(t for t in l['tasks'] if t['id'].endswith('-writing'));role=next(t for t in l['tasks'] if t['type']=='roleplay');interpret=next(t for t in l['tasks'] if t['id'].endswith('-interpretation'))
        core=[v['id'] for v in l['vocabulary'] if v['chinese'] in CORE[n-1]]
        briefs=[('Recall the words that do the work','Retrieve useful expressions in context. The full vocabulary remains available.',8),('Read between the lines','Interpret the original dialogues and distinguish evidence from inference.',12),('Build a flexible response','Practise source patterns, then produce connected Chinese independently.',10),(role['title'],'Listen with a partner if available, negotiate a change and save a rehearsal reflection.',10),(writing['title'],'Create the source-based outcome, check formative answers and reflect.',15 if n<16 else 18)]
        steps=[]
        for i,(stage,(title,brief,minutes)) in enumerate(zip(STAGES,briefs),1):
            field=['vocabulary','readings','patterns','tasks','tasks'][i-1];refs=sorted({r for item in l[field] for r in item.get('sourceRefs',[])})
            steps.append({'id':f'{l["id"]}-step-{i}','lessonId':l['id'],'number':i,'position':(n-1)*5+i,'stage':stage,'title':title,'brief':brief,'minutes':minutes,'questionIds':groups[stage],'vocabularyIds':[v['id'] for v in l['vocabulary']] if i==1 else [],'coreVocabularyIds':core if i==1 else [],'readingIds':[r['id'] for r in l['readings']] if i==2 else [],'patternIds':[p['id'] for p in l['patterns']] if i==3 else [],'taskIds':[interpret['id']] if i==2 else [role['id']] if i==4 else [writing['id']] if i==5 else [],'sourceRefs':refs,'origin':'adaptation','approval':l['approval']})
        units.append({'id':l['id'],'number':n,'title':l['originalTitle'],'subtitle':l['subtitle'],'status':l['status'],'steps':steps})
    assert len(units)==20 and sum(len(u['steps']) for u in units)==100
    return {'schemaVersion':1,'origin':'adaptation','notice':'Microsteps and retrieval variants are editorial activities. Original source records remain separate; teacher approval is pending.','units':units}
def initialize(state):
    if 'learning' not in state:
        state['learning']={'version':2,'settings':{'dailyGoal':10,'weeklyGoal':4,'timeZone':'Asia/Bangkok'},'steps':{},'srs':{},'phrases':{},'reviewHistory':[],'xpLedger':{},'daily':{},'sessions':{},'pending':{},'work':{},'recommendations':{}}
        for lid,p in state.get('progress',{}).items():
            if p.get('completed') and lid.startswith('zt-'):
                for i in range(1,6):state['learning']['steps'][f'{lid}-step-{i}']={'completed':True,'completedAt':p.get('updatedAt'),'migration':'legacy_completed_unit','reflection':p.get('reflection','')}
        for iid,r in state.get('reviews',{}).items():
            state['learning']['srs'][iid]={'itemId':iid,'lessonId':r['lessonId'],'firstLearnedAt':None,'legacyFirstDateUnknown':True,'lastReviewedAt':r.get('updatedAt'),'nextReviewAt':r['dueAt'],'successfulReviews':max(0,r.get('repetitions',0)-r.get('lapses',0)),'failedReviews':r.get('lapses',0),'interval':r.get('interval',0),'easeFactor':2.5,'ladder':min(r.get('repetitions',0),5),'mastery':'learning','lastRating':r.get('lastRating'),'revision':0}
    return state['learning']
def catalog(curriculum,learning):
    items={}
    for l in curriculum['lessons']+curriculum['supplementary']:
        for field,kind in [('vocabulary','vocabulary'),('patterns','grammar'),('questions','question'),('tasks','communication')]:
            for d in l[field]:
                k='expression' if field=='vocabulary' and len(d['chinese'])>2 else 'reading' if d.get('category')=='comprehension' else kind
                items[d['id']]={'id':d['id'],'kind':k,'lessonId':l['id'],'lessonTitle':l['title'],'label':d.get('chinese',d.get('title',d.get('prompt',''))),'data':d,'sourceRefs':d.get('sourceRefs',[]),'origin':d.get('origin','adaptation')}
    for p in learning['phrases'].values():
        if p.get('targetId') in items:continue
        items[p['id']]={'id':p['id'],'kind':'personal','label':p['chinese'],'data':p,'lessonId':None,'lessonTitle':'Personal phrasebook','sourceRefs':[],'origin':'personal_unverified'}
    return items
def enroll(learning,item,at=None,due_now=False):
    if item['id'] not in learning['srs']:
        at=moment(at);due=at if due_now else next_date(at,1,learning['settings']['timeZone'])
        learning['srs'][item['id']]={'itemId':item['id'],'lessonId':item.get('lessonId'),'firstLearnedAt':iso(at),'lastReviewedAt':None,'nextReviewAt':iso(due),'successfulReviews':0,'failedReviews':0,'interval':0,'easeFactor':2.5,'ladder':0 if due_now else 1,'mastery':'new','revision':0}
    return learning['srs'][item['id']]
def schedule(record,rating,zone='Asia/Bangkok',at=None):
    if rating not in {'again','hard','good','easy'}:raise ValueError('Choose Again, Hard, Good or Easy.')
    at=moment(at);r=copy.deepcopy(record);ease=r.get('easeFactor',2.5);index=r.get('ladder',0);old=r.get('interval',0)
    if rating=='again':
        interval=0;due=at+timedelta(minutes=10);ease=max(1.3,ease-.2);index=0;r['failedReviews']+=1
    elif rating=='hard':
        interval=max(1,round(max(old,1)*.6));due=next_date(at,interval,zone);ease=max(1.3,ease-.15);r['successfulReviews']+=1
    else:
        ladder=[1,2,4,7,16];base=ladder[index] if index<len(ladder) else max(1,old)*ease
        interval=max(1,round(base*ease/2.5)) if index<len(ladder) else round(base)
        if rating=='easy':interval=max(3,round(max(interval,old)*1.6));ease=min(3.2,ease+.15)
        interval=min(365,interval);due=next_date(at,interval,zone);index+=1;r['successfulReviews']+=1
    r.update({'lastReviewedAt':iso(at),'nextReviewAt':iso(due),'interval':interval,'easeFactor':round(ease,2),'ladder':index,'lastRating':rating,'revision':r.get('revision',0)+1})
    r['mastery']='relearning' if rating=='again' else 'mastered' if r['successfulReviews']>=5 and interval>=30 else 'reviewing' if r['successfulReviews']>=2 else 'learning'
    return r
def award(learning,key,xp,kind,at=None):
    if key in learning['xpLedger']:return 0
    at=moment(at);day=str(local_day(at,learning['settings']['timeZone']));learning['xpLedger'][key]={'xp':xp,'kind':kind,'at':iso(at),'day':day}
    learning['daily'].setdefault(day,{'activeSeconds':0,'events':[]})['events'].append({'kind':kind,'at':iso(at),'xp':xp})
    return xp
def path_state(curriculum,state):
    learning=initialize(state);path=build_path(curriculum);opened=True
    for u in path['units']:
        for s in u['steps']:
            r=learning['steps'].get(s['id'],{});done=r.get('completed',False);ids=s['coreVocabularyIds']+s['patternIds']+s['questionIds']+s['taskIds'];mastered=bool(ids) and all(learning['srs'].get(i,{}).get('mastery')=='mastered' for i in ids)
            s['state']='mastered' if done and mastered else 'completed' if done else 'in_progress' if opened and r else 'available' if opened else 'locked';s['record']=r
            if not done:opened=False
        u['completed']=all(s['state'] in {'completed','mastered'} for s in u['steps'])
    return path
def review_counts(learning,items,at=None):
    at=moment(at);today=local_day(at,learning['settings']['timeZone']);c=dict(due=0,overdue=0,upcoming=0,mastered=0,needsPractice=0,total=0)
    for iid,r in learning['srs'].items():
        if iid not in items:continue
        c['total']+=1
        if moment(r['nextReviewAt'])<=at:
            c['due']+=1;c['overdue']+=local_day(r['nextReviewAt'],learning['settings']['timeZone'])<today
        else:c['upcoming']+=1
        c['mastered']+=r['mastery']=='mastered';c['needsPractice']+=r['failedReviews']>=2 or r['mastery']=='relearning'
    return c
def queue(learning,items,mode='due',at=None):
    at=moment(at);rows=[]
    for iid,r in learning['srs'].items():
        if iid not in items:continue
        due=moment(r['nextReviewAt'])<=at
        if mode=='due' and not due:continue
        if mode=='overdue' and (not due or local_day(r['nextReviewAt'],learning['settings']['timeZone'])>=local_day(at,learning['settings']['timeZone'])):continue
        if mode=='upcoming' and due:continue
        if mode=='mastered' and r['mastery']!='mastered':continue
        if mode=='support' and r['failedReviews']<2 and r['mastery']!='relearning':continue
        item=items[iid];rows.append({'id':iid,'label':item['label'],'kind':item['kind'],'lessonTitle':item['lessonTitle'],'sourceRefs':item['sourceRefs'],'record':r,'recommendation':learning['recommendations'].get(iid)})
    rows.sort(key=lambda x:(not bool(x['recommendation'] and x['recommendation'].get('active',True)),moment(x['record']['nextReviewAt']),-x['record']['failedReviews']))
    return rows
def challenge_catalog(curriculum):
    definitions=[
      ('welcome','A welcome with a question','A guest arrives before the room is ready. In 50–100 Chinese characters, welcome them, ask one useful question and explain that you will check readiness before making a promise.',3),
      ('checkout','A clear check-out','A guest queries a charge at check-out. You have not verified it. Write 50–100 Chinese characters acknowledging the query, clarifying which charge and explaining the next check. Do not invent a refund policy.',3),
      ('reservation','A reservation enquiry','A guest asks for a room next weekend without dates or a guest count. Write 50–100 Chinese characters asking for missing details. Availability needs confirmation.',14),
      ('facilities','Explain before promising','A guest asks about an accessible route to a hotel facility. Location and accessibility are unconfirmed. Write 50–100 Chinese characters clarifying the need and explaining who will verify the route.',4),
      ('destination','A recommendation with choice','A visitor wants a quieter activity. Write 50–100 Chinese characters eliciting interests and explaining how you would compare options. Use 我觉得 carefully; do not invent current hours.',7),
      ('dining','Ask the kitchen','A guest asks whether a dish contains an ingredient. You do not know. Write 50–100 Chinese characters confirming the question, asking the kitchen and arranging follow-up. Do not guarantee food safety.',9),
      ('transfer','Before the airport transfer','A guest confuses hotel departure with boarding. Write 50–100 Chinese characters clarifying the two events and asking to confirm actual flight details.',10),
      ('complaint','Listen, clarify, act','A guest says the room is noisy and a previous request went unanswered. Write 80–140 Chinese characters acknowledging both concerns, asking a question and agreeing a check-back. Room changes and compensation are unconfirmed.',15),
      ('unexpected','A changed plan','An outdoor activity is no longer suitable. Write 80–140 Chinese characters clarifying priorities and offering to verify an alternative. Use a comparison and preserve choice.',20)]
    return [{'id':'hospitality-'+id,'title':title,'prompt':prompt,'level':'Foundation' if i<3 else 'Developing' if i<7 else 'Extended','suggestedAfter':n,'sourceRefs':curriculum['lessons'][n-1]['patterns'][0]['sourceRefs'],'foundationLessonId':curriculum['lessons'][n-1]['id'],'origin':'supplementary','minCharacters':50 if i<7 else 80,'criteria':['accuracy','communication','audience'],'successCriteria':['Address the actual concern.','Use connected, accurate Chinese and a courteous register.','Separate confirmed facts from a proposed next check.'],'extension':'Rehearse with a partner who changes one requirement. No audio is captured.'} for i,(id,title,prompt,n) in enumerate(definitions)]
def dashboard(curriculum,state,at=None):
    at=moment(at);l=initialize(state);path=path_state(curriculum,state);items=catalog(curriculum,l);settings=l['settings'];today=local_day(at,settings['timeZone']);weekstart=today-timedelta(days=today.weekday());days=[]
    for i in range(7):
        d=weekstart+timedelta(days=i);r=l['daily'].get(str(d),{});days.append({'date':str(d),'label':d.strftime('%a'),'activeSeconds':r.get('activeSeconds',0),'events':len(r.get('events',[])),'xp':sum(e['xp'] for e in r.get('events',[])),'today':d==today,'future':d>today})
    streak=0;cursor=today if l['daily'].get(str(today),{}).get('events') else today-timedelta(days=1)
    while l['daily'].get(str(cursor),{}).get('events'):streak+=1;cursor-=timedelta(days=1)
    complete=sum(s['state'] in {'completed','mastered'} for u in path['units'] for s in u['steps']);units=sum(u['completed'] for u in path['units']);counts=review_counts(l,items,at);xp=sum(e['xp'] for e in l['xpLedger'].values());reviewed=[r for r in l['reviewHistory'] if local_day(r['at'],settings['timeZone'])==today and not r.get('practiceOnly')]
    nextstep=next((dict(s,unitTitle=u['title'],unitNumber=u['number']) for u in path['units'] for s in u['steps'] if s['state'] in {'available','in_progress'}),None)
    badges=[{'id':'first-steps','title':'First departure','earned':complete>=1,'detail':'Complete your first step'},*({'id':f'steps-{n}','title':f'{n} steps, new horizons','earned':complete>=n,'detail':f'Complete {n} steps'} for n in [5,20,50,100]),{'id':'steady','title':'A little, often','earned':streak>=3,'detail':'Learn on 3 consecutive days'},{'id':'mastery','title':'Words within reach','earned':counts['mastered']>=10,'detail':'10 items with a 30+ day retrieval interval'},{'id':'host','title':'A thoughtful host','earned':sum(w.get('submitted',False) for w in l['work'].values() if w.get('kind')=='challenge')>=3,'detail':'Submit 3 communication challenges'}]
    all_challenges=challenge_catalog(curriculum)
    eligible=[c for c in all_challenges if c['suggestedAfter']<=max(3,(nextstep or {'unitNumber':20})['unitNumber'])]
    choices=l.setdefault('dailyChallenges',{});key=str(today)
    if key not in choices:choices[key]=eligible[today.toordinal()%len(eligible)]['id']
    challenge=next(c for c in all_challenges if c['id']==choices[key])
    active=l['daily'].get(str(today),{}).get('activeSeconds',0);limit=4 if counts['overdue']>=8 or settings['dailyGoal']==10 else 6
    return {'date':str(today),'settings':settings,'path':path,'completedSteps':complete,'completedUnits':units,'xp':xp,'streak':streak,'week':days,'weeklyActiveDays':sum(d['events']>0 for d in days),'activeSeconds':active,'goalComplete':active>=settings['dailyGoal']*60,'reviewCounts':counts,'reviewLimit':limit,'reviewedToday':len(reviewed),'nextStep':nextstep,'reviewFirst':counts['overdue']>=8,'shortSession':{'minutes':3,'items':min(3,counts['due'])},'badges':badges,'dailyChallenge':challenge,'challengeDone':bool(l['work'].get(f'{today}:{challenge["id"]}',{}).get('submitted')),'reminders':[{'title':f'{counts["overdue"]} overdue retrievals' if counts['overdue'] else f'{counts["due"]} items ready','body':'A few thoughtful recalls are enough to restart. Your progress is safe.' if counts['overdue'] else 'Your review schedule lives on this device.'}]+[{'title':'Teacher recommendation','body':v['note']} for v in l['recommendations'].values() if v.get('active',True)]}
def review_prompt(item,record):
    d=item['data'];kind=item['kind'];turn=record.get('successfulReviews',0)+record.get('failedReviews',0);p={'itemId':item['id'],'kind':kind,'lessonTitle':item['lessonTitle'],'sourceRefs':item['sourceRefs'],'origin':'supplementary','label':item['label']}
    if kind in {'vocabulary','expression','personal'}:
        word=d['chinese'];meaning=d.get('meaning',d.get('english',''));example=d.get('example','');variant=turn%3
        if variant==0:p.update(format='Chinese → English recall',cue=f'Explain “{word}” in English, then recall a useful context.',check='self',expected=meaning,explanation=example or 'Compare your meaning and context. Personal phrases are not teacher-verified.',minimum=2)
        elif variant==1:p.update(format='English → Chinese production',cue=f'Produce the saved expression for: {meaning}',check='exact',expected=word,explanation=example or 'Exact saved-expression retrieval. Valid alternatives can be discussed with your teacher.',minimum=1)
        elif word in example:p.update(format='Sentence completion',cue=example.replace(word,'____')+' (Use the saved expression.)',check='exact',expected=word,explanation=example,minimum=1)
        else:p.update(format='Contextual production',cue=f'Use “{word}” in a connected Chinese response.',check='self',expected=example or word,explanation='Check meaning, word order and the intended audience.',minimum=10)
    elif kind in {'question','reading'}:
        p.update(format='Reading retrieval' if kind=='reading' else 'Contextual question',cue=d['prompt'],check='choice' if d['type']=='choice' else 'exact',expected=d.get('answer',d.get('acceptedAnswers',[None])[0]),accepted=d.get('acceptedAnswers',[]),explanation=d['explanation'],minimum=1)
        if d['type']=='choice':
            options=copy.deepcopy(d['options']);shift=turn%len(options);p['options']=options[shift:]+options[:shift]
    elif kind=='grammar':
        sentence=d['examples'][0]
        if turn%2==0:
            tokens=re.findall(r'[A-Za-z0-9]+|[^\s]',sentence);chunks=[''.join(tokens[i:i+2]) for i in range(0,len(tokens),2)]
            p.update(format='Sentence reconstruction',cue='Reconstruct this '+('source-linked ' if item['sourceRefs'] else '')+'example from character pairs. These are recall scaffolds, not word boundaries. Other valid sentences may exist.',check='exact',expected=sentence,explanation=d['explanation']+(' '+d['pitfall'] if d.get('pitfall') else ''),tokens=chunks[1::2]+chunks[::2],minimum=1)
        else:p.update(format='Pattern production',cue=d.get('application','Use this pattern in a connected response appropriate to its original scenario.')+' Target: '+d['title'],check='self',expected=' / '.join(d['examples']),explanation=d['explanation']+(' '+d['pitfall'] if d.get('pitfall') else ''),minimum=15)
    else:p.update(format='Dialogue / situation response',cue=d['prompt'],check='self',expected=d['model'],explanation='Compare the task criteria; this is self-assessed retrieval, not a teacher score.',criteria=d.get('successCriteria',d.get('criteria',[])),minimum=min(d.get('minCharacters',50),50))
    return p
def public_prompt(prompt):return {k:v for k,v in prompt.items() if k not in {'expected','accepted','explanation','check'}}
