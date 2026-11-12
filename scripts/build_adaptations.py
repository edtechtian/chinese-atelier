"""Build reviewed editorial course units without altering original-source audit data."""
from pathlib import Path
import json, sys, re, hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.schema import validate_curriculum

def refs(n,*ss): return [f'zt-{n:02d}-slide-{s:03d}' for s in ss]
def q(n,key,prompt,options,explanation,slides,skill='comprehension',layer='understand',answers=None,category=None):
    v={'id':f'zt-{n:02d}-q-{key}','type':'text' if answers else 'choice','prompt':prompt,'explanation':explanation,'sourceRefs':refs(n,*slides),'origin':'supplementary','skill':skill,'layer':layer,'category':category or skill}
    if answers:v['acceptedAnswers']=answers
    else:
        # Correct answer is authored first; deterministic rotation avoids position cues.
        indexed=list(enumerate(options)); shift=sum(ord(c) for c in key)%len(options); indexed=indexed[shift:]+indexed[:shift]
        v['options']=[{'id':f'o{j+1}','text':x} for j,(i,x) in enumerate(indexed)]; v['answer']=next(f'o{j+1}' for j,(i,x) in enumerate(indexed) if i==0)
    return v

def task(n,key,title,prompt,model,slides,kind='writing',minimum=180,checks=(),scaffold=(),challenge='',criteria=None):
    return {'id':f'zt-{n:02d}-{key}','title':title,'prompt':prompt,'model':model,'modelOrigin':'supplementary','origin':'supplementary','sourceRefs':refs(n,*slides),'type':kind,'minCharacters':minimum,'criteria':criteria or ['comprehension','accuracy','communication','organization','audience'],'successCriteria':list(checks),'scaffold':list(scaffold),'challenge':challenge,'assessmentMode':'teacher_criterion_review'}

