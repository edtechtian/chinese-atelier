import {visualView,visualEvent,visualSubmit,visualInput,visualPortfolio,vocabularyPicture,prepareVisual} from './visual.js';
import {celebrate} from './rewards.js';
import {api,esc,icon,notice,empty,date,toast,errorView,originLabel,sourceRefs,download,setTimeZone} from './lib.js';
import {teacherView,teacherEvent,teacherSubmit} from './teacher.js';
import {dailyView,dailyEvent,dailySubmit,dailyInput,microPortfolio,teacherDailySubmit,trackVisualClock} from './daily.js';

let B=null, activeLesson=null, practiceData=null, currentRoute='', renderId=0;
let flashIndex=0, flashFlipped=false, flashKey='';
let libraryQuery='', libraryFilter='all', portfolioFilter='all';
let resolvedMistake=null;
const lessonCache=new Map(), saveQueues=new Map(), saveTimers=new Map();
const sections=[['overview','Overview'],['vocabulary','Vocabulary'],['reading','Reading & dialogue'],['language','Language development'],['practice','Check understanding'],['challenge','Communication & application'],['reflection','Reflect & complete'],['sources','Original sources']];
const sectionNames=Object.fromEntries(sections);
const route=()=>location.hash.replace(/^#\/?/,'').split('/').filter(Boolean);
const href=(id,section='overview')=>'#/lesson/'+encodeURIComponent(id)+'/'+section;
const allLessons=()=>B.lessons.concat(B.supplementary);
const progress=(id)=>B.state.progress[id]||{sections:[],completed:false,lastSection:'overview'};
const latestAttempts=()=>Object.values(B.state.attempts.reduce((a,v)=>{a[v.questionId]=v;return a;},{}));
const canLearn=(l)=>['available','published'].includes(l.status);
const pct=(id)=>progress(id).completed?100:Math.round(progress(id).sections.length/sections.length*100);
const tag=(s,c='')=>'<span class="tag '+c+'">'+esc(s)+'</span>';
const linkButton=(text,url,cls='button')=>'<a class="'+cls+'" href="'+esc(url)+'">'+text+'</a>';
const inputDraft=(id)=>{try{return localStorage.getItem('atelier-draft-'+id);}catch{return null;}};
const putDraft=(id,text)=>{try{localStorage.setItem('atelier-draft-'+id,text);}catch{toast('Browser draft storage is unavailable. Use Save draft before leaving.',true);}};
const removeDraft=(id)=>{try{localStorage.removeItem('atelier-draft-'+id);}catch{}};

function sidebar(teacher=false) {
  const r=route()[0]||'home';
  const nav=teacher ? [['home','Student view','#/home'],['book','Teacher desk','#/teacher/overview']] : [['home','Today','#/home'],['globe','Learning path','#/path'],['practice','Review Centre','#/review'],['book','Phrasebook','#/phrasebook'],['pin','Hospitality challenges','#/challenges'],['portfolio','Your portfolio','#/portfolio'],['folder','Source library','#/lessons']];
  return '<aside class="sidebar" id="sidebar" aria-label="Main navigation"><a class="brand" href="'+(teacher?'#/teacher/overview':'#/home')+'"><span class="brand-mark" lang="zh">旅</span><span class="brand-name">Chinese Atelier<small>YOUR CHINESE ADVENTURE</small></span></a><div class="student-tag">'+(teacher?'TEACHER WORKSPACE':'EMMALYNE’S ADVENTURE')+'</div><nav class="nav">'+nav.map(([i,t,url],index)=>'<a href="'+url+'" class="'+((teacher?index===1:(['home','path','review','phrasebook','challenges','portfolio','lessons'][index]===r || (r==='step'&&index===1) || (r==='lesson'&&index===6)))?'active':'')+'">'+icon(i)+esc(t)+'<span class="nav-dot"></span></a>').join('')+'</nav><div class="sidebar-note">'+icon('globe')+'<p>A new word.<br>A wider world.</p><a class="text-link" href="#/visual">Explore with pictures →</a></div><div class="profile"><span class="avatar">'+(teacher?'T':'E')+'</span><div><strong>'+ (teacher?'Teacher desk':'Emmalyne')+'</strong><small>'+(teacher?'Same-device teaching view':'Grade 11 · Chinese B')+'</small></div></div></aside>';
}

function shell(content,label,teacher=false) {
  const today=new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:B.state.learning?.settings.timeZone||'Asia/Bangkok'}).format(new Date());
  return sidebar(teacher)+'<div class="page"><header class="topbar"><div class="topbar-left"><button class="icon-button menu-button" data-action="menu" aria-label="Toggle navigation" aria-expanded="false">'+icon('menu')+'</button><span class="muted">Your atelier</span>'+icon('chevron')+'<strong>'+esc(label)+'</strong></div><div class="topbar-right"><time>'+today+'</time><span class="local-dot"></span><span>Saved on this device</span></div></header><aside class="browser-privacy" aria-label="Browser storage">Online learning · Saved in this browser only. Export your portfolio to back up or share your work.</aside><main class="main" id="main" tabindex="-1">'+content+'</main><footer class="page-footer"><span>《走遍泰国》 · Prince of Songkla University Phuket Confucius Institute</span><span>Local, private learning · <a href="#" data-action="privacy">About your data</a></span></footer></div>'+(!teacher?'<nav class="bottom-nav" aria-label="Mobile main navigation">'+[['home','Today','home'],['globe','Path','path'],['refresh','Review','review'],['book','Phrases','phrasebook'],['portfolio','Portfolio','portfolio']].map(([i,t,r])=>'<a href="#/'+r+'" class="'+((route()[0]||'home')===r?'active':'')+'">'+icon(i)+'<span>'+t+'</span></a>').join('')+'</nav>':'');
}

function intro(eyebrow,title,description,action='') {
  return '<div class="page-intro"><div><div class="eyebrow">'+esc(eyebrow)+'</div><h1>'+esc(title)+'</h1><p>'+esc(description)+'</p></div>'+action+'</div>';
}

function stat(label,value,caption,i='book',bar=null) {
  return '<div class="stat"><div class="stat-top">'+esc(label)+icon(i)+'</div><div class="stat-value">'+value+'</div><div class="stat-caption">'+esc(caption)+'</div>'+(bar!==null?'<progress max="100" value="'+bar+'" aria-label="'+esc(label)+'"></progress>':'')+'</div>';
}

