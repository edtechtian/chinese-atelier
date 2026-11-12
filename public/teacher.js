import {teacherVisualPanel} from './visual.js';
import {teacherLearningView} from './daily.js';
import {api,esc,icon,notice,empty,date,toast,errorView,download} from './lib.js';
let T=null;
const tag=(text,c='')=>'<span class="tag '+c+'">'+esc(text)+'</span>';
const teacherHref=(tab,id='')=>'/teacher#/teacher/'+tab+(id?'/'+id:'');
const all=()=>T.curriculum.lessons.concat(T.curriculum.supplementary);

function header(title,text,actions=''){
  return '<div class="page-intro"><div><div class="eyebrow">TEACHER WORKSPACE · EMMALYNE</div><h1>'+esc(title)+'</h1><p>'+esc(text)+'</p></div><div class="button-row">'+actions+'<button class="text-link" data-action="teacher-logout">Lock teacher desk '+icon('lock')+'</button></div></div>';
}

function login(){
  return '<section class="teacher-login"><span class="brand-mark">师</span><div class="eyebrow">PRIVATE LOCAL ACCESS</div><h1>A space for her teacher.</h1><p>Review Emmalyne’s work, verify the original sources, and shape the next steps.</p><form data-form="teacher-login"><label class="field-label" for="teacher-key">Local teacher key</label><input id="teacher-key" name="key" type="password" autocomplete="current-password" required placeholder="Enter your teacher key"><button class="button" type="submit">Open teacher desk '+icon('arrow')+'</button><div class="form-errors" aria-live="polite"></div></form><p class="login-hint">The server terminal prints the key when it starts. It is also stored privately in <code>data/teacher-key</code>. Student pages do not contain teacher editing controls.</p><a class="text-link" href="/#/home">Return to Emmalyne’s journal</a></section>';
}

function tabs(tab){
  return '<nav class="teacher-tabs" aria-label="Teacher sections">'+[['learning','Daily learning'],['overview','Overview'],['sources','Source collection'],['content','Curriculum editor'],['work','Student work'],['insights','Learning signals']].map(([id,t])=>'<a href="'+teacherHref(id)+'" class="'+(tab===id?'active':'')+'">'+t+'</a>').join('')+'</nav>';
}

function overview(){
  const c=T.curriculum,s=T.state;
  const imported=c.lessons.filter(l=>l.sourceSlides.length).length;
  const verified=c.lessons.reduce((n,l)=>n+l.sourceSlides.filter(s=>s.reviewStatus==='verified').length,0);
  const submitted=Object.values(s.responses).filter(r=>r.submitted&&!r.teacherReview).length;
  const complete=c.lessons.filter(l=>s.progress[l.id]?.completed).length;
  return '<div class="stats-grid"><div class="stat"><div class="stat-top">Verified source inventory '+icon('folder')+'</div><div class="stat-value">'+imported+' <small>/ 20 files</small></div><div class="stat-caption">'+c.fileInventory.length+' actual files inventoried</div></div><div class="stat"><div class="stat-top">Source slide checks '+icon('check')+'</div><div class="stat-value">'+verified+' <small>/ '+c.lessons.reduce((n,l)=>n+l.sourceSlides.length,0)+'</small></div><div class="stat-caption">Teacher verification, separate from extraction</div></div><div class="stat"><div class="stat-top">Review queue '+icon('portfolio')+'</div><div class="stat-value">'+submitted+'</div><div class="stat-caption">Submitted responses awaiting your feedback</div></div><div class="stat"><div class="stat-top">Student course progress '+icon('book')+'</div><div class="stat-value">'+complete+' <small>/ 20</small></div><div class="stat-caption">Studio workshops tracked separately</div></div></div>'+notice(esc(c.attribution.notice),'warning')+'<div class="dashboard-columns"><section class="panel"><div class="section-heading"><h2>The next teaching decisions</h2></div><ol><li>Review slide 12 of lesson 7: it has fruit images but no selectable text.</li><li>Check cultural generalizations, old prices, travel times, festival permissions and site rules against context before real-world use.</li><li>Inspect the vocabulary glosses, English grammar explanations and newly authored activities before marking a lesson teacher-approved.</li><li>Use the criteria selected for each task. Across the course, six assessment dimensions are available. Automated writing checks count characters and prompt reflection.</li></ol><div class="button-row"><a class="button" href="'+teacherHref('sources','zt-07')+'">Review source slides '+icon('arrow')+'</a><a class="button secondary" href="'+teacherHref('work')+'">Student work</a></div></section><section class="panel"><h3>Private, portable data</h3><p class="quiet-note">The app runs on this computer. Source files, progress and writing are saved locally; no paid API or cloud service is involved.</p><button class="button secondary small" data-action="teacher-export" data-format="json">'+icon('download')+' Export curriculum & portfolio</button><p class="small muted">Exports contain student work. Keep them private. Backups of curriculum edits are saved in data/backups.</p><h3>Dataset checks</h3>'+(T.validation.length?notice(T.validation.map(esc).join('<br>'),'error'):'<p class="small">'+icon('check')+' 20 lesson numbers in order. Stable identifiers, reference integrity and exercise keys validated.</p>')+'</section></div><div class="section-bottom"></div><h2>Learning journey</h2>'+progressTable();
}

