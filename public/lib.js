export function esc(value) { return String(value == null ? '' : value).replace(/[&<>"']/g, function(c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
async function localFetch(path, options) {
  try { return await fetch(path, options); }
  catch { throw new Error('Cannot reach the local app. Check that the local server is running, then try again. Keep this page open if you have unsaved work.'); }
}
export async function api(path, data, options = {}) {
  const headers = {'X-App-Request':'1'};
  const request = {credentials:'same-origin', headers:headers};
  if (data !== undefined) { request.method='POST'; headers['Content-Type']='application/json'; request.body=JSON.stringify(data); }
  Object.assign(request,options);
  const response = await localFetch(path,request);
  let result;
  try { result=await response.json(); } catch { throw new Error('The server returned an unreadable response. Check that the local server is running.'); }
  if (!response.ok) { const e=new Error(result.error || 'The request failed.'); e.details=result.details; e.status=response.status; throw e; }
  return result;
}
export const paths = {
 home:'M3 10l9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z',
 book:'M3 4h6a4 4 0 0 1 3 2 4 4 0 0 1 3-2h6v15h-6a4 4 0 0 0-3 2 4 4 0 0 0-3-2H3z M12 6v15',
 practice:'M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z',
 portfolio:'M8 6V4h8v2 M3 7h18v14H3z M3 12h18 M10 12v3h4v-3',
 arrow:'M4 12h16 M14 6l6 6-6 6', chevron:'M9 5l7 7-7 7', check:'M5 12l4 4L19 6',
 clock:'M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
 search:'M21 21l-6-6 M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0',
 globe:'M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0 M2 12h20 M12 2c6 6 6 14 0 20 M12 2c-6 6-6 14 0 20',
 menu:'M4 6h16 M4 12h16 M4 18h16', close:'M6 6l12 12 M18 6L6 18',
 leaf:'M20 3C7 2 2 8 5 16s16 3 15-13z M4 21L15 9',
 folder:'M3 5h6l2 3h10v13H3z', download:'M12 3v12 M6 9l6 6 6-6 M4 17v4h16v-4',
 lock:'M6 10V7a6 6 0 0 1 12 0v3 M4 10h16v12H4z M12 14v4',
 info:'M12 11v6 M12 7h.01 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
 sound:'M3 9h4l5-4v14l-5-4H3z M16 8q6 4 0 8 M18 4q12 8 0 16',
 refresh:'M20 7V2l-4 4 M20 7a9 9 0 1 0 1 8', save:'M4 3h13l4 4v14H3V3z M7 3v6h9V3 M7 21v-8h10v8',
 pin:'M12 22s8-8 8-14a8 8 0 1 0-16 0c0 6 8 14 8 14z M15 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0'
};
export function icon(name,cls='') { return '<svg class="icon '+esc(cls)+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="'+(paths[name]||paths.info)+'"/></svg>'; }
export function button(label, action, cls='button', attrs='') { return '<button class="'+cls+'" data-action="'+esc(action)+'" '+attrs+'>'+label+'</button>'; }
export function notice(text,kind='info') { return '<div class="notice '+kind+'">'+icon('info')+'<div>'+text+'</div></div>'; }
export function empty(title,text,link='',label='') { return '<div class="empty">'+icon('leaf')+'<h3>'+esc(title)+'</h3><p>'+esc(text)+'</p>'+(link?'<a class="button" href="'+esc(link)+'">'+esc(label)+icon('arrow')+'</a>':'')+'</div>'; }
let presentationTimeZone='Asia/Bangkok';
export function setTimeZone(zone) { new Intl.DateTimeFormat('en-GB',{timeZone:zone}); presentationTimeZone=zone; }
export function date(value) { return value ? new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:presentationTimeZone}).format(new Date(value)) : 'Not yet'; }
export function toast(message,error=false) { const t=document.querySelector('#toast'); t.textContent=message; t.className='visible'+(error?' error':''); clearTimeout(window.toastTimer); window.toastTimer=setTimeout(()=>{t.className='';},5000); }
export function errorView(error) { return notice(esc(error.message)+(error.details?'<ul>'+error.details.map(e=>'<li>'+esc(e)+'</li>').join('')+'</ul>':''),'error'); }
export function originLabel(origin) { return {textbook:'Original source',adaptation:'Editorial adaptation',supplementary:'Newly authored activity'}[origin]||'Source review'; }
export function sourceRefs(item) { return (item.sourceRefs||[]).length ? '<span class="source-ref">'+item.sourceRefs.map(r=>{ const m=r.match(/zt-(\d+)-slide-(\d+)/); return m?'L'+Number(m[1])+' · S'+Number(m[2]):esc(r); }).join(' / ')+'</span>' : ''; }
export async function download(url,filename) { const r=await localFetch(url,{credentials:'same-origin'}); if(!r.ok) throw new Error('Export failed. Please sign in again if required.'); const b=await r.blob(); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download=filename; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000); }