function home() {
  const completed=B.lessons.filter(l=>progress(l.id).completed).length;
  const started=B.lessons.filter(l=>B.state.progress[l.id]&&!progress(l.id).completed).sort((a,b)=>(progress(b.id).updatedAt||'').localeCompare(progress(a.id).updatedAt||''));
  const next=started[0]||B.lessons.find(l=>!progress(l.id).completed&&canLearn(l))||B.lessons[0];
  const section=progress(next.id).lastSection||'overview';
  const due=Object.values(B.state.reviews).filter(r=>new Date(r.dueAt)<=new Date()).length;
  const works=Object.values(B.state.responses).filter(r=>r.submitted).length;
  const verified=Object.values(B.state.responses).filter(r=>r.teacherReview).length;
  const activities=B.state.activity.slice(0,4);
  return intro('A personal path to hospitality','Welcome back, Emmalyne.','Your Chinese is a way to help someone feel at home.')+
    '<section class="hero" aria-label="Your Chinese learning journey"><div class="hero-copy"><div class="eyebrow">CHINESE B, BEYOND THE CLASSROOM</div><h2>A world to explore.<br><span>A welcome to give.</span></h2><p>Read with confidence. Find your voice. Turn Chinese into thoughtful experiences for the people you meet.</p>'+linkButton('Continue your journey '+icon('arrow'),href(next.id,section))+'</div><div class="hero-visual"><img src="../public/assets/coast.jpg" alt="A beach photograph preserved from the source course"><a class="photo-credit" href="'+href('zt-11','sources')+'">Source image · Lesson 11, slide 5</a><div class="destination-note"><div><span class="chinese-title" lang="zh">走遍泰国</span><small>TWENTY LESSONS · COUNTLESS CONVERSATIONS</small></div><span class="stamp">TH / ZH</span></div></div></section>'+
    '<div class="stats-grid">'+stat('Course journey',completed+' <small>/ 20 lessons</small>','Textbook course completion','book',completed*5)+stat('Words revisited',Object.keys(B.state.reviews).length+' <small>expressions</small>',due?due+' ready to review':'A few words, often','refresh')+stat('Your portfolio',works+' <small>submissions</small>',verified+' with teacher feedback','portfolio')+stat('Source collection',B.sourceStats.files+' <small>/ 20 files</small>',B.sourceStats.slides+' slides · source-linked learning','folder')+'</div>'+
    '<div class="dashboard-columns"><section class="panel"><div class="section-heading"><div><h2>Your course, at a glance</h2><p>Follow the original journey. Make it your own.</p></div>'+linkButton('View all '+icon('arrow'),'#/lessons','text-link')+'</div><div class="course-map">'+B.lessons.map(l=>'<a class="course-stop '+(progress(l.id).completed?'complete':l.id===next.id?'current':!canLearn(l)?'missing':'')+'" href="'+href(l.id,progress(l.id).lastSection)+'" aria-label="Lesson '+l.number+': '+esc(l.title)+(progress(l.id).completed?', completed':'')+'">'+(progress(l.id).completed?icon('check'):String(l.number).padStart(2,'0'))+'</a>').join('')+'</div><div class="map-legend"><span><i class="legend-dot dark"></i>Your next stop</span><span><i class="legend-dot"></i>Completed</span><span><i class="legend-dot hollow"></i>Ready to explore</span></div><div class="next-lesson"><span class="lesson-number">'+String(next.number).padStart(2,'0')+'</span><div><div class="eyebrow">'+(B.state.progress[next.id]?'PICK UP WHERE YOU LEFT OFF':'YOUR FIRST DESTINATION')+'</div><h3 lang="zh">'+esc(next.title)+'</h3><small class="muted">'+esc(next.subtitle)+' · '+next.minutes+' min</small></div>'+linkButton('Open '+icon('arrow'),href(next.id,section),'text-link')+'</div><p class="review-footnote">Source text, editorial explanations and newly authored tasks are labeled separately. Teacher verification is still pending for adaptations and source visuals.</p></section><div class="dashboard-right"><section class="panel practice-banner"><div class="eyebrow">A LITTLE, OFTEN</div><h2>Keep the words<br>within reach.</h2><p>'+(due?'You have '+due+' expression'+(due===1?'':'s')+' due for review.':'Review the expressions from lessons you’ve started, at a pace that suits you.')+'</p>'+linkButton('Visit practice centre '+icon('arrow'),'#/practice/vocabulary','button secondary small')+'</section><section class="panel"><h3>Recent moments</h3>'+(activities.length?'<ul class="activity-list">'+activities.map(a=>'<li><span class="activity-symbol">'+icon('check')+'</span><div><strong>'+esc(a.title)+'</strong><small>'+date(a.at)+'</small></div></li>').join('')+'</ul>':'<p class="quiet-note">Your journal is waiting.<br>Open a lesson, try a conversation, or save your first piece of writing.</p>')+'</section></div></div>';
}

function lessonCard(l) {
  const p=progress(l.id);
  const status=p.completed?'Completed':p.sections.length?'In progress':canLearn(l)?'Ready to explore':'Source review';
  return '<a class="lesson-card" href="'+href(l.id,p.lastSection)+'"><div class="card-top"><span class="number">'+String(l.number).padStart(2,'0')+'</span>'+tag(status,p.completed?'verified':p.sections.length?'warm':'gray')+'</div><h3 lang="zh">'+esc(l.title)+'</h3><div class="subtitle">'+esc(l.subtitle)+'</div><div class="card-bottom"><span>'+icon('clock')+' '+(l.minutes||'—')+' min · '+l.vocabularyCount+' expressions</span>'+icon('arrow')+'</div><progress max="100" value="'+pct(l.id)+'" aria-label="Lesson '+l.number+' completion"></progress></a>';
}

function library() {
  return intro('The original course · your own journey','Twenty stops. A wider world.','Explore 《走遍泰国》 in its original sequence, with a professional purpose for every lesson.')+
    '<div class="toolbar"><label class="search-field"><span class="sr-only">Search lessons</span>'+icon('search')+'<input id="lesson-search" type="search" placeholder="Search in Chinese or English…" value="'+esc(libraryQuery)+'" aria-label="Search lessons"></label><label><span class="sr-only">Filter lessons</span><select id="lesson-filter" aria-label="Filter lessons"><option value="all">All lessons</option><option value="progress" '+(libraryFilter==='progress'?'selected':'')+'>In progress</option><option value="complete" '+(libraryFilter==='complete'?'selected':'')+'>Completed</option><option value="ready" '+(libraryFilter==='ready'?'selected':'')+'>Not started</option><option value="review" '+(libraryFilter==='review'?'selected':'')+'>Source review needed</option></select></label></div><div id="lesson-results">'+libraryResults()+'</div><section class="scroll-anchor" id="studio"><div class="section-heading"><div><div class="eyebrow">BEYOND THE SOURCE COURSE</div><h2>The hospitality studio</h2><p>Four newly authored workshops, separate from the 20 textbook lessons.</p></div></div><div class="studio-grid">'+B.supplementary.map(l=>'<a class="studio-card" href="'+href(l.id,progress(l.id).lastSection)+'">'+tag('SUPPLEMENTARY','warm')+'<h3 lang="zh">'+esc(l.title)+'</h3><p>'+esc(l.subtitle)+' · '+l.minutes+' min</p><span class="text-link">'+(progress(l.id).completed?'Revisit workshop':B.state.progress[l.id]?'Resume workshop':'Explore workshop')+icon('arrow')+'</span></a>').join('')+'</div></section>';
}

function libraryResults() {
  const query=libraryQuery.toLocaleLowerCase().trim();
  const filtered=B.lessons.filter(l=>(l.title+' '+l.subtitle+' '+l.number).toLocaleLowerCase().includes(query)).filter(l=>{
    const p=progress(l.id);
    return libraryFilter==='all'||libraryFilter==='progress'&&B.state.progress[l.id]&&!p.completed||libraryFilter==='complete'&&p.completed||libraryFilter==='ready'&&!B.state.progress[l.id]&&canLearn(l)||libraryFilter==='review'&&l.approval!=='teacher_approved';
  });
  return '<p class="small muted">'+filtered.length+' of 20 lessons</p>'+(filtered.length?'<div class="lesson-grid">'+filtered.map(lessonCard).join('')+'</div>':empty('No matching lessons','Try a different search term or filter.'))+'<div class="section-bottom"></div>';
}

function originRow(item) { return '<div class="origin-row">'+tag(originLabel(item.origin),item.origin==='textbook'?'gray':'warm')+sourceRefs(item)+'</div>'; }

