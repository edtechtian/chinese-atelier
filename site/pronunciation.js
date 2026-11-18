import {pinyin,customPinyin} from './pinyin-engine.js?v=68969ca6a5a3';

// Hospitality contexts where the general dictionary needs an explicit reading.
customPinyin({'还给':'huán gěi','归还':'guī huán','退还':'tuì huán','还房卡':'huán fáng kǎ','还钥匙':'huán yào shi','还钱':'huán qián','还书':'huán shū','同行的游客':'tóng xíng de yóu kè','同行的客人':'tóng xíng de kè rén','同行的人':'tóng xíng de rén','与您同行':'yǔ nín tóng xíng','同行旅客':'tóng xíng lǚ kè'});

// All pronunciation is computed on this device. Source vocabulary takes priority.
const sourceReadings=new Map();
const segmenter=new Intl.Segmenter('zh',{granularity:'word'});
const preferred=['落地签','大皇宫','佛殿','不要','请问','穿鞋','还给','孔明灯','合十','同行','佳佳','小爱','一点儿'];
const chinese=/\p{Script=Han}/u;
const skip='script,style,textarea,input,select,option,code,[contenteditable],.pinyin,.pinyin-reading,.source-key,.brand-mark,[data-no-pinyin],[data-hanzi]';
let panel,active,observer,serial=0;

export function registerPronunciation(lesson){
 for(const v of lesson?.vocabulary||[])if(v.chinese&&v.pinyin)sourceReadings.set(v.chinese.trim(),v.pinyin.trim());
}
export function pronunciation(text){
 const exact=sourceReadings.get(text.trim());
 return {text:exact||pinyin(text,{toneType:'symbol',toneSandhi:false,nonZh:'consecutive'}),source:exact?'Source vocabulary pronunciation':'Automatic pronunciation support · check unfamiliar names with your teacher'};
}
export function chineseWords(text){
 const known=[...new Set([...sourceReadings.keys(),...preferred])].filter(x=>/^\p{Script=Han}+$/u.test(x)).sort((a,b)=>b.length-a.length);
 const natural=new Map(Array.from(segmenter.segment(text),s=>[s.index,s.segment]));
 const sounds=[];let offset=0;
 for(const char of pinyin(text,{type:'all',toneType:'symbol',toneSandhi:false})){sounds.push({start:offset,end:offset+char.origin.length,reading:char.pinyin,isZh:char.isZh});offset+=char.origin.length;}
 const result=[];let start=0;
 while(start<text.length){
  const naturalWord=natural.get(start),learned=known.find(w=>text.startsWith(w,start));
  // A learned single character must not split a normal compound such as 要求.
  const word=(learned&&(learned.length>1||!naturalWord||naturalWord.length===1)?learned:naturalWord)||String.fromCodePoint(text.codePointAt(start));
  const end=start+word.length;
  const reading=sourceReadings.get(word)||sounds.filter(s=>s.start>=start&&s.end<=end&&s.isZh).map(s=>s.reading).join(' ');
  result.push({text:word,start,end,pinyin:reading});start=end;
 }
 return result;
}
function close(){
 if(active?.isConnected&&active.matches('[role="button"]'))active.setAttribute('aria-expanded','false');
 if(panel)panel.hidden=true;active=null;
}
function show(target,text){
 if(target===active&&!panel.hidden){close();return;}
 close();active=target;
 document.dispatchEvent(new Event('atelier-pinyin-open'));
 const reading=target.dataset.reading?{text:target.dataset.reading,source:sourceReadings.has(text)?'Source vocabulary pronunciation':'Contextual pronunciation support · check unfamiliar names with your teacher'}:pronunciation(text);
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
  for(const word of chineseWords(text)){
   if(!chinese.test(word.text))continue;
   fragment.append(text.slice(end,word.start));
   const el=document.createElement('span');el.className='hanzi-tap';el.dataset.hanzi=word.text;el.dataset.reading=word.pinyin;el.lang='zh';el.textContent=word.text;
   const control=node.parentElement.closest('a,button,label,summary');
   if(!control){el.tabIndex=0;el.setAttribute('role','button');el.setAttribute('aria-expanded','false');el.setAttribute('aria-controls','pinyin-panel');el.setAttribute('aria-label','Show pinyin: '+word.text);}
   else{
    // Keep native controls valid: no nested buttons or extra tab stops.
    const keyboard=control.tagName==='LABEL'?control.control||control:control;
    keyboard.setAttribute('aria-keyshortcuts','Alt+P');
   }
   el.title='Tap this word for pinyin · select a sentence for English and Thai';fragment.append(el);end=word.end;
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
  if(window.getSelection()?.toString().trim().length>1&&!panel.contains(e.target))return;
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
 document.addEventListener('atelier-translation-open',close);
 observer=new MutationObserver(records=>{
  const roots=new Set();for(const record of records)for(const node of record.addedNodes){const el=node.nodeType===1?node:node.parentElement;if(el?.closest('#main'))roots.add(el);else if(el?.querySelector?.('#main'))roots.add(el.querySelector('#main'));}
  for(const root of roots)enhanceChinese(root);
 });
 observer.observe(document.getElementById('app'),{childList:true,subtree:true});
 enhanceChinese(document.getElementById('main'));
}