function progressTable(){
  return '<div class="table-wrap"><table><thead><tr><th>Lesson</th><th>Status</th><th>Sections</th><th>Latest practice</th><th>Written work</th><th>Last activity</th></tr></thead><tbody>'+all().map(l=>{
    const p=T.state.progress[l.id],attempts=T.state.attempts.filter(a=>a.lessonId===l.id),latest=Object.values(attempts.reduce((a,v)=>{a[v.questionId]=v;return a;},{})),work=Object.values(T.state.responses).filter(r=>r.lessonId===l.id);
    return '<tr><td><a class="text-link" href="'+teacherHref('content',l.id)+'">'+(l.number?String(l.number).padStart(2,'0')+' · ':'Studio · ')+esc(l.title)+'</a></td><td>'+tag(p?.completed?'Completed':p?'Started':'Not started',p?.completed?'verified':'gray')+'</td><td>'+(p?.sections.length||0)+' / 8</td><td>'+(latest.length?latest.filter(a=>a.correct).length+' / '+latest.length+' correct':'No attempts')+'</td><td>'+work.filter(r=>r.submitted).length+' submitted</td><td>'+date(p?.updatedAt)+'</td></tr>';
  }).join('')+'</tbody></table></div>';
}

function lessonList(tab,current){
  return '<nav class="teacher-lesson-list" aria-label="Choose a lesson">'+all().filter(l=>tab!=='sources'||l.kind==='textbook').map(l=>'<a class="'+(l.id===current?'active':'')+'" href="'+teacherHref(tab,l.id)+'"><span class="num">'+(l.number?String(l.number).padStart(2,'0'):'＋')+'</span><span>'+esc(l.title)+'</span></a>').join('')+'</nav>';
}

function sources(id,slideView){
  const c=T.curriculum;
  const inventory='<div class="section-heading"><div><h2>Twenty original lessons, accounted for.</h2><p>File hashes detect exact duplicates. Extraction status does not imply teacher verification.</p></div></div><div class="table-wrap"><table><thead><tr><th>No.</th><th>Original filename</th><th>Size</th><th>Slides</th><th>Processing status</th><th>Review</th></tr></thead><tbody>'+c.lessons.map(l=>{
    const f=c.fileInventory.find(f=>l.processing.files.includes(f.id));
    return '<tr><td>'+l.number+'</td><td>'+(f?'<a class="text-link" href="/source-file/'+esc(f.storedName)+'">'+esc(f.filename)+icon('download')+'</a><div class="source-key">SHA-256: '+esc(f.sha256.slice(0,18))+'…</div>':'Not supplied')+'</td><td>'+(f?(f.bytes/1024/1024).toFixed(1)+' MB':'—')+'</td><td>'+l.sourceSlides.length+'</td><td>'+tag(l.processing.status,'warm')+'</td><td><a class="text-link" href="'+teacherHref('sources',l.id)+'">'+l.sourceSlides.filter(s=>s.reviewStatus==='verified').length+' / '+l.sourceSlides.length+' checked</a></td></tr>';
  }).join('')+'</tbody></table></div>';
  const lesson=c.lessons.find(l=>l.id===id);
  return inventory+'<div class="section-bottom"></div>'+(lesson?'<div class="teacher-two">'+lessonList('sources',id)+'<section><div class="eyebrow">ORIGINAL MATERIAL · LESSON '+lesson.number+'</div><h2 lang="zh">'+esc(lesson.originalTitle||lesson.title)+'</h2>'+notice('Compare text and visual meaning with the original PPT. Mark verified only after checking. The app preserves original content rather than silently correcting it.','warning')+lesson.sourceSlides.map(s=>slideView(s,lesson,true)).join('')+'</section></div>':'<div class="content-card"><h3>Open a lesson to verify its slides</h3><p>Use the review count in the table to open the slide gallery. Check images, maps, diagrams, source exercises and displayed answer keys, then add teacher notes.</p></div>')+'<details class="content-card"><summary>Add a missing original source</summary><p class="small muted">PPTX extraction is built in. Legacy PPT requires LibreOffice. Files are kept locally; duplicate files and replacing existing sources are blocked to protect references. Maximum file size: 100 MB.</p><form data-form="upload-source"><label class="field-label" for="source-number">Original lesson number</label><select id="source-number" name="number">'+c.lessons.map(l=>'<option value="'+l.number+'">Lesson '+l.number+' · '+esc(l.title)+'</option>').join('')+'</select><label class="field-label" for="source-file">Original PPT or PPTX</label><input class="file-input" type="file" id="source-file" name="file" accept=".ppt,.pptx" required><button class="button secondary" type="submit">Inventory & extract source</button><div class="form-errors" aria-live="polite"></div></form></details>';
}