def prototype():
    n=3
    return {
    'id':'zt-03','subtitle':'Arrival, clarity & consent','minutes':65,
    'objectives':['Interpret the three source dialogues and distinguish a total from a per-room price.','Use 到 + place + 了, 一共 and 可以…吗 in connected Chinese.','Repair a check-in misunderstanding and respond appropriately when permission is declined.','Write a guest message and an internal handover for different audiences.'],
    'goals':['Use evidence to separate confirmed details from assumptions.','Clarify a total and request permission in a live exchange.','Communicate clearly with a guest and a colleague.'],
    'hospitality':'Reception and luggage delivery: clear totals, courteous requests and the guest’s control over access to the room.',
    'pedagogy':{
      'profile':'Start with the Chinese dialogues without pinyin. Move quickly from fluent reading to inference, spoken repair and register; spoken spontaneity is assessed separately.',
      'diagnostic':'Read slide 9 once, explain what 3,000泰铢 covers, then answer aloud when a guest asks “是每个房间三千吗？” Open the scaffold if formulating the reply is difficult.',
      'sequence':[{'stage':'Understand','minutes':20,'activity':'Read three exchanges, retrieve words in context and interpret totals.'},{'stage':'Communicate','minutes':20,'activity':'Practise arrival and permission; exchange roles and handle a changed constraint.'},{'stage':'Apply professionally','minutes':25,'activity':'Write for guest and colleague; revise against task criteria.'}],
      'decisions':[{'action':'retain','content':'All three dialogues, original vocabulary, arrival grammar and the source total.','sourceRefs':refs(3,3,5,6,9,10,11,12)},{'action':'extend','content':'Interpret missing booking details, repair a misunderstanding and differentiate guest/colleague audiences.','sourceRefs':refs(3,9,11)},{'action':'scaffold','content':'Optional pinyin/Thai, role cards, a sequence map and sentence openings.','sourceRefs':refs(3,3,6,10,12)},{'action':'interactive','content':'Contextual word retrieval, total interpretation, bounded pattern practice and service choices.','sourceRefs':refs(3,5,7,9,11,12)}],
      'multilingual':'Optional: compare request strategies in Thai or German, then explain why a literal translation might sound too direct in Chinese. No full trilingual translation is needed.',
      'reflection':'Can I clarify a total and ask permission before acting? Quote one phrase I improved.'},
    'readingSlides':[5,9,11],
    'readingPrompts':{
      '5':[{'prompt':'Quote the phrases that signal arrival, appreciation and intention. How do their functions differ?','guide':'到酒店了 announces arrival; 太漂亮了 expresses appreciation; 要办理入住 states intention.'}],
      '9':[{'prompt':'What does the amount cover? What cannot be inferred about the stay?','guide':'两个房间一共 is a total for two rooms. Nights, room category, tax and equal individual prices are not specified.'},{'prompt':'Repair “每个房间三千” without adding information.','guide':'For example: 不是每个房间三千，是两个房间一共三千泰铢。Acknowledge confusion and repeat the unit.'}],
      '11':[{'prompt':'Which words show that entry is requested? Why does the guest’s next turn matter?','guide':'可以进来吗 requests permission; 请进 grants it. A professional extension also allows the guest to delay or decline.'}]},
    'patterns':[
      {'id':'zt-03-arrival','title':'到 + place + 了','explanation':'This source pattern reports arrival or a newly reached situation. Contrast 去酒店 (go to the hotel) and 在酒店 (be at the hotel). 了 is not a general past-tense marker.','examples':['我们到酒店了。','我到曼谷了。'],'origin':'adaptation','exampleOrigin':'textbook','sourceRefs':refs(3,5,12),'pitfall':'In this target pattern put 了 after the place. 到了酒店 is possible in other constructions and is not universally wrong.','application':'Report that you have arrived, then state where the guest is now. Explain the change in meaning.'},
      {'id':'zt-03-total','title':'一共: specify the unit of a total','explanation':'一共 introduces a total across stated rooms, people or items. Slide 9 gives a combined total for two rooms, without specifying nights or a nightly rate.','examples':['两个房间一共是3,000泰铢，','酒店一共有100个房间。'],'origin':'adaptation','exampleOrigin':'textbook','sourceRefs':refs(3,7,9),'pitfall':'Do not infer equal prices or included charges from a combined total.','application':'Clarify the total with 不是…，是…. Ask about one detail not supplied.'},
      {'id':'zt-03-permission','title':'可以…吗？ / 请…','explanation':'可以…吗？ asks whether an action is permitted here. 请 makes a request or invitation more courteous. Respecting a refusal is a supplementary pragmatic extension of the source.','examples':['服务员：您好!我是服务员，可以进来吗？','小乐：请进，有什么事情?'],'origin':'adaptation','exampleOrigin':'textbook','sourceRefs':refs(3,11),'pitfall':'A polite request is not itself consent. Wait for an answer and acknowledge 现在不方便.','application':'Make a luggage-delivery request and respond naturally when the guest declines.'}],
    'questions':[
      q(n,'purpose','Which phrase states the purpose of the guests’ visit?',['我们要办理入住。','这个酒店太漂亮了！','这儿是曼谷酒店。'],'要办理入住 states the intended action; the others express appreciation and identify the hotel.',[5]),
      q(n,'total','Which interpretation of slide 9 is supported?',['两个房间合计三千泰铢。','每个房间每晚三千泰铢。','两个房间住三晚，一共三千泰铢。'],'一共 marks a combined total. Nights and individual rates are not given; the amount is a source training scenario.',[9]),
      q(n,'inference','Which detail must be clarified rather than inferred?',['客人住几个晚上。','客人拿到的是房卡。','工作人员向客人要护照。'],'The dialogue identifies room cards and a passport request, but does not specify length of stay.',[8,9]),
      q(n,'permission','What shows that permission is requested on slide 11?',['工作人员先问能否进来，客人再说“请进”。','送行李不必询问。','工作人员先进去，再说明原因。'],'可以进来吗 precedes 请进. The sequence matters.',[11],layer='communicate'),
      q(n,'collocation','Complete with the source verb: 您好，我们要____入住。',None,'办理入住 is the collocation on slide 5: complete check-in formalities.',[3,5],'accuracy',answers=['办理'],category='vocabulary'),
      q(n,'card','A guest needs access to the room. Which source item is relevant?',['房卡','电话卡','银行卡'],'Slide 8 contrasts the cards: 房卡 is the room key card.',[8],'accuracy',category='vocabulary'),
      q(n,'arrival','Use the exact source pattern 到 + place + 了. Complete: 我们____。（arrived at the hotel）',None,'我们到酒店了 reports arrival. 去酒店 indicates going; 在酒店 indicates location.',[12],'accuracy',answers=['到酒店了'],category='grammar'),
      q(n,'repair','The guest asks “是每个房间三千吗？” Which reply resolves this misunderstanding?',['抱歉没说明白，是两个房间一共三千泰铢。','对，每个房间三千，住三晚。','不用问，给钱就可以。'],'Restate the source unit and total; do not invent nights or dismiss the question.',[9],'communication','apply'),
      q(n,'decline','New service scenario: the guest answers “现在不方便。” after “可以进来吗？” Choose a suitable next turn.',['好的，请问什么时候方便？','没关系，我已经进来了。','您不方便也得开门。'],'Respect the answer and negotiate a time. This is a newly authored extension, not a textbook answer.',[11],'audience','apply'),
      q(n,'wording','Which displayed wording on slide 4 needs teacher review as a likely typo?',['远动员','服务员','工作人员'],'The source displays 远动员. The standard word 运动员 (athlete) is an editorial correction; the source transcription is retained.',[4],'accuracy',category='grammar')],
    'tasks':[
      task(n,'interpretation','Read with evidence','In 80–120 Chinese characters, explain what dialogue two confirms and leaves unknown. Quote 一共, identify two unknown booking details, and explain why they need clarification.','对话确认客人办理两个房间，费用“一共是三千泰铢”，并且会拿到房卡。不过，课文没有说明住几个晚上，也没有说明房型。因此，工作人员应该先核实这些信息，不能把总价说成每间房每晚的价格。',[9],minimum=80,criteria=['comprehension','accuracy','organization'],checks=['Interpret total and unit accurately.','Identify two absent details.','Support the interpretation with a quotation.'],scaffold=['已确认…；课文未说明…','“一共”说明…，但不能说明…'],challenge='Compare slides 7 and 9: explain why the differing example totals need not be a contradiction.'),
      task(n,'roleplay','Check-in and a change of plan','With a partner, perform a 2–3-minute check-in. Round 1: welcome two guests, confirm the source total of 3,000 baht and offer luggage help. Round 2: the guest thinks the amount is per room and later declines room entry. Repair the misunderstanding and agree a next step. Save an 80–140-character transcript excerpt or reflection. A partner provides live listening; the app does not record or score speech.','客人：是每个房间三千吗？\n前台：抱歉没说明白，是两个房间一共三千泰铢。请问需要帮您送行李吗？\n客人：需要，可是现在不方便进房间。\n前台：好的，我们先不进去。请问什么时候送比较方便？',[5,9,11],kind='roleplay',minimum=80,criteria=['accuracy','communication','audience'],checks=['Clarify total without inventing a nightly rate.','Ask before acting.','Acknowledge refusal and negotiate.','Paraphrase a partner rather than read a complete script.'],scaffold=['Receptionist: welcome → confirm → offer → clarify.','Guest: question the total; decline entry; choose a later time.','您的意思是…，对吗？ / 请问什么时候方便？'],challenge='The guest changes the delivery time twice. Summarize the final agreement without sounding impatient.'),
      task(n,'writing','Two audiences, one clear arrival','Write 180–260 Chinese characters in two labeled parts: a guest welcome message confirming the training scenario (two rooms, 3,000 baht total), explaining room cards and asking about luggage help; then an internal handover identifying confirmed and unresolved details. Use 到…了, 一共 and a permission request. Do not invent room numbers, nights or included services.','客人消息：您好，欢迎您！您已经到酒店了，我们可以先核对预订，再办理入住。在这次培训情境中，两个房间一共是三千泰铢，并不是每间房三千。手续确认后，我们会把房卡交给您。请问需要帮您送行李吗？同事到门口会先问“可以进来吗”，再等您的答复。如果现在不方便，也请告诉我们合适的时间。\n内部交接：客人已到店，练习情境为两个房间，总额三千泰铢。入住晚数、房型及行李送达时间仍需确认。请先核对预订，并征得客人同意后再送行李进房。',[5,7,8,9,11,12],checks=['Keep total and unit accurate.','Explain room cards without inventing services.','Ask permission before action.','Differentiate guest and colleague audiences.','Name unresolved details.'],scaffold=['客人消息：欢迎…；一共…；请问…？','内部交接：已确认…；待确认…','Check the unit after each number.'],challenge='Extend to 300–400 characters with an unexpected request. Justify two register choices in English.')],
    'culturalNotes':[{'id':'zt-03-wording-review','title':'Source wording and professional interpretation','text':'Slide 4 displays 远动员, apparently a typo for 运动员. Keep the original and label the editorial correction. Slides 7 and 9 use separate example totals; do not combine them. The additional service responses extend, rather than quote, the source permission exchange.','origin':'supplementary','sourceRefs':refs(3,4,7,9,11)}]}