function sectionFooter(l,section) {
  const i=sections.findIndex(s=>s[0]===section), done=progress(l.id).sections.includes(section);
  return '<div class="section-bottom"><span class="small muted">'+(done?icon('check')+' Section marked complete':'Move forward when you feel ready.')+'</span><button class="button" data-action="section-done" data-section="'+section+'" data-next="'+(sections[Math.min(i+1,sections.length-1)][0])+'">'+(done?'Continue': 'Mark section complete')+icon('arrow')+'</button></div>';
}

function teachingBrief(l) {
  const p=l.pedagogy;if(!p)return '';
  return '<div class="content-card"><div class="eyebrow">YOUR ROUTE THROUGH THIS LESSON</div><h2>Start from what you can already read.</h2><p>'+esc(p.profile)+'</p><h3>A quick starting check</h3><p>'+esc(p.diagnostic)+'</p><div class="learning-layers">'+p.sequence.map(x=>'<div class="layer"><h3>'+esc(x.stage)+' · '+x.minutes+' min</h3><p>'+esc(x.activity)+'</p></div>').join('')+'</div><details class="details"><summary>How this lesson adapts the source</summary>'+p.decisions.map(x=>'<h3>'+esc(x.action.charAt(0).toUpperCase()+x.action.slice(1))+'</h3><p>'+esc(x.content)+' '+sourceRefs(x)+'</p>').join('')+'</details><details class="details"><summary>Optional multilingual connection</summary><p>'+esc(p.multilingual)+'</p></details></div>';
}

function lessonOverview(l) {
  return teachingBrief(l)+'<div class="content-card"><div class="eyebrow">YOUR LEARNING BRIEF</div><h2>Understand. Communicate. Apply.</h2><p>'+esc(l.subtitle)+' — a '+l.minutes+'-minute learning unit built around purposeful communication.</p>'+originRow({origin:l.kind==='textbook'?'adaptation':'supplementary',sourceRefs:[]})+'<h3>By the end, you can…</h3><ul>'+l.objectives.map(o=>'<li>'+esc(o)+'</li>').join('')+'</ul><div class="learning-layers">'+[['01','Understand',l.goals[0]],['02','Communicate',l.goals[1]||l.goals[0]],['03','Apply professionally',l.goals[2]||l.hospitality]].map(([n,t,txt])=>'<div class="layer"><span class="num">'+n+'</span><h3>'+t+'</h3><p>'+esc(txt)+'</p></div>').join('')+'</div><h3>Your professional connection</h3><p>'+esc(l.hospitality)+'</p></div><div class="content-card"><h3>Make the level work for you</h3><p>Your reading fluency is the starting point. Focus on interpreting intentions, explaining choices and using a professional register. Pinyin is optional. Open a scaffold when needed, or try the extended challenge when you are ready.</p><p>Listening happens through live partner or teacher dialogue practice. No recorded course audio or automatic speech recognition is available in this version.</p></div>'+sectionFooter(l,'overview');
}

function flashcard(v,total,context='lesson') {
  const prefs=B.state.preferences;
  return '<div class="vocab-head"><span class="small muted">Expression '+(flashIndex+1)+' of '+total+'</span><div class="button-row"><label class="toggle"><input id="pinyin-toggle" type="checkbox" '+(prefs.pinyin?'checked':'')+'> Optional pinyin</label><label class="toggle">Gloss <select id="gloss-select" aria-label="Optional support language"><option value="en">English</option><option value="th" '+(prefs.gloss==='th'?'selected':'')+'>Thai support</option><option value="de" '+(prefs.gloss==='de'?'selected':'')+'>German support</option></select></label></div></div><button class="flashcard" data-action="flip" aria-label="'+(flashFlipped?'Show Chinese expression':'Reveal meaning and context')+'" aria-pressed="'+flashFlipped+'">'+(flashFlipped?'<span class="eyebrow">MEANING & CONTEXT</span><span class="meaning">'+esc(v.meaning)+'</span><span class="example zh" lang="zh">'+esc(v.example)+'</span><span class="small muted">'+(v.exampleOrigin==='textbook'?'Source example':'Newly authored example')+'</span><span class="small muted">'+(prefs.gloss!=='en'&&v.gloss&&v.gloss[prefs.gloss]?esc(v.gloss[prefs.gloss]):prefs.gloss!=='en'?'No '+(prefs.gloss==='de'?'German':'Thai')+' gloss supplied for this expression.':'')+'</span>':vocabularyPicture(v)+'<span class="eyebrow">RECALL THE MEANING. USE IT IN CONTEXT.</span><span class="word zh" lang="zh">'+esc(v.chinese)+'</span>'+(prefs.pinyin?'<span class="pinyin">'+esc(v.pinyin)+'</span>':''))+'<span class="flip-hint">'+(flashFlipped?'Tap to return to the expression':'Tap to reveal meaning and context')+'</span></button><div class="origin-row">'+sourceRefs(v)+'<span class="small muted">'+(v.editorialNote?esc(v.editorialNote):'Newly authored supplementary vocabulary')+'</span></div>'+(flashFlipped?'<div class="review-controls">'+[['again','Again','10 minutes'],['hard','Hard','slower review'],['good','Good','regular interval'],['easy','Easy','longer interval']].map(([rating,t,sub])=>'<button class="button secondary small" data-action="rate" data-rating="'+rating+'" data-vocab="'+v.id+'" data-lesson="'+(v.lessonId||activeLesson.id)+'" data-context="'+context+'">'+t+'<small>'+sub+'</small></button>').join('')+'</div>':'<p class="small muted">Try recalling a meaning and a contextual use before you reveal the card.</p>')+'<div class="section-bottom"><button class="text-link" data-action="flash-prev" '+(flashIndex===0?'disabled':'')+'>Previous</button><span class="small muted">Self-rating schedules practice; it is not an assessment score.</span><button class="text-link" data-action="flash-next">Next expression '+icon('arrow')+'</button></div>';
}

function lessonVocab(l) {
  if(!l.vocabulary.length) return empty('Vocabulary needs source review','The original slide material is preserved in Sources. The teacher can add reviewed vocabulary.');
  if(flashKey!==l.id){flashIndex=0;flashFlipped=false;flashKey=l.id;}
  flashIndex=Math.min(flashIndex,l.vocabulary.length-1);
  return '<div class="content-card"><h2>Words with a purpose</h2><p>Recall the meaning, then think about how you would use the expression with a guest.</p>'+flashcard(l.vocabulary[flashIndex],l.vocabulary.length)+'</div><div class="content-card"><details><summary>Browse all '+l.vocabulary.length+' expressions</summary><div class="vocab-list">'+l.vocabulary.map(v=>'<div class="vocab-row"><div class="vocab-word zh" lang="zh">'+esc(v.chinese)+(B.state.preferences.pinyin?'<div class="pinyin">'+esc(v.pinyin)+'</div>':'')+'</div><div><p>'+esc(v.meaning)+'</p><p class="example zh" lang="zh">'+esc(v.example)+'</p>'+(v.collocations.length?'<p class="small muted">'+'Editorial usage chunk: '+esc(v.collocations.join(' · '))+'</p>':'')+'</div>'+sourceRefs(v)+'</div>').join('')+'</div></details><p class="small muted">All original word lists, proper names, phrase lists and illustrated vocabulary remain in the source slides, including items outside the flashcard set.</p></div>'+sectionFooter(l,'vocabulary');
}