function editable(l){const copy=structuredClone(l);delete copy.sourceSlides;delete copy.processing;return copy;}

function content(id){
  const l=all().find(l=>l.id===id)||all()[0];
  return '<div class="teacher-two">'+lessonList('content',l.id)+'<section><div class="eyebrow">'+(l.kind==='textbook'?'TEXTBOOK LESSON '+l.number:'SUPPLEMENTARY STUDIO')+'</div><h2 lang="zh">'+esc(l.title)+'</h2><div class="origin-row">'+tag(l.status)+tag(l.approval,'warm')+'</div><p class="small muted">Edit structured vocabulary, readings, language explanations, questions, exact answer keys, task models and criteria. Source slides and extraction records remain immutable; attach teacher notes in Source collection. IDs are stable and must stay unique.</p>'+notice('To publish as teacher-approved, every original slide must be verified and the required lesson fields must validate. Until then, use status “available” and approval “author_adapted_pending_teacher”.','warning')+'<form data-form="edit-lesson" data-lesson="'+l.id+'"><label class="field-label" for="lesson-json">Structured lesson content (JSON)</label><textarea id="lesson-json" class="code-editor" name="json" spellcheck="false" rows="26">'+esc(JSON.stringify(editable(l),null,2))+'</textarea><div class="writing-meta"><span id="editor-dirty">Saved content · original files unchanged</span><span>'+l.vocabulary.length+' expressions · '+l.questions.length+' questions · '+l.tasks.length+' tasks</span></div><div class="button-row"><button class="button" type="submit">'+icon('save')+' Validate & save changes</button><button class="button secondary" type="button" data-action="teacher-approve" data-lesson="'+l.id+'">Set teacher-approved status</button><a class="text-link" href="/#/lesson/'+l.id+'/overview" target="_blank" rel="noopener">Preview student lesson '+icon('arrow')+'</a></div><div class="form-errors" aria-live="polite"></div></form><p class="small muted">New teacher adaptations must cite existing slide IDs such as '+esc(l.id)+'-slide-001. Newly authored activities use origin “supplementary”. The answer key is teacher-only in this editor; source slides may include original visible answers.</p></section></div>';
}

function taskCriteria(r){return all().find(l=>l.id===r.lessonId)?.tasks.find(t=>t.id===r.taskId)?.criteria||T.curriculum.criteria.map(c=>c.id);}