def integrate(specs):
    path=ROOT/'data/curriculum.json'; app=json.loads(path.read_text()); source=json.loads((ROOT/'curriculum/lessons.json').read_text())
    for spec in specs:
        n=int(spec['id'].split('-')[1]); lesson=app['lessons'][n-1]; original=source['lessons'][n-1]
        for k,v in spec.items():
            if k not in {'readingSlides','readingPrompts'}:lesson[k]=v
        lesson['originalTitle']=original['titleFromSourceSlide']
        lesson['title']=original['titleFromSourceSlide']
        lesson['readings']=[]
        for slide in spec['readingSlides']:
            s=original['slides'][slide-1]
            lines=[x.strip() for x in s['text'].splitlines() if re.search(r'[\u3400-\u9fff]',x) and not re.match(r'^\s*课文',x)]
            lesson['readings'].append({'id':f'zt-{n:02d}-reading-{slide}','title':f'Source dialogue · slide {slide}','context':'Original Chinese extracted from the textbook. Pinyin is optional in vocabulary; full multilingual text and original visuals are in Sources.','body':lines,'origin':'textbook','sourceRefs':refs(n,slide),'discussion':spec.get('readingPrompts',{}).get(str(slide),[])})
        lesson['adaptationVersion']=2;lesson['approval']='author_adapted_pending_teacher';lesson['status']='available'
    errors=validate_curriculum(app)
    if errors:raise ValueError(errors)
    path.write_text(json.dumps(app,ensure_ascii=False,indent=2)+'\n')
    return app

if __name__=='__main__':
    target=ROOT/'curriculum/adaptations.json'
    if '--prototype' in sys.argv:
        specs=[prototype()]
        target.write_text(json.dumps({'schemaVersion':2,'approval':'editorial_pending_teacher','lessons':specs},ensure_ascii=False,indent=2)+'\n')
    elif '--author' in sys.argv:
        from scripts.lesson_specs import build_all
        from scripts.enrich_adaptations import enrich
        specs=enrich(build_all())
        target.write_text(json.dumps({'schemaVersion':2,'approval':'editorial_pending_teacher','lessons':specs},ensure_ascii=False,indent=2)+'\n')
    else:specs=json.loads(target.read_text())['lessons']
    app=integrate(specs)
    from scripts.enrich_adaptations import enrich_vocabulary
    app=enrich_vocabulary(app)
    (ROOT/'data/curriculum.json').write_text(json.dumps(app,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'adaptedLessons':len(specs),'questions':sum(len(l['questions']) for l in specs),'tasks':sum(len(l['tasks']) for l in specs)}))
