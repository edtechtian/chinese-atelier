import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {chineseWords,registerPronunciation} from '../public/pronunciation.js';
import {translationKey,findTranslation} from '../public/translation.js';
import {filterVocabulary} from '../public/flashcards.js';
const root=new URL('../',import.meta.url);
const curriculum=JSON.parse(fs.readFileSync(new URL('data/curriculum.json',root)));
const words=curriculum.lessons.flatMap(l=>l.vocabulary.map(v=>({...v,lessonId:l.id,lessonNumber:l.number,lessonTitle:l.originalTitle,record:null})));
for(const lesson of curriculum.lessons)registerPronunciation(lesson);
assert.deepEqual(chineseWords('请把房卡还给前台。').map(w=>w.text),['请','把','房卡','还给','前台','。']);
assert.equal(chineseWords('同行的游客')[0].pinyin,'tóng xíng');
for(const word of words){
 const segmented=chineseWords(word.chinese);assert.equal(segmented.map(w=>w.text).join(''),word.chinese);
 assert.ok(segmented.filter(w=>/\p{Script=Han}/u.test(w.text)).every(w=>w.pinyin),word.id);
}
const data=JSON.parse(fs.readFileSync(new URL('public/language-support.json',root)));
const entries=new Map(data.entries.map(e=>[translationKey(e.chinese),e]));
assert.equal(entries.size,data.entries.length);
assert.ok(data.entries.every(e=>e.en&&e.th&&e.origin));
for(const text of ['我们不可以穿鞋进佛殿。','请不要在图书馆吃东西。','欢迎光临，请问您有预订吗？']){
 const found=findTranslation(text,entries);assert.ok(found?.en&&found?.th,text);assert.equal(found.expanded,false);
}
const fixtures=new Map([['您好欢迎光临',{chinese:'您好，欢迎光临。',en:'Hello, welcome.',th:'สวัสดี ยินดีต้อนรับ'}],['请收好房卡',{chinese:'请收好房卡。',en:'Keep your key card safe.',th:'กรุณาเก็บคีย์การ์ดให้ดี'}]]);
assert.equal(findTranslation('您好，欢迎光临。请收好房卡。',fixtures).en,'Hello, welcome.\nKeep your key card safe.');
assert.equal(findTranslation('您好欢迎',fixtures).expanded,true);
assert.equal(findTranslation('这是没有存储的新句子',entries),null);
const defaults={lesson:'all',mode:'all',query:''};
assert.equal(filterVocabulary(words,defaults).length,268);
for(const lesson of curriculum.lessons)assert.equal(filterVocabulary(words,{...defaults,lesson:lesson.id}).length,lesson.vocabulary.length);
assert.ok(filterVocabulary(words,{...defaults,query:'房卡'}).every(w=>w.chinese.includes('房卡')));
assert.equal(filterVocabulary(words,{...defaults,mode:'new'}).length,268);
const cases=words.slice(0,4).map((w,i)=>({...w,record:i===0?null:{lastReviewedAt:'2020-01-01',nextReviewAt:i===1?'2020-01-02':'2099-01-01',mastery:i===2?'mastered':'learning',lastRating:i===3?'again':'good'}}));
for(const [mode,n] of [['new',1],['due',1],['support',1],['mastered',1],['learning',2]])assert.equal(filterVocabulary(cases,{...defaults,mode}).length,n,mode);
// Render and operate the actual deck using isolated review/network fixtures.
let cache={},ratings=[];
const box={api:async(path,body)=>{if(path==='/api/learning/vocabulary')return {items:words,lessons:curriculum.lessons.map(l=>({id:l.id,number:l.number,title:l.originalTitle,count:l.vocabulary.length})),total:268};ratings.push(body);return {dueAt:'2099-01-01'};},esc:v=>String(v??''),icon:()=>'',sourceRefs:v=>v.sourceRefs.join(','),date:x=>x,empty:(t,d)=>t+d,toast:()=>{},registerPronunciation:()=>{},prepareVisual:async()=>{},vocabularyPicture:()=>'<figure>Original PPT image</figure>',encouragement:()=> 'Keep going.',celebrate:()=>{},localStorage:{getItem:k=>cache[k],setItem:(k,v)=>cache[k]=v}};
vm.createContext(box);
const source=fs.readFileSync(new URL('public/flashcards.js',root),'utf8').replace(/^import .*;\n/gm,'').replaceAll('export async function','async function').replaceAll('export function','function');
vm.runInContext(source+'\nthis.deck={flashcardsView,flashcardsEvent,flashcardsSubmit};',box);
const ctx={render:async()=>{},refresh:async()=>{}};
let html=await box.deck.flashcardsView();assert.ok(html.includes('268 SOURCE VOCABULARY RECORDS'));assert.ok(!html.includes('vocabulary-rate'));
await assert.rejects(()=>box.deck.flashcardsEvent('vocabulary-rate',{dataset:{word:words[0].id,rating:'good'}},ctx),/reveal/);
await box.deck.flashcardsEvent('vocabulary-reveal',{},ctx);html=await box.deck.flashcardsView();assert.ok(html.includes('vocabulary-rate'));assert.ok(html.includes('Original PPT image'));
await box.deck.flashcardsEvent('vocabulary-rate',{dataset:{word:words[0].id,rating:'good'}},ctx);assert.equal(ratings[0].vocabularyId,words[0].id);assert.equal(JSON.parse(cache['atelier-all-vocabulary-v1']).currentId,words[1].id);
await box.deck.flashcardsSubmit(null,new Map(Object.entries({...defaults,lesson:'zt-20',direction:'meaning'})),ctx);html=await box.deck.flashcardsView();assert.ok(html.includes('RECALL THE CHINESE'));assert.ok(html.includes('LESSON 20'));
console.log('Vocabulary support checks passed: 268 records, 20 lesson filters, both recall directions, reveal gate, ratings, preference persistence, phrase segmentation and bilingual selection matching.');