function studentWork(){
  const responses=Object.values(T.state.responses).filter(r=>r.text.trim()).sort((a,b)=>(Number(b.submitted&&!b.teacherReview)-Number(a.submitted&&!a.teacherReview))||b.updatedAt.localeCompare(a.updatedAt));
  return '<div class="section-heading"><div><h2>Read the work. Respond to the person.</h2><p>Teacher levels are criterion feedback, not official IB grades. Assess speaking only from evidence you have actually heard.</p></div></div>'+(responses.length?responses.map(r=>'<article class="work-card"><div class="work-header"><div>'+tag(r.teacherReview?'Reviewed':r.submitted?'Ready for review':'Student draft',r.teacherReview?'verified':'warm')+'<h3>'+esc(r.taskTitle)+'</h3><span class="small muted">'+esc(all().find(l=>l.id===r.lessonId)?.title||r.lessonId)+' · revision '+r.revision+' · '+date(r.updatedAt)+'</span></div></div><details class="details"><summary>Task brief and model</summary><p>'+esc(all().find(l=>l.id===r.lessonId)?.tasks.find(t=>t.id===r.taskId)?.prompt||'Task was edited after submission.')+'</p><p class="zh" lang="zh">'+esc(all().find(l=>l.id===r.lessonId)?.tasks.find(t=>t.id===r.taskId)?.model||'')+'</p></details><div class="work-text zh" lang="zh">'+esc(r.text)+'</div>'+(r.submitted?'<form data-form="assessment" data-response="'+r.id+'" data-revision="'+r.revision+'"><h3>Teacher assessment · current revision</h3>'+T.curriculum.criteria.filter(c=>taskCriteria(r).includes(c.id)).map(c=>'<div class="teacher-score"><label for="'+r.id+'-'+c.id+'">'+esc(c.label)+'<small>1 emerging · 2 developing · 3 effective · 4 assured</small></label><select name="'+c.id+'" id="'+r.id+'-'+c.id+'" required><option value="">Select level</option>'+c.descriptors.map((d,i)=>'<option value="'+(i+1)+'" '+(r.teacherReview?.scores[c.id]===i+1?'selected':'')+'>'+(i+1)+' · '+esc(d)+'</option>').join('')+'</select></div>').join('')+'<label class="field-label" for="feedback-'+r.id+'">Evidence-based feedback and one practical next step</label><textarea id="feedback-'+r.id+'" name="comment" rows="4" maxlength="6000" required>'+esc(r.teacherReview?.comment||'')+'</textarea><button class="button" type="submit">Save teacher feedback '+icon('check')+'</button><div class="form-errors" aria-live="polite"></div></form>':'<p class="small muted">This is an unsubmitted draft. Wait for the student to submit before assessing.</p>')+(r.reviewHistory?.length?'<details class="details"><summary>Earlier teacher reviews</summary>'+r.reviewHistory.map(review=>'<p><strong>Revision '+review.revision+' · '+date(review.at)+'</strong><br>'+esc(review.comment)+'</p>').join('')+'</details>':'')+'</article>').join(''):empty('Original-lesson review queue','Original-lesson writing and speaking reflections appear here. Daily-learning and visual submissions have their own review sections below. Student drafts need submission before assessment.'));
}

function learningSignals(insightView){
  const latest=Object.values(T.state.attempts.reduce((a,v)=>{a[v.questionId]=v;return a;},{}));
  const missed=latest.filter(a=>!a.correct);
  const lapses=Object.values(T.state.reviews).filter(r=>r.lapses>0).sort((a,b)=>b.lapses-a.lapses);
  return insightView()+'<div class="insight-grid"><section class="panel"><h3>Questions to revisit</h3>'+(missed.length?'<ul class="activity-list">'+missed.map(a=>{
    const l=all().find(l=>l.id===a.lessonId),q=l?.questions.find(q=>q.id===a.questionId),attempts=T.state.attempts.filter(x=>x.questionId===a.questionId&&!x.correct).length;
    return '<li><div><strong>'+esc(q?.prompt||a.questionId)+'</strong><small>'+esc(l?.title)+' · '+attempts+' incorrect attempt(s) · latest '+date(a.at)+'</small><small>Expected answer: '+esc(q?.answer||q?.acceptedAnswers?.join(' / '))+'</small></div></li>';
  }).join('')+'</ul>':'<p class="quiet-note">No unresolved mistakes in the latest practice attempts.</p>')+'</section><section class="panel"><h3>Expressions needing support</h3>'+(lapses.length?'<ul class="activity-list">'+lapses.slice(0,20).map(r=>{
    const l=all().find(l=>l.id===r.lessonId),v=l?.vocabulary.find(v=>v.id===r.vocabularyId);
    return '<li><div><strong class="zh" lang="zh">'+esc(v?.chinese||r.vocabularyId)+'</strong><small>'+r.lapses+' “Again” self-rating(s) · due '+date(r.dueAt)+'</small></div></li>';
  }).join('')+'</ul>':'<p class="quiet-note">As Emmalyne self-rates vocabulary, repeated “Again” ratings will identify words that may need another approach.</p>')+'</section></div><h2>Completion and learning evidence</h2>'+progressTable();
}

export async function teacherView(B,r,slideView,insightView){
  if(!B.teacher){T=null;return login();}
  T=await api('/api/teacher');
  const tab=['learning','overview','sources','content','work','insights'].includes(r[1])?r[1]:'learning';
  const titles={learning:['A journey made visible.','100 steps, retrieval evidence and thoughtful professional communication.'],overview:['Teaching with a clearer view.','A source-aware course and a real record of Emmalyne’s learning.'],sources:['Every lesson has a source.','Inspect the original files and verify what text extraction cannot decide.'],content:['Shape the next conversation.','Correct, extend and approve the structured curriculum with traceable references.'],work:['Feedback that moves her forward.','Read drafts, assess submitted work and give a useful next step.'],insights:['Notice what needs attention.','Use practice signals and teacher evidence without turning them into unsupported proficiency claims.']};
  const actions='<button class="button secondary small" data-action="teacher-export" data-format="csv">'+icon('download')+' Progress CSV</button>';
  return header(...titles[tab],actions)+tabs(tab)+(tab==='learning'?(await teacherLearningView(B))+(await teacherVisualPanel()):({overview:()=>overview(),sources:()=>sources(r[2],slideView),content:()=>content(r[2]),work:()=>studentWork(),insights:()=>learningSignals(insightView)}[tab]())+(tab==='work'?await teacherVisualPanel():''));
}

