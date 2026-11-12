let worker,sequence=0;
const pending=new Map();
function engine(){
  if(!worker){
    worker=new Worker(new URL('./worker.js',import.meta.url),{type:'module'});
    worker.onmessage=({data})=>{
      if(data.type==='status'){const line=document.querySelector('#engine-status');if(line)line.textContent=data.message;return;}
      if(data.type==='fatal'){for(const p of pending.values())p.reject(new Error(data.message));pending.clear();return;}
      const p=pending.get(data.id);if(!p)return;pending.delete(data.id);
      if(data.status>=400){const e=new Error(data.body.error||'The request could not be completed.');e.status=data.status;e.details=data.body.details;p.reject(e);}
      else p.resolve(data);
    };
    worker.onerror=()=>{for(const p of pending.values())p.reject(new Error('The browser engine could not start. Reload with site storage and JavaScript enabled.'));pending.clear();};
  }
  return worker;
}
async function request(path,data){
  const id=++sequence;const target=engine();
  return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject});target.postMessage({id,path,data});});
}
let lockReady;
if(navigator.locks){
  lockReady=new Promise((resolve,reject)=>{
    navigator.locks.request('chinese-atelier-learning-v1',{ifAvailable:true},async lock=>{
      if(!lock){reject(new Error('Your learning app is already open in another tab. Close that tab and reload this page to protect your saved work.'));return;}
      resolve();await new Promise(()=>{});
    }).catch(reject);
  });
  lockReady.catch(()=>{});
} else lockReady=Promise.resolve();
export async function browserApi(path,data){await lockReady;return (await request(path,data)).body;}
export async function browserDownload(path,filename){
  await lockReady;const r=await request(path);
  const text=r.contentType?.startsWith('application/json')?JSON.stringify(r.body,null,2):r.body;
  const url=URL.createObjectURL(new Blob([text],{type:r.contentType}));const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