function lessonReading(l) {
  return l.readings.map(r=>'<article class="content-card">'+originRow(r)+'<h2>'+esc(r.title)+'</h2><p class="muted">'+esc(r.context)+'</p><div class="reading-text zh" lang="zh">'+r.body.map(p=>'<p>'+esc(p)+'</p>').join('')+'</div><div class="reading-questions"><h3>Interpret and discuss</h3><p class="small muted">Newly authored prompts · give evidence in Chinese. These are open responses, not automatically scored.</p>'+(r.discussion||[]).map(x=>'<div class="discussion-item"><p>'+esc(x.prompt)+'</p><details class="details"><summary>Compare your reasoning</summary><p>'+esc(x.guide)+'</p></details></div>').join('')+'</div></article>').join('')+sectionFooter(l,'reading');
}

function lessonLanguage(l) {
  return l.patterns.map(p=>'<article class="content-card">'+originRow(p)+'<h2>'+esc(p.title)+'</h2><p>'+esc(p.explanation)+'</p><h3>Language in context</h3><p class="small muted">'+(p.exampleOrigin==='textbook'?'Examples quoted from the source; English explanation is editorial.':'Newly authored examples based on the source pattern.')+'</p>'+p.examples.map(x=>'<span class="pattern-example zh" lang="zh">'+esc(x)+'</span>').join('')+(p.pitfall?'<h3>Notice the distinction</h3><p>'+esc(p.pitfall)+'</p>':'')+'<details class="details"><summary>Apply it in your own words</summary><p>'+esc(p.application||'Use the pattern in a two-sentence response, then change one detail and explain the difference.')+'</p></details></article>').join('')+sectionFooter(l,'language');
}

function feedbackHtml(a) {
  return '<div class="feedback '+(a.correct?'success':'incorrect')+'"><strong>'+icon(a.correct?'check':'info')+' '+(a.correct?'You’ve got it.':'A useful point to revisit.')+'</strong>'+esc(a.explanation||'Your answer is saved. Recheck this item to see its explanation.')+'</div>';
}

function questionCard(q,l,practice=false) {
  const last=[...B.state.attempts].reverse().find(a=>a.questionId===q.id);
  const readings=practice&&q.skill==='comprehension'?l.readings:[];
  return '<form class="question-card" data-form="question" data-lesson="'+l.id+'" data-question="'+q.id+'"><div class="origin-row">'+tag('Newly authored practice','warm')+tag(q.category||q.skill.replace('accuracy','Language accuracy'))+sourceRefs(q)+(practice?linkButton('Open lesson '+icon('arrow'),href(l.id,'reading'),'text-link'):'')+'</div>'+(readings.length?'<details class="details"><summary>Read the source context before answering</summary>'+readings.map(r=>'<div class="reading-text zh" lang="zh">'+r.body.map(x=>'<p>'+esc(x)+'</p>').join('')+'</div>').join('')+'</details>':'')+'<h3>'+esc(q.prompt)+'</h3>'+(q.type==='choice'?'<fieldset class="options"><legend class="sr-only">Choose one answer</legend>'+q.options.map(o=>'<label class="option"><input type="radio" name="answer" value="'+esc(o.id)+'" required '+(last&&last.answer===o.id?'checked':'')+'><span>'+esc(o.text)+'</span></label>').join('')+'</fieldset>':'<label class="field-label" for="answer-'+q.id+'">Your Chinese answer</label><input class="answer-input" id="answer-'+q.id+'" name="answer" type="text" maxlength="1000" required value="'+esc(last?last.answer:'')+'" lang="zh" autocomplete="off">')+'<button class="button secondary small" type="submit">'+(last?'Check again':'Check answer')+'</button><span class="small muted" data-attempt-status> '+(last?'Previous attempt: '+(last.correct?'correct':'needs review'):'Practice feedback · not an official grade')+'</span><div class="answer-feedback" aria-live="polite">'+(last&&last.explanation?feedbackHtml(last):'')+'</div></form>';
}

function lessonPractice(l) {
  return '<div class="content-card"><div class="eyebrow">FORMATIVE PRACTICE</div><h2>Make your understanding visible.</h2><p>Read the source dialogue first. Try every question, use the feedback, and return to any items that need another look.</p></div>'+l.questions.map(q=>questionCard(q,l)).join('')+sectionFooter(l,'practice');
}

function rubric(criteria,compact=false) {
  return '<div class="rubric-grid">'+B.criteria.filter(c=>!criteria||criteria.includes(c.id)).map(c=>'<div class="rubric-item"><strong>'+esc(c.label)+'</strong><p>'+(compact?esc(c.descriptors[2]):c.descriptors.map((d,i)=>'<b>'+String(i+1)+'.</b> '+esc(d)).join('<br>'))+'</p></div>').join('')+'</div>';
}

function teacherFeedback(r) {
  if(!r.teacherReview) return '<p class="small muted">'+(r.submitted?'Awaiting teacher review. Automated checks are practice guidance only.':'Draft · submit when you want your teacher to review it.')+'</p>';
  const t=r.teacherReview;
  return '<div class="teacher-feedback"><strong>Teacher-verified feedback</strong><p>'+esc(t.comment)+'</p><div class="score-tags">'+B.criteria.filter(c=>Number.isInteger(t.scores[c.id])).map(c=>'<span>'+esc(c.label)+' · '+t.scores[c.id]+'/4</span>').join('')+'</div><small>'+date(t.at)+' · Criterion levels, not an official IB grade.</small></div>';
}