export async function teacherEvent(action,target,ctx){
  if(action==='teacher-logout'){await api('/api/teacher/logout',{});T=null;await ctx.refresh();await ctx.render();toast('Teacher desk locked.');}
  if(action==='teacher-export')await download('/api/teacher/export?format='+target.dataset.format,'emmalyne-teacher-'+(target.dataset.format==='csv'?'progress.csv':'curriculum-portfolio.json'));
  if(action==='teacher-approve'){
    const area=document.querySelector('#lesson-json'),draft=JSON.parse(area.value);
    draft.approval='teacher_approved';draft.status='published';
    area.value=JSON.stringify(draft,null,2);
    document.querySelector('#editor-dirty').textContent='Approval fields updated · validate and save to apply';
    toast('Approval fields set. Validate & save after verifying every source slide.');
  }
}

export async function teacherSubmit(kind,form,fd,ctx){
  if(kind==='teacher-login'){
    await api('/api/teacher/login',{key:fd.get('key')});
    await ctx.refresh();await ctx.render();toast('Teacher desk opened.');return;
  }
  if(kind==='edit-lesson'){
    let edited;try{edited=JSON.parse(fd.get('json'));}catch{throw new Error('The lesson JSON has a syntax error. Your edit is still in the field; correct it and try again.');}
    const original=all().find(l=>l.id===form.dataset.lesson);
    const lesson={...edited,sourceSlides:original.sourceSlides,processing:original.processing};
    await api('/api/teacher/lesson',{lesson});
    ctx.lessonCache.delete(lesson.id);
    document.querySelector('#editor-dirty').textContent='Validated & saved';toast('Lesson validated and saved.');
    await ctx.refresh();T=null;return;
  }
  if(kind==='verify-slide'){
    const result=await api('/api/teacher/verify-slide',{lessonId:form.dataset.lesson,slideId:form.dataset.slide,notes:fd.get('notes'),verified:fd.get('verified')==='on'});
    const l=T.curriculum.lessons.find(l=>l.id===form.dataset.lesson);
    l.sourceSlides[l.sourceSlides.findIndex(s=>s.id===result.id)]=result;
    const label=form.closest('details').querySelector('summary .tag');if(label){label.textContent=result.reviewStatus==='verified'?'Teacher verified':'Review pending';label.className='tag '+(result.reviewStatus==='verified'?'verified':'warm');}
    ctx.lessonCache.delete(l.id);toast('Slide verification saved.');return;
  }
  if(kind==='assessment'){
    const scores=Object.fromEntries(T.curriculum.criteria.filter(c=>fd.has(c.id)).map(c=>[c.id,Number(fd.get(c.id))]));
    await api('/api/teacher/assessment',{responseId:form.dataset.response,revision:Number(form.dataset.revision),scores,comment:fd.get('comment')});
    await ctx.refresh();await ctx.render();toast('Teacher feedback saved. The student can see it in the portfolio.');return;
  }
  if(kind==='upload-source'){
    const file=fd.get('file');if(!file?.size)throw new Error('Select a source PowerPoint first.');
    if(file.size>100*1024*1024)throw new Error('The source is over 100 MB. Import a smaller copy or use the local command-line importer.');
    const slot=form.querySelector('.form-errors');slot.innerHTML=notice('Inventorying and extracting source slides. Large files may take a little time.');
    const r=await fetch('/api/teacher/source?lesson='+fd.get('number'),{method:'POST',credentials:'same-origin',headers:{'X-App-Request':'1','X-Filename':encodeURIComponent(file.name),'Content-Type':'application/octet-stream'},body:file});
    const result=await r.json();if(!r.ok)throw new Error(result.error);
    slot.innerHTML=notice('File retained. Status: '+esc(result.status)+'. '+esc(result.issues.join(' ')),result.status==='unreadable'?'warning':'info');
    ctx.lessonCache.clear();await ctx.refresh();T=null;toast('Source inventory updated.');
  }
}
