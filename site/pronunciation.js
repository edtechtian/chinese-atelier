import {pinyin,customPinyin} from './pinyin-engine.js?v=1f592a6fd73d';

// Hospitality contexts where the general dictionary needs an explicit reading.
customPinyin({'还给':'huán gěi','归还':'guī huán','退还':'tuì huán','还房卡':'huán fáng kǎ','还钥匙':'huán yào shi','还钱':'huán qián','还书':'huán shū','同行的游客':'tóng xíng de yóu kè','同行的客人':'tóng xíng de kè rén','同行的人':'tóng xíng de rén','与您同行':'yǔ nín tóng xíng','同行旅客':'tóng xíng lǚ kè'});

// All pronunciation is computed on this device. Source vocabulary takes priority.
const sourceReadings=new Map();
const chinese=/\p{Script=Han}/u;
const phrases=/\p{Script=Han}+(?:[\s，。！？；：、“”‘’（）《》〈〉…—·,.!?;:0-9０-９%％+-]+\p{Script=Han}+)*[，。！？；：、]?/gu;
const skip='script,style,textarea,input,select,option,code,[contenteditable],.pinyin,.pinyin-reading,.source-key,.brand-mark,[data-no-pinyin],[data-hanzi]';
let panel,active,observer,serial=0;

export function registerPronunciation(lesson){
 for(const v of lesson?.vocabulary||[])if(v.chinese&&v.pinyin)sourceReadings.set(v.chinese.trim(),v.pinyin.trim());
}
export function pronunciation(text){
 const exact=sourceReadings.get(text.trim());
 return {text:exact||pinyin(text,{toneType:'symbol',toneSandhi:false,nonZh:'consecutive'}),source:exact?'Source vocabulary pronunciation':'Automatic pronunciation support · check unfamiliar names with your teacher'};
}
function close(){
 if(active?.isConnected&&active.matches('[role="button"]'))active.setAttribute('aria-expanded','false');
 if(panel)panel.hidden=true;active=null;
}
function show(target,text){
 if(target===active&&!panel.hidden){close();return;}
 close();active=target;
 const reading=pronunciation(text);
 panel.querySelector('.pinyin-original').textContent=text;
 panel.querySelector('.pinyin-reading').textContent=reading.text;
 panel.querySelector('.pinyin-source').textContent=reading.source;
 panel.hidden=false;
 if(target.matches('[role="button"]'))target.setAttribute('aria-expanded','true');
}
export function enhanceChinese(root){
 if(!root||root.nodeType!==1||root.closest(skip)||!root.closest('#main'))return;
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:node=>chinese.test(node.textContent)&&!node.parentElement.closest(skip)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT});
 const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
 for(const node of nodes){
  const text=node.textContent,fragment=document.createDocumentFragment();let end=0;
  for(const match of text.matchAll(phrases)){
   fragment.append(text.slice(end,match.index));
   const el=document.createElement('span');el.className='hanzi-tap';el.dataset.hanzi=match[0];el.lang='zh';el.textContent=match[0];
   const control=node.parentElement.closest('a,button,label,summary');
   if(!control){el.tabIndex=0;el.setAttribute('role','button');el.setAttribute('aria-expanded','false');el.setAttribute('aria-controls','pinyin-panel');el.setAttribute('aria-label','Show pinyin: '+match[0]);}
   else{
    // Keep native controls valid: no nested buttons or extra tab stops.
    const keyboard=control.tagName==='LABEL'?control.control||control:control;
    keyboard.setAttribute('aria-keyshortcuts','Alt+P');
   }
   el.title='Tap for pinyin · Alt+P on a focused card or answer';fragment.append(el);end=match.index+match[0].length;
  }
  fragment.append(text.slice(end));node.replaceWith(fragment);
 }
 // Native select options cannot contain HTML. Offer the same support beside them.
 const selects=[...(root.matches('select')?[root]:[]),...root.querySelectorAll('select')];
 for(const select of selects){
  if(select.dataset.pinyinSupport||!Array.from(select.options).some(o=>chinese.test(o.text)))continue;
  select.dataset.pinyinSupport='1';select.id||=("pinyin-select-"+(++serial));
  const button=document.createElement('button');button.type='button';button.className='pinyin-select-button';button.dataset.pinyinSelect=select.id;button.textContent='Pinyin for Chinese options';select.after(button);
 }
}
export function installPronunciation(){
 panel=document.createElement('aside');panel.id='pinyin-panel';panel.className='pinyin-panel';panel.hidden=true;panel.setAttribute('aria-label','Optional pinyin');panel.setAttribute('aria-live','polite');
 panel.innerHTML='<button type="button" class="pinyin-close" aria-label="Close pinyin">×</button><strong class="pinyin-original" lang="zh"></strong><p class="pinyin-reading" lang="zh-Latn"></p><small class="pinyin-source"></small>';
 document.body.append(panel);
 document.addEventListener('click',e=>{
  if(e.target.closest('.pinyin-close')){const previous=active;close();previous?.focus?.({preventScroll:true});return;}
  const target=e.target.closest('[data-hanzi]'),selectButton=e.target.closest('[data-pinyin-select]');
  if(target){e.preventDefault();e.stopImmediatePropagation();show(target,target.dataset.hanzi);}
  else if(selectButton){e.preventDefault();e.stopImmediatePropagation();const select=document.getElementById(selectButton.dataset.pinyinSelect);show(selectButton,Array.from(select.options).filter(o=>chinese.test(o.text)).map(o=>o.text).join('\n'));}
  else if(!panel.contains(e.target))close();
 },true);
 document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){const previous=active;close();previous?.focus?.({preventScroll:true});return;}
  const standalone=e.target.closest('[data-hanzi][role="button"]');
  const target=e.altKey&&e.key.toLowerCase()==='p'?(standalone||e.target.closest('label')?.querySelector('[data-hanzi]')||e.target.querySelector('[data-hanzi]')):standalone;
  if(target&&((e.altKey&&e.key.toLowerCase()==='p')||e.key==='Enter'||e.key===' ')){e.preventDefault();e.stopImmediatePropagation();show(target,target.dataset.hanzi);}
 },true);
 window.addEventListener('hashchange',close);
 observer=new MutationObserver(records=>{
  const roots=new Set();for(const record of records)for(const node of record.addedNodes){const el=node.nodeType===1?node:node.parentElement;if(el?.closest('#main'))roots.add(el);else if(el?.querySelector?.('#main'))roots.add(el.querySelector('#main'));}
  for(const root of roots)enhanceChinese(root);
 });
 observer.observe(document.getElementById('app'),{childList:true,subtree:true});
 enhanceChinese(document.getElementById('main'));
}