function taskCard(t,l) {
  const r=B.state.responses[t.id];
  const stored=inputDraft(t.id), local=stored!==null&&stored!==(r?.text||'')?stored:null, text=local!==null?local:r?r.text:'';
  return '<article class="content-card" id="'+t.id+'">'+originRow(t)+'<div class="eyebrow">'+(t.type==='roleplay'?'SPEAK, THEN REFLECT':'WRITE FOR A REAL AUDIENCE')+'</div><h2>'+esc(t.title)+'</h2><p class="task-prompt">'+esc(t.prompt)+'</p>'+(t.successCriteria?.length?'<div class="success-criteria"><h3>Success looks like…</h3><ul>'+t.successCriteria.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul><p class="small muted">Teacher-reviewed communication. Automated feedback checks length and revision only.</p></div>':'')+'<details class="details"><summary>Need a little structure?</summary><ul>'+t.scaffold.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ul></details><details class="details"><summary>Try the extended challenge</summary><div class="challenge-box"><p>'+esc(t.challenge)+'</p></div></details><form data-form="response" data-task="'+t.id+'" data-lesson="'+l.id+'"><label class="field-label" for="response-'+t.id+'">'+(t.type==='roleplay'?'Your Chinese transcript or reflection':'Your Chinese response')+'</label><textarea class="response-box zh" id="response-'+t.id+'" name="text" data-task="'+t.id+'" data-lesson="'+l.id+'" rows="8" maxlength="12000" lang="zh" placeholder="Write in Chinese. Your voice, your choices.">'+esc(text)+'</textarea><div class="writing-meta"><span data-count-for="'+t.id+'">'+(text.match(/[\u3400-\u9fff]/g)||[]).length+' Chinese characters</span><span data-save-for="'+t.id+'">'+(local!==null?'Recovered browser draft · saving required':r?'Saved '+date(r.updatedAt):'Drafts save automatically on this device')+'</span></div>'+(local!==null?'<button type="button" class="text-link" data-action="discard-draft" data-task="'+t.id+'">Discard recovered browser draft · keep saved version</button>':'')+'<div class="button-row"><button class="button secondary" type="submit" name="intent" value="save">'+icon('save')+' Save draft</button><button class="button" type="submit" name="intent" value="submit">Submit for teacher review '+icon('arrow')+'</button><button class="text-link" type="button" data-action="model" data-task="'+t.id+'" data-lesson="'+l.id+'">View a model response</button></div><div data-response-feedback="'+t.id+'" aria-live="polite">'+(r?responseFeedback(r):'')+'</div></form><details class="details"><summary>Assessment criteria · what stronger communication looks like</summary>'+rubric(t.criteria)+'</details><div data-model-for="'+t.id+'"></div></article>';
}

function responseFeedback(r) {
  return '<div class="notice"><div><strong>Automated practice checks</strong><ul>'+r.feedback.messages.map(m=>'<li>'+esc(m)+'</li>').join('')+'</ul><span class="small">No automated language-quality or speaking score is assigned.</span></div></div>'+teacherFeedback(r);
}

function lessonChallenge(l) {
  const live=l.liveListening;
  return (live?'<section class="content-card"><div class="eyebrow">LIVE LISTENING · PARTNER OR TEACHER</div><h2>Listen before reopening the text.</h2>'+originRow(live)+'<ol>'+live.instructions.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ol><h3>Listen for this</h3><p>'+esc(live.focus)+'</p><p class="small muted">'+esc(live.assessment)+'</p></section>':'')+notice('Use the task brief and success criteria, draft in your own words, then compare with a model. Models and extensions are newly authored, not textbook answer keys.')+l.tasks.map(t=>taskCard(t,l)).join('')+sectionFooter(l,'challenge');
}

function lessonReflection(l) {
  const p=progress(l.id);
  const tried=new Set(B.state.attempts.filter(a=>a.lessonId===l.id).map(a=>a.questionId));
  const attempted=l.questions.filter(q=>tried.has(q.id)).length;
  const works=Object.values(B.state.responses).filter(r=>r.lessonId===l.id&&r.submitted&&r.text.trim()).length;
  return '<div class="content-card"><div class="eyebrow">LOOK BACK, THEN MOVE FORWARD</div><h2>What can you do now?</h2><p>Completion records your participation and reflection. Your teacher’s criterion feedback records the quality of your communication.</p><ul><li>'+attempted+' / '+l.questions.length+' formative questions attempted</li><li>'+works+' communication task'+(works===1?'':'s')+' submitted (at least one required)</li><li>'+p.sections.length+' / '+sections.length+' sections marked complete</li></ul><form data-form="reflection" data-lesson="'+l.id+'">'+(l.pedagogy?.reflection?'<p>'+esc(l.pedagogy.reflection)+'</p>':'')+'<label class="reflection-label" for="reflection">In Chinese, describe what you can now do and one thing to improve.</label><textarea name="reflection" id="reflection" rows="5" maxlength="4000" lang="zh" placeholder="现在我能…；下一次我想…">'+esc(p.reflection||'')+'</textarea>'+'<div class="button-row"><button class="button secondary" type="submit" name="intent" value="save">Save reflection</button><button class="button" type="submit" name="intent" value="complete">'+icon('check')+' '+(p.completed?'Lesson completed · save update':'Complete this lesson')+'</button></div><div class="reflection-feedback" aria-live="polite"></div></form></div>'+rubric(null,true)+sectionFooter(l,'reflection');
}

export function sourceSlide(s,l,teacher=false) {
  return '<details class="source-slide" id="'+s.id+'"><summary><span>Slide '+s.number+' '+(s.hidden?'· hidden in original':'')+'</span><span>'+tag(s.reviewStatus==='verified'?'Teacher verified':'Review pending',s.reviewStatus==='verified'?'verified':'warm')+' '+(s.visuals.length?'· '+s.visuals.length+' visuals':'')+'</span></summary><div class="source-body"><div class="source-key">'+esc(s.id)+'</div><pre lang="zh">'+esc(s.text||'No selectable text. Review the retained images below; content has not been guessed.')+'</pre>'+(s.notes?'<details class="details"><summary>Original speaker notes</summary><pre>'+esc(s.notes)+'</pre></details>':'')+(s.tables.length?'<details class="details"><summary>Original tables · '+s.tables.length+'</summary>'+s.tables.map(rows=>'<div class="source-table"><table><tbody>'+rows.map(row=>'<tr>'+row.map(c=>'<td>'+esc(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>').join('')+'</details>':'')+(s.charts.length?'<details class="details"><summary>Extracted chart data · verify labels and units</summary><pre>'+esc(JSON.stringify(s.charts,null,2))+'</pre></details>':'')+'<div class="source-images">'+s.visuals.map((v,i)=>'<figure>'+(v.url?'<a href="'+esc(v.url)+'" target="_blank" rel="noopener"><img src="'+esc(v.url)+'" loading="lazy" alt="'+esc(v.alt||'Source illustration '+(i+1)+', lesson '+l.number+', slide '+s.number+'; no source description supplied')+'"></a>':'<p>Original visual retained in PPT; this format cannot be shown.</p>')+'<figcaption>'+esc(v.alt||'No descriptive alt text in original source. Inspect image before using its meaning.')+'</figcaption></figure>').join('')+'</div><ul class="source-issues">'+s.issues.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'+(s.reviewNotes?'<p class="small">Teacher notes: '+esc(s.reviewNotes)+'</p>':'')+(teacher?'<form data-form="verify-slide" data-lesson="'+l.id+'" data-slide="'+s.id+'"><label class="field-label" for="notes-'+s.id+'">Teacher visual / text review notes</label><textarea id="notes-'+s.id+'" name="notes" rows="3" maxlength="4000">'+esc(s.reviewNotes||'')+'</textarea><label class="toggle"><input type="checkbox" name="verified" '+(s.reviewStatus==='verified'?'checked':'')+'> I checked the text, images and context against this original slide.</label><button class="button secondary small" type="submit">Save slide verification</button></form>':'')+'</div></details>';
}

function lessonSources(l) {
  if(l.kind==='supplementary')return '<div class="content-card"><h2>Newly authored, clearly separate.</h2><p>This hospitality workshop was created for Emmalyne. It is not part of 《走遍泰国》, and none of its dialogues, vocabulary or activities are attributed to that textbook. Scenarios and operational details are fictional training briefs.</p><p>Teacher approval is not implied. Use the teacher desk to correct or approve material.</p></div>'+sectionFooter(l,'sources');
  return '<div class="content-card"><h2>A clear path to the original</h2><p>'+esc(B.attribution.institution)+' · 《'+esc(B.attribution.title)+'》</p><p>All '+l.sourceSlides.length+' slides are retained in sequence. Original text, Thai glosses, exercises, visible answer displays, notes and supported images are preserved here. Source answer displays are study materials; newly authored quiz keys are checked separately by the app.</p>'+notice('Text extraction preserves words, but may not preserve reading order or visual relationships. Teacher verification is pending unless a slide is marked verified. Open original files in the teacher desk to check full layout.','warning')+l.culturalNotes.map(n=>'<h3>'+esc(n.title)+'</h3><p>'+esc(n.text)+'</p>').join('')+'</div>'+l.sourceSlides.map(s=>sourceSlide(s,l)).join('')+sectionFooter(l,'sources');
}

async function lessonView(id,section='overview') {
  if(!sectionNames[section])section='overview';
  activeLesson=await loadLesson(id);
  const l=activeLesson;
  if(!canLearn(l))return intro('SOURCE STATUS','This lesson needs source review.',l.title)+notice(esc((l.processing?.issues||['The teacher has not yet prepared this lesson.']).join(' ')),'warning')+linkButton('Back to lesson library','#/lessons');
  const views={overview:lessonOverview,vocabulary:lessonVocab,reading:lessonReading,language:lessonLanguage,practice:lessonPractice,challenge:lessonChallenge,reflection:lessonReflection,sources:lessonSources};
  return '<div class="lesson-heading"><div><a class="text-link" href="#/lessons">← Lesson library</a><div class="eyebrow">'+(l.kind==='textbook'?'LESSON '+String(l.number).padStart(2,'0')+' / 20':'HOSPITALITY STUDIO · SUPPLEMENTARY')+'</div><h1 lang="zh">'+esc(l.title)+'</h1><p class="muted small">'+esc(l.subtitle)+' · '+l.minutes+' min</p></div>'+tag(progress(l.id).completed?'Completed':l.approval==='teacher_approved'?'Teacher approved':'Teacher review pending',progress(l.id).completed?'verified':'warm')+'</div><div class="split-layout"><nav class="section-nav" aria-label="Lesson sections">'+sections.map(([k,label],i)=>'<a href="'+href(l.id,k)+'" class="'+(section===k?'active':'')+'" '+(section===k?'aria-current="page"':'')+'><span class="step">'+String(i+1).padStart(2,'0')+'</span>'+label+(progress(l.id).sections.includes(k)?icon('check','done'):'')+'</a>').join('')+'</nav><div class="section-content">'+views[section](l)+'</div></div>';
}

async function loadLesson(id) {
  if(!lessonCache.has(id))lessonCache.set(id,await api('/api/lessons/'+encodeURIComponent(id)));
  return lessonCache.get(id);
}

async function practice(mode='vocabulary') {
  const modes=[['vocabulary','Vocabulary review'],['mixed','Mixed review'],['accuracy','Language patterns'],['comprehension','Reading'],['audience','Professional Chinese'],['mistakes','From your mistakes']];
  if(!modes.some(([m])=>m===mode))mode='vocabulary';
  practiceData=await api('/api/practice?mode='+mode);
  const introText=intro('A little practice, a lasting impression','Keep your Chinese in motion.','Revisit lessons you’ve started. Build accuracy, notice patterns, and make each response more useful.')+'<nav class="practice-tabs" aria-label="Practice modes">'+modes.map(([m,t])=>'<a href="#/practice/'+m+'" class="'+(m===mode?'active':'')+'">'+t+'</a>').join('')+'</nav>';
  if(!practiceData.startedCount)return introText+empty('Your practice starts with a lesson','Open your first lesson to bring its vocabulary and questions into your personal review collection.',href(B.lessons.find(canLearn)?.id||'zt-01'),'Open lesson one');
  if(mode==='vocabulary') {
    const vocab=practiceData.vocabulary;
    const due=vocab.filter(v=>B.state.reviews[v.id]&&new Date(B.state.reviews[v.id].dueAt)<=new Date());
    const fresh=vocab.filter(v=>!B.state.reviews[v.id]);
    practiceData.queue=due.concat(fresh);
    if(!practiceData.queue.length)return introText+empty('You’re up to date','Every expression in your started lessons is scheduled for later. You can still browse and practise cards inside a lesson.','#/lessons','Explore your lessons');
    const key='practice-vocabulary';if(flashKey!==key){flashIndex=0;flashFlipped=false;flashKey=key;}
    flashIndex=Math.min(flashIndex,practiceData.queue.length-1);
    const v=practiceData.queue[flashIndex];
    return introText+'<div class="practice-grid"><section class="content-card"><div class="origin-row">'+tag(v.lessonTitle)+tag(B.state.reviews[v.id]?'Due now':'New expression','warm')+'</div>'+flashcard(v,practiceData.queue.length,'practice')+'</section><aside class="panel sticky-note"><div class="eyebrow">YOUR REVIEW RHYTHM</div><div class="review-count">'+due.length+'</div><p class="small muted">due expressions, plus '+fresh.length+' not yet reviewed.</p><h3>Recall, then connect.</h3><p class="quiet-note">Say what the expression means. Then use it in a sentence a guest might hear.</p><p class="small muted">Again returns in 10 minutes. Hard grows slowly; Good and Easy extend the interval. All scheduling is local and based on your self-rating.</p></aside></div>';
  }
  const qs=practiceData.questions.slice(0,12);
  const lessons=await Promise.all([...new Set(qs.map(q=>q.lessonId))].map(loadLesson));
  const resolved=mode==='mistakes'&&resolvedMistake?'<section class="content-card" aria-live="polite"><h2>Review item resolved</h2><p>'+esc(resolvedMistake.prompt)+'</p>'+feedbackHtml(resolvedMistake.attempt)+'</section>':'';
  return introText+resolved+(qs.length?notice(mode==='mistakes'?'These are the latest unanswered mistakes, rather than every historical error. A correct retry removes an item from this view.':'Up to 12 items from lessons you have started. Open the reading context before comprehension questions.')+qs.map(q=>questionCard(q,lessons.find(l=>l.id===q.lessonId),true)).join(''):empty(mode==='mistakes'?'Nothing to revisit right now':'No items in this practice category',mode==='mistakes'?'Your latest attempts contain no remaining mistakes. Keep exploring your lessons.':'Start another lesson to expand your practice collection.','#/lessons','Open lesson library'));
}

function insights() {
  const latest=latestAttempts();
  const visualReviews=Object.values(B.state.visualLearning?.responses||{}).filter(r=>r.teacherReview).map(r=>({teacherReview:{...r.teacherReview,scores:Object.fromEntries(Object.entries(r.teacherReview.scores).map(([k,v])=>[({'Comprehension':'comprehension','Language accuracy':'accuracy','Organization':'organization','Audience awareness':'audience'})[k]||k,v]))}}));
  const reviews=[...Object.values(B.state.responses),...Object.values(B.state.learning?.work||{}),...visualReviews].filter(r=>r.teacherReview);
  return '<div class="insight-grid"><section class="panel"><h3>Practice signals</h3><p class="small muted">Latest attempts only · useful for review, not language proficiency grades.</p>'+(latest.length?B.criteria.filter(c=>latest.some(a=>a.skill===c.id)).map(c=>{ const a=latest.filter(a=>a.skill===c.id), correct=a.filter(x=>x.correct).length; return '<div class="bar-row"><div>'+esc(c.label)+'<small>'+correct+' / '+a.length+' latest answers correct</small></div><progress max="'+a.length+'" value="'+correct+'" aria-label="'+esc(c.label)+' latest practice answers"></progress></div>'; }).join(''):'<p class="quiet-note">Complete a few practice items to discover which questions need another look.</p>')+'</section><section class="panel"><h3>Teacher evidence</h3><p class="small muted">Criterion levels use teacher-reviewed submissions only.</p>'+(reviews.length?B.criteria.map(c=>{ const scores=reviews.map(r=>r.teacherReview.scores[c.id]).filter(Number.isInteger);if(!scores.length)return '';const avg=scores.reduce((a,b)=>a+b,0)/scores.length; return '<div class="bar-row"><div>'+esc(c.label)+'<small>Average '+avg.toFixed(1)+' / 4 across '+scores.length+' reviewed task'+(scores.length===1?'':'s')+'</small></div><progress max="4" value="'+avg+'" aria-label="'+esc(c.label)+' teacher evidence"></progress></div>'; }).join(''):'<p class="quiet-note">Your strengths and development priorities will appear as your teacher reviews your work. Reading fluency alone does not establish listening or speaking proficiency.</p>')+'</section></div>';
}

function portfolio() {
  const responses=Object.values(B.state.responses).sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt));
  const selected=responses.filter(r=>portfolioFilter==='all'||portfolioFilter==='draft'&&!r.submitted||portfolioFilter==='submitted'&&r.submitted&&!r.teacherReview||portfolioFilter==='reviewed'&&r.teacherReview);
  return intro('A record of your growing voice','Your work, worth keeping.','Collect your writing and speaking reflections, revisit feedback, and notice what is improving.','<div class="button-row"><button class="button secondary small" data-action="export" data-format="json">'+icon('download')+' Export portfolio</button><button class="text-link" data-action="export" data-format="csv">Progress CSV</button></div>')+insights()+'<div class="section-heading"><h2>Saved work</h2><select id="portfolio-filter" aria-label="Filter saved work"><option value="all">All work</option><option value="draft" '+(portfolioFilter==='draft'?'selected':'')+'>Drafts</option><option value="submitted" '+(portfolioFilter==='submitted'?'selected':'')+'>Awaiting review</option><option value="reviewed" '+(portfolioFilter==='reviewed'?'selected':'')+'>Teacher reviewed</option></select></div>'+(selected.length?selected.map(r=>{ const l=allLessons().find(l=>l.id===r.lessonId);return '<article class="work-card"><div class="work-header"><div>'+tag(r.teacherReview?'Teacher reviewed':r.submitted?'Awaiting review':'Draft',r.teacherReview?'verified':'warm')+'<h3>'+esc(r.taskTitle)+'</h3><span class="small muted">'+esc(l?.title||r.lessonId)+' · '+date(r.updatedAt)+'</span></div>'+linkButton('Revisit & edit '+icon('arrow'),href(r.lessonId,'challenge'),'text-link')+'</div><div class="work-text zh" lang="zh">'+esc(r.text||'Empty draft')+'</div>'+teacherFeedback(r)+(r.reviewHistory?.length?'<p class="small muted">'+r.reviewHistory.length+' earlier teacher review(s) retained in your export. A revision requires a new review.</p>':'')+'</article>';}).join(''):empty('Original-lesson writing','No original-lesson responses match this view. Microlearning and visual work have their own sections below.','#/lessons','Find your next lesson'))+'<section class="content-card"><h3>Lessons completed</h3>'+(B.lessons.some(l=>progress(l.id).completed)?'<ul>'+B.lessons.filter(l=>progress(l.id).completed).map(l=>'<li><a class="text-link" href="'+href(l.id,'reflection')+'">'+esc(l.title)+'</a><p class="small">'+esc(progress(l.id).reflection)+'</p></li>').join('')+'</ul>':'<p class="muted small">Your completed textbook lessons and reflections will appear here. Studio completion is recorded separately in each workshop.</p>')+'</section>';
}

async function render(focus=false) {
  const id=++renderId;
  try {
    if(!B)B=await api('/api/bootstrap');
    setTimeZone(B.state.learning?.settings.timeZone||'Asia/Bangkok');
    await prepareVisual();
    const r=route();
    const teacher=location.hash.startsWith('#/teacher');
    let html,label;
    if(teacher) { html=await teacherView(B,r,sourceSlide,insights);label='Teacher desk'; }
    else if(r[0]==='lessons') {html=library();label='Lesson library';}
    else if(r[0]==='lesson'&&r[1]) {html=await lessonView(r[1],r[2]);label=sectionNames[r[2]]||'Lesson workspace';}
    else if(r[0]==='practice'){html=await practice(r[1]);label='Practice centre';}
    else if(r[0]==='visual'){html=await visualView(dailyContext(),r);label='Visual learning';}
    else if(r[0]==='portfolio'){html=portfolio()+microPortfolio(B,portfolioFilter)+visualPortfolio(B,portfolioFilter);label='Your portfolio';}
    else {html=await dailyView(dailyContext(),r);label=({path:'Learning path',step:'Learning step',review:'Review Centre',phrasebook:'Phrasebook',challenges:'Hospitality challenges',reminders:'Reminders'})[r[0]]||'Today';}
    if(id!==renderId)return;
    document.querySelector('#app').innerHTML=shell(html,label,teacher);
    document.title=(teacher?'Teacher desk':activeLesson&&r[0]==='lesson'?activeLesson.title:label)+' · Emmalyne’s Chinese Atelier';
    if(focus){document.querySelector('#main').focus({preventScroll:true});window.scrollTo(0,0);}
  }catch(e){if(id!==renderId)return;document.querySelector('#app').innerHTML=B?shell(errorView(e)+'<button class="button" data-action="retry">Try again</button>','Something needs attention',location.hash.startsWith('#/teacher')):'<div class="top-error">'+errorView(e)+'<button class="button" data-action="retry">Reconnect</button></div>';}
}

async function refresh(){B=await api('/api/bootstrap');}
function dailyContext(){return {B,refresh,render,loadLesson,trackVisual:trackVisualClock,trackVisual:trackVisualClock,setActiveLesson:l=>activeLesson=l,questionCard,taskCard};}

function saveResponse(lessonId,taskId,text,submit=false,manual=false) {
  putDraft(taskId,text);
  const prior=saveQueues.get(taskId)||Promise.resolve();
  const promise=prior.catch(()=>{}).then(async()=>{
    const r=await api('/api/response',{lessonId,taskId,text,submit});
    B.state.responses[taskId]=r;
    if(inputDraft(taskId)===text)removeDraft(taskId);
    const indicator=document.querySelector('[data-save-for="'+taskId+'"]');
    if(indicator)indicator.textContent=(r.submitted?'Submitted · ':'Saved · ')+date(r.updatedAt);
    const feedback=document.querySelector('[data-response-feedback="'+taskId+'"]');
    if(feedback&&(manual||submit))feedback.innerHTML=responseFeedback(r);
    if(manual)toast(submit?'Submitted for teacher review.':'Draft saved.');
    return r;
  }).catch(e=>{const indicator=document.querySelector('[data-save-for="'+taskId+'"]');if(indicator)indicator.textContent='Server save failed · browser draft retained';if(manual)toast(e.message,true);throw e;});
  saveQueues.set(taskId,promise);
  return promise;
}

document.addEventListener('input',e=>{
  dailyInput(e);visualInput(e);
  if(e.target.id==='lesson-search'){libraryQuery=e.target.value;document.querySelector('#lesson-results').innerHTML=libraryResults();}
  if(e.target.matches('.response-box')){
    const {task,lesson}=e.target.dataset,text=e.target.value;
    putDraft(task,text);
    const counter=document.querySelector('[data-count-for="'+task+'"]');if(counter)counter.textContent=(text.match(/[\u3400-\u9fff]/g)||[]).length+' Chinese characters';
    const indicator=document.querySelector('[data-save-for="'+task+'"]');if(indicator)indicator.textContent='Saving…';
    clearTimeout(saveTimers.get(task));
    saveTimers.set(task,setTimeout(()=>{saveResponse(lesson,task,text).catch(()=>{});},700));
  }
  if(e.target.id==='lesson-json'){const el=document.querySelector('#editor-dirty');if(el)el.textContent='Unsaved changes';}
});

document.addEventListener('change',async e=>{
  try{
    if(e.target.id==='lesson-filter'){libraryFilter=e.target.value;document.querySelector('#lesson-results').innerHTML=libraryResults();}
    if(e.target.id==='portfolio-filter'){portfolioFilter=e.target.value;await render();}
    if(['pinyin-toggle','gloss-select'].includes(e.target.id)){
      B.state.preferences=await api('/api/preferences',{pinyin:document.querySelector('#pinyin-toggle')?.checked||false,gloss:document.querySelector('#gloss-select')?.value||'en'});await render();
    }
  }catch(e){toast(e.message,true);}
});

document.addEventListener('click',async e=>{
  const target=e.target.closest('[data-action]');if(!target)return;
  const action=target.dataset.action;
  e.preventDefault();
  try{
    if(action.startsWith('visual-')){target.disabled=true;await visualEvent(action,target,dailyContext());return;}
    if(action.startsWith('learn-')){target.disabled=true;await dailyEvent(action,target,dailyContext());return;}
    if(action==='menu'){const s=document.querySelector('#sidebar'),opened=s.classList.toggle('open');target.setAttribute('aria-expanded',opened);return;}
    if(action==='retry'){await render();return;}
    if(action==='privacy'){toast('Progress and writing stay in this browser on this device. Export a portfolio backup before clearing site data or changing devices. Teacher review is a same-device view, not remote synchronization.');return;}
    if(action.startsWith('teacher-')){await teacherEvent(action,target,{B,refresh,render,lessonCache});return;}
    if(action==='export'){await download('/api/export?format='+target.dataset.format,'emmalyne-'+(target.dataset.format==='csv'?'progress.csv':'portfolio.json'));return;}
    if(action==='flip'){flashFlipped=!flashFlipped;await render();document.querySelector('.flashcard')?.focus({preventScroll:true});return;}
    if(action==='flash-prev'||action==='flash-next'){
      const total=route()[0]==='practice'?practiceData.queue.length:activeLesson.vocabulary.length;
      flashIndex=action==='flash-prev'?Math.max(0,flashIndex-1):(flashIndex+1)%total;flashFlipped=false;await render();document.querySelector('.flashcard')?.focus({preventScroll:true});return;
    }
    target.disabled=true;
    if(action==='rate'){
      const {vocab,lesson,rating,context}=target.dataset;
      B.state.reviews[vocab]=await api('/api/review',{lessonId:lesson,vocabularyId:vocab,rating});
      flashFlipped=false;
      if(context!=='practice')flashIndex=(flashIndex+1)%activeLesson.vocabulary.length;
      await render();toast('Review scheduled.');document.querySelector('.flashcard')?.focus({preventScroll:true});
    }
    if(action==='section-done'){
      B.state.progress[activeLesson.id]=await api('/api/progress',{lessonId:activeLesson.id,section:target.dataset.section,mark:true});
      if(target.dataset.section===target.dataset.next)await render();else location.hash=href(activeLesson.id,target.dataset.next);
    }
    if(action==='discard-draft'){clearTimeout(saveTimers.get(target.dataset.task));removeDraft(target.dataset.task);await render();toast('Recovered browser draft discarded. Your server-saved version is kept.');}
    if(action==='model'){
      const {task,lesson}=target.dataset;
      const textarea=document.querySelector('#response-'+task);
      if(textarea){clearTimeout(saveTimers.get(task));await saveResponse(lesson,task,textarea.value,false,false);}
      const result=await api('/api/model',{lessonId:lesson,taskId:task});
      document.querySelector('[data-model-for="'+task+'"]').innerHTML='<div class="model-output"><div class="eyebrow">ONE POSSIBLE RESPONSE · NEWLY AUTHORED</div><p class="zh" lang="zh">'+esc(result.model)+'</p><small>'+esc(result.notice)+'</small></div>';
    }
  }catch(e){toast(e.message,true);}finally{if(target.isConnected)target.disabled=false;}
});

document.addEventListener('submit',async e=>{
  const form=e.target.closest('[data-form]');if(!form)return;
  e.preventDefault();
  const submitter=e.submitter;
  if(submitter)submitter.disabled=true;
  try{
    const kind=form.dataset.form,fd=new FormData(form);
    if(kind.startsWith('visual-')){await visualSubmit(kind,form,fd,dailyContext(),submitter);return;}
    if(['learn-recommend','learn-assess'].includes(kind)){await teacherDailySubmit(kind,form,fd,dailyContext());return;}
    if(kind.startsWith('learn-')){await dailySubmit(kind,form,fd,dailyContext(),submitter);return;}
    if(kind.startsWith('teacher')||['verify-slide','assessment','edit-lesson','upload-source'].includes(kind)){await teacherSubmit(kind,form,fd,{B,refresh,render,lessonCache});return;}
    if(kind==='question'){
      const a=await api('/api/attempt',{lessonId:form.dataset.lesson,questionId:form.dataset.question,answer:fd.get('answer')});
      B.state.attempts.push(a);if(a.correct)celebrate(a.xpEarned,'You’ve got it!');
      form.querySelector('.answer-feedback').innerHTML=feedbackHtml(a);
      form.querySelector('[data-attempt-status]').textContent='Latest attempt: '+(a.correct?'correct':'needs review');
      form.querySelector('button[type="submit"]').textContent='Check again';
      if(a.correct&&route()[0]==='practice'&&route()[1]==='mistakes'&&form.isConnected){
        resolvedMistake={prompt:form.querySelector('h3').textContent,attempt:a};
        await render();
      }
    }
    if(kind==='response'){
      clearTimeout(saveTimers.get(form.dataset.task));
      await saveResponse(form.dataset.lesson,form.dataset.task,fd.get('text'),submitter?.value==='submit',true);
    }
    if(kind==='reflection'){
      const complete=submitter?.value==='complete';
      B.state.progress[form.dataset.lesson]=await api('/api/progress',{lessonId:form.dataset.lesson,section:'reflection',reflection:fd.get('reflection'),complete,mark:complete});
      if(complete){await refresh();await render();toast('Lesson completed. Your reflection is saved.');}
      else{form.querySelector('.reflection-feedback').innerHTML=notice('Reflection saved.');toast('Reflection saved.');}
    }
  }catch(error){
    const slot=form.querySelector('.answer-feedback,.reflection-feedback,.form-errors');
    if(slot)slot.innerHTML=errorView(error);
    toast(error.message,true);
  }finally{if(submitter?.isConnected)submitter.disabled=false;}
});

window.addEventListener('hashchange',async()=>{
  const previous=currentRoute;currentRoute=location.hash;
  try{
    await refresh();
    const r=route();
    if(r[0]==='lesson'&&r[1]){
      const l=allLessons().find(l=>l.id===r[1]);
      if(l&&canLearn(l))B.state.progress[l.id]=await api('/api/progress',{lessonId:l.id,section:sectionNames[r[2]]?r[2]:'overview'});
    }
  }catch(e){toast(e.message,true);}
  await render(previous!==currentRoute);
});

window.addEventListener('beforeunload',()=>{document.querySelectorAll('.response-box').forEach(el=>putDraft(el.dataset.task,el.value));});
currentRoute=location.hash;
await render();
if(route()[0]==='lesson'&&activeLesson&&canLearn(activeLesson)){
  try{B.state.progress[activeLesson.id]=await api('/api/progress',{lessonId:activeLesson.id,section:route()[2]||'overview'});}catch(e){toast(e.message,true);}
}

// Missing assets retain a meaningful alternative and never masquerade as a valid picture.
document.addEventListener('error',e=>{const image=e.target;if(image?.tagName!=='IMG')return;const figure=image.closest('.learning-image');if(!figure)return;const fallback=document.createElement('div');fallback.className='image-unavailable';fallback.setAttribute('role','img');fallback.setAttribute('aria-label',image.alt||'Teaching image unavailable');fallback.textContent='Image unavailable. Use the source context or ask your teacher to check the image reference.';image.replaceWith(fallback);},true);
