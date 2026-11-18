// Translation support is a local course asset. No selected text leaves the device.
export const translationKey=text=>text.normalize('NFKC').replace(/[\s，。！？,.!?、；;：:（）()“”‘’《》…—·]/gu,'');
let dataset,loading,panel,selectionTimer,request=0;
export async function loadTranslations(){
 if(dataset)return dataset;
 if(!loading)loading=fetch(new URL('./language-support.json',import.meta.url)).then(async r=>{if(!r.ok)throw new Error('Translation support could not be loaded. Reconnect and try selecting the sentence again.');const json=await r.json();dataset=new Map(json.entries.filter(e=>e.en&&e.th).map(e=>[translationKey(e.chinese),e]));return dataset;}).catch(e=>{loading=null;throw e;});
 return loading;
}
export function findTranslation(text,entries){
 const key=translationKey(text);if(entries.has(key))return {...entries.get(key),expanded:false};
 const parts=text.match(/[^。！？；\n]+[。！？；]?/gu)||[];
 const found=parts.map(s=>entries.get(translationKey(s.trim())));
 if(found.length>1&&found.every(Boolean))return {chinese:text,en:found.map(r=>r.en).join('\n'),th:found.map(r=>r.th).join('\n'),reviewStatus:found.every(r=>r.reviewStatus==='teacher_reviewed')?'teacher_reviewed':'machine_translation_pending_teacher_review',expanded:false};
 // A partial selection may use its enclosing sentence, clearly labelled as such.
 const full=Array.from(entries.values()).filter(r=>translationKey(r.chinese).includes(key)&&key.length>=4&&translationKey(r.chinese).length<=key.length+40).sort((a,b)=>a.chinese.length-b.chinese.length)[0];
 return full?{...full,expanded:true}:null;
}
async function showSelection(){
 const selected=window.getSelection();if(!selected||selected.isCollapsed)return;
 const text=selected.toString().trim(),anchor=selected.anchorNode?.parentElement,focus=selected.focusNode?.parentElement;
 if(!anchor?.closest('#main')||!focus?.closest('#main')||!/[\u3400-\u9fff]/u.test(text))return;
 if(anchor.closest('textarea,input,[contenteditable],.work-text,.teacher-feedback')||focus.closest('textarea,input,[contenteditable],.work-text,.teacher-feedback'))return;
 request++;const current=request;document.dispatchEvent(new Event('atelier-translation-open'));panel.hidden=false;
 panel.querySelector('.translation-original').textContent=text;
 const english=panel.querySelector('[data-translation="en"]'),thai=panel.querySelector('[data-translation="th"]'),note=panel.querySelector('.translation-note');
 english.textContent='Loading course translation…';thai.textContent='';note.textContent='Saved course translations · selected text stays on this device.';
 if(text.length>650){english.textContent='Please select one or two sentences (up to 650 characters).';return;}
 try{
  const entry=findTranslation(text,await loadTranslations());if(current!==request)return;
  if(!entry){english.textContent='This selection does not have a saved course translation yet. Select the full sentence, or ask your teacher to add one.';note.textContent='Nothing was sent to a translation service.';return;}
  english.textContent=entry.en;thai.textContent=entry.th;
  if(entry.expanded)panel.querySelector('.translation-original').textContent=entry.chinese;
  note.textContent=(entry.expanded?'Full sentence translation for your selection. ':'')+(entry.reviewStatus==='teacher_reviewed'?'Teacher-reviewed support.':entry.reviewStatus==='existing_vocabulary_gloss'?'Existing vocabulary gloss.':'Supplementary machine translation · pending teacher review.')+' Original Chinese remains authoritative.';
 }catch(e){if(current===request){english.textContent=e.message;note.textContent='Your work is unchanged. Nothing was sent to a translation service.';}}
}
export function installTranslation(){
 panel=document.createElement('aside');panel.id='translation-panel';panel.className='translation-panel pinyin-panel';panel.hidden=true;panel.setAttribute('aria-label','English and Thai translation');panel.setAttribute('aria-live','polite');
 panel.innerHTML='<button type="button" class="translation-close pinyin-close" aria-label="Close translation">×</button><strong class="translation-original" lang="zh"></strong><h3>English</h3><p data-translation="en" lang="en"></p><h3>ภาษาไทย</h3><p data-translation="th" lang="th"></p><small class="translation-note"></small>';
 document.body.append(panel);
 const schedule=()=>{clearTimeout(selectionTimer);selectionTimer=setTimeout(showSelection,180);};
 document.addEventListener('pointerup',e=>{if(!panel.contains(e.target))schedule();});
 document.addEventListener('keyup',e=>{if(e.key==='Shift'||e.shiftKey)schedule();});
 document.addEventListener('selectionchange',()=>{if(!window.getSelection()?.isCollapsed)schedule();});
 document.addEventListener('click',e=>{if(e.target.closest('.translation-close')){request++;panel.hidden=true;window.getSelection()?.removeAllRanges();}else if(e.target.closest('[data-hanzi]')&&window.getSelection()?.isCollapsed){request++;panel.hidden=true;}},true);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){request++;panel.hidden=true;}});
 document.addEventListener('atelier-pinyin-open',()=>{request++;panel.hidden=true;});
 window.addEventListener('hashchange',()=>{request++;panel.hidden=true;});
}
