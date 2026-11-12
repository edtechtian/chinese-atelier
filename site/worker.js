// Existing Python curriculum logic runs on this device. Learner data stays local.
import {loadPyodide} from './runtime/pyodide.mjs';
let python;
let queue = Promise.resolve();
async function sync(populate = false) {
  await new Promise((resolve, reject) => python.FS.syncfs(populate, e => e ? reject(e) : resolve()));
}
async function initialize() {
  postMessage({type:'status',message:'Starting your private learning engine…'});
  python = await loadPyodide({indexURL:new URL('./runtime/', import.meta.url).href});
  await python.loadPackage('tzdata');
  const response = await fetch(new URL('./course.zip',import.meta.url));
  if (!response.ok) throw new Error('The course download failed. Reload when your connection is ready.');
  python.unpackArchive(await response.arrayBuffer(),'zip',{extractDir:'/atelier'});
  python.FS.mkdirTree('/atelier/data');
  const curriculumSeed=python.FS.readFile('/atelier/data/curriculum.json');
  python.FS.mount(python.FS.filesystems.IDBFS,{},'/atelier/data');
  try {await sync(true);} catch {throw new Error('Private browser storage is unavailable. Allow site storage or use a normal browser window. Existing work has not been reset.');}
  if(!python.FS.analyzePath('/atelier/data/curriculum.json').exists)python.FS.writeFile('/atelier/data/curriculum.json',curriculumSeed);
  await python.runPythonAsync([
    'import os, sys',
    'from pathlib import Path',
    "sys.path.insert(0, '/atelier')",
    "exec(Path('/atelier/bridge.py').read_text(), globals())"
  ].join(String.fromCharCode(10)));
  await sync();
}
const ready = initialize();
ready.catch(e=>postMessage({type:'fatal',message:e.message}));
onmessage = event => {
  queue = queue.catch(()=>{}).then(async()=>{
    const {id,path,data}=event.data;
    try {
      await ready;
      python.globals.set('_request_path',path);
      python.globals.set('_request_body',data===undefined?'':JSON.stringify(data));
      const raw=await python.runPythonAsync('browser_request(_request_path, _request_body)');
      const result=JSON.parse(raw);
      await sync();
      postMessage({id,...result});
    } catch(e){postMessage({id,status:503,body:{error:e.message||'The browser engine could not save this change. Keep your draft and reload.'}});}
  });
};
