import {api,esc,icon,sourceRefs,date,empty,toast} from './lib.js?v=68969ca6a5a3';
import {registerPronunciation} from './pronunciation.js?v=68969ca6a5a3';
import {encouragement,celebrate} from './rewards.js?v=68969ca6a5a3';
import {prepareVisual,vocabularyPicture} from './visual.js?v=68969ca6a5a3';
let DATA,flipped=false,reviewNotice='';
const storageKey='atelier-all-vocabulary-v1';
let prefs={lesson:'all',mode:'all',query:'',direction:'chinese',currentId:''};
try{prefs={...prefs,...JSON.parse(localStorage.getItem(storageKey)||'{}')};}catch{}
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(prefs));}catch{}}
const seen=v=>!!v.record?.lastReviewedAt;
const due=v=>seen(v)&&new Date(v.record.nextReviewAt)<=new Date();
const support=v=>v.record?.mastery==='relearning'||['again','hard'].includes(v.record?.lastRating);
export function filterVocabulary(items,options){
 const query=options.query.trim().toLowerCase();
 return items.filter(v=>(options.lesson==='all'||v.lessonId===options.lesson)&&(!query||(v.chinese+' '+v.pinyin+' '+v.meaning+' '+(v.gloss?.th||'')).toLowerCase().includes(query))&&(options.mode==='all'||options.mode==='new'&&!seen(v)||options.mode==='due'&&due(v)||options.mode==='support'&&support(v)||options.mode==='mastered'&&v.record?.mastery==='mastered'||options.mode==='learning'&&seen(v)&&v.record.mastery!=='mastered'));
}
export async function flashcardsView(){
 DATA=await api('/api/learning/vocabulary');registerPronunciation({vocabulary:DATA.items});
 let imagesReady=true;try{await prepareVisual();}catch{imagesReady=false;}
 if(!DATA.lessons.some(l=>l.id===prefs.lesson)&&prefs.lesson!=='all')prefs.lesson='all';
 if(!['all','new','due','support','learning','mastered'].includes(prefs.mode))prefs.mode='all';
 if(typeof prefs.query!=='string')prefs.query='';
 if(!['chinese','meaning'].includes(prefs.direction))prefs.direction='chinese';
 const deck=filterVocabulary(DATA.items,prefs);let index=Math.max(0,deck.findIndex(v=>v.id===prefs.currentId));const v=deck[index];
 if(v){prefs.currentId=v.id;persist();}
 const reviewed=DATA.items.filter(seen).length,mastered=DATA.items.filter(v=>v.record?.mastery==='mastered').length;
 const status=v?.record?.mastery==='mastered'?'Spaced recall milestone':v&&support(v)?'Needs another look':v&&seen(v)?'Learning':'New to your review history';
 return '<div class="page-intro"><div><div class="eyebrow">ALL 20 LESSONS · '+DATA.total+' SOURCE VOCABULARY RECORDS</div><h1>Every word, within reach.</h1><p>Emmalyne’s complete vocabulary deck. Choose any lesson, recall actively, then compare and rate honestly.</p></div></div>'+
 '<div class="vocabulary-stats"><div><strong>'+reviewed+' / '+DATA.total+'</strong><span>reviewed at least once</span></div><div><strong>'+DATA.items.filter(due).length+'</strong><span>due now</span></div><div><strong>'+DATA.items.filter(support).length+'</strong><span>need support</span></div><div><strong>'+mastered+'</strong><span>spaced recall milestones</span></div></div><progress class="vocabulary-coverage" max="'+DATA.total+'" value="'+reviewed+'" aria-label="Vocabulary review coverage"></progress>'+
 '<form class="vocabulary-filters" data-form="vocabulary-filter"><label>Lesson<select name="lesson">'+[['all','All 20 lessons'],...DATA.lessons.map(l=>[l.id,'Lesson '+l.number+' · '+l.title+' ('+l.count+')'])].map(([value,label])=>'<option value="'+value+'" '+(prefs.lesson===value?'selected':'')+'>'+esc(label)+'</option>').join('')+'</select></label><label>Review set<select name="mode">'+[['all','Every expression'],['new','Not reviewed yet'],['due','Due now'],['support','Needs support'],['learning','Learning'],['mastered','Spaced recall milestones']].map(([value,label])=>'<option value="'+value+'" '+(prefs.mode===value?'selected':'')+'>'+label+'</option>').join('')+'</select></label><label>Recall direction<select name="direction"><option value="chinese" '+(prefs.direction==='chinese'?'selected':'')+'>Chinese → meaning</option><option value="meaning" '+(prefs.direction==='meaning'?'selected':'')+'>Meaning → Chinese</option></select></label><label>Find an expression<input name="query" type="search" value="'+esc(prefs.query)+'" placeholder="Chinese, pinyin or English"></label><button class="button secondary" type="submit">Apply filters</button></form>'+
 (reviewNotice?'<div class="notice" role="status">'+esc(reviewNotice)+'</div>':'')+
 (v?'<section class="content-card complete-vocab-card" aria-label="Vocabulary flashcard"><div class="origin-row"><span class="tag">LESSON '+v.lessonNumber+'</span><span class="tag">'+status+'</span>'+sourceRefs(v)+'</div><p class="small muted">Card '+(index+1)+' of '+deck.length+' in this set · '+esc(v.lessonTitle)+'</p><div class="vocabulary-prompt"><span class="eyebrow">'+(prefs.direction==='meaning'?'RECALL THE CHINESE':'RECALL A MEANING AND A USE')+'</span><h2 lang="'+(prefs.direction==='meaning'?'en':'zh')+'">'+esc(prefs.direction==='meaning'?v.meaning:v.chinese)+'</h2></div>'+
 (!flipped?'<p class="small muted">Try recalling before revealing. Reading a word is different from retrieving its meaning or producing it yourself.</p><button class="button" data-action="vocabulary-reveal">Reveal & compare</button>':'<div class="vocabulary-answer" role="status">'+(imagesReady?vocabularyPicture(v):'<p class="small muted">Source pictures are unavailable. Your text card and review still work.</p>')+'<h3 lang="zh">'+esc(v.chinese)+'</h3><p class="meaning">'+esc(v.meaning)+'</p>'+(v.gloss?.th?'<p lang="th">'+esc(v.gloss.th)+'</p>':'')+'<p class="zh" lang="zh">'+esc(v.example)+'</p><small>'+(v.exampleOrigin==='textbook'?'Source example':'Supplementary example')+'</small><p class="small muted">Tap a Chinese word for pinyin. Recall is self-rated; a teacher checks meaningful use.</p></div><div class="rating-grid">'+[['again','Again','Could not recall'],['hard','Hard','Needed a clue'],['good','Good','Recalled independently'],['easy','Easy','Recalled with a useful context']].map(([rating,label,hint])=>'<button class="button '+(rating==='good'?'':'secondary')+'" data-action="vocabulary-rate" data-rating="'+rating+'" data-word="'+v.id+'">'+label+'<small>'+hint+'</small></button>').join('')+'</div>')+
 '<div class="vocabulary-card-nav"><button class="text-link" data-action="vocabulary-previous" '+(index===0?'disabled':'')+'>← Previous</button><span class="small muted">'+(v.record?.lastReviewedAt?'Next scheduled review: '+date(v.record.nextReviewAt):'Revealing alone does not mark this word reviewed.')+'</span><button class="text-link" data-action="vocabulary-next">'+(index===deck.length-1?'Return to first card':'Next expression')+' →</button></div></section>':empty('No expressions in this set','Change the filters to review more words. Every source expression remains available.'))+
 '<p class="quiet-note">A spaced recall milestone requires at least five successful scheduled self-ratings and a 30+ day interval. It does not certify language mastery. Use the <a href="#/review">Review Centre</a> for typed retrieval and source-based checks. Early practice does not shorten or extend your existing schedule, and does not earn XP.</p>'+
 '<details class="content-card"><summary>All 20 lessons · check your coverage</summary><div class="vocabulary-lessons">'+DATA.lessons.map(l=>{const words=DATA.items.filter(v=>v.lessonId===l.id),n=words.filter(seen).length;return '<button class="vocabulary-lesson" data-action="vocabulary-lesson" data-lesson="'+l.id+'"><span>LESSON '+l.number+'</span><strong lang="zh">'+esc(l.title)+'</strong><small>'+n+' / '+l.count+' reviewed</small><progress max="'+l.count+'" value="'+n+'" aria-label="Lesson '+l.number+' vocabulary coverage"></progress></button>';}).join('')+'</div></details><details class="content-card"><summary>Browse '+deck.length+' expressions in this set</summary><div class="vocabulary-word-list">'+deck.map(word=>'<button class="button secondary small" data-action="vocabulary-open" data-word="'+word.id+'"><span lang="zh">'+esc(word.chinese)+'</span><small>L'+word.lessonNumber+' · '+(seen(word)?support(word)?'needs support':'reviewed':'new')+'</small></button>').join('')+'</div></details>';
}
export async function flashcardsEvent(action,target,ctx){
 const deck=filterVocabulary(DATA.items,prefs),index=Math.max(0,deck.findIndex(v=>v.id===prefs.currentId));
 if(action==='vocabulary-reveal'){flipped=true;await ctx.render();return;}
 if(action==='vocabulary-lesson'){prefs.lesson=target.dataset.lesson;prefs.mode='all';prefs.query='';prefs.currentId='';}
 if(action==='vocabulary-open')prefs.currentId=target.dataset.word;
 if(action==='vocabulary-next'||action==='vocabulary-previous')prefs.currentId=deck[(index+(action==='vocabulary-next'?1:deck.length-1))%deck.length]?.id||'';
 if(action==='vocabulary-rate'){
  if(!flipped)throw new Error('Recall first, then reveal and compare before rating.');
  const word=DATA.items.find(v=>v.id===target.dataset.word);if(!word)throw new Error('Expression not found. Reload the vocabulary deck.');
  const early=word.record?.lastReviewedAt&&new Date(word.record.nextReviewAt)>new Date();
  const result=await api('/api/review',{lessonId:word.lessonId,vocabularyId:word.id,rating:target.dataset.rating});
  prefs.currentId=deck[(index+1)%deck.length]?.id||'';
  reviewNotice=encouragement('review')+' '+(early?'Early practice saved; your existing date stays the same.':'Next review: '+date(result.dueAt)+'.');
  await ctx.refresh();celebrate(0,target.dataset.rating==='again'?'A useful word to meet again. Keep going, Emmalyne.':'Another expression revisited. Your effort counts.');
 }
 flipped=false;persist();await ctx.render();
}
export async function flashcardsSubmit(form,fd,ctx){
 prefs={...prefs,...Object.fromEntries(fd),currentId:''};flipped=false;reviewNotice='';persist();await ctx.render();
}
