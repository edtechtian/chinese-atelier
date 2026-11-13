import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {loadPyodide} from '../site/runtime/pyodide.mjs';
const python=await loadPyodide({indexURL:fileURLToPath(new URL('../site/runtime/',import.meta.url))});
await python.loadPackage('tzdata');
python.unpackArchive(new Uint8Array(readFileSync(new URL('../site/course.zip',import.meta.url))),'zip',{extractDir:'/atelier'});
await python.runPythonAsync("from pathlib import Path\nexec(Path('/atelier/bridge.py').read_text(), globals())");
function api(path,body){
 python.globals.set('_test_path',path);python.globals.set('_test_body',body===undefined?'':JSON.stringify(body));
 return JSON.parse(python.runPython('browser_request(_test_path,_test_body)'));
}
assert.equal(api('/api/bootstrap').body.lessons.length,20);
assert.equal(api('/api/learning').body.path.units.flatMap(u=>u.steps).length,100);
const curriculum=JSON.parse(python.FS.readFile('/atelier/data/curriculum.json',{encoding:'utf8'}));
let correct=0,incorrect=0;
for(const lesson of curriculum.lessons){
 assert.equal(api('/api/lessons/'+lesson.id).body.originalTitle,lesson.originalTitle);
 for(const question of lesson.questions){
  const answer=question.type==='choice'?question.answer:question.acceptedAnswers[0];
  const r=api('/api/attempt',{lessonId:lesson.id,questionId:question.id,answer});
  assert.equal(r.status,200,JSON.stringify(r));assert.equal(r.body.correct,true,question.id);assert.equal(r.body.explanation,question.explanation);correct++;
  if(question.type==='choice'){
   const wrong=question.options.find(o=>o.id!==question.answer).id;
   const out=api('/api/attempt',{lessonId:lesson.id,questionId:question.id,answer:wrong});
   assert.equal(out.body.correct,false);assert.equal(out.body.explanation,question.explanation);incorrect++;
  }
 }
}
const lesson=curriculum.lessons[2],task=lesson.tasks[0];
const saved=api('/api/response',{lessonId:lesson.id,taskId:task.id,text:task.model,submit:true});
assert.equal(saved.body.text,task.model);
assert.equal(api('/api/bootstrap').body.state.responses[task.id].text,task.model);
assert.equal(api('/api/teacher').status,401);
assert.equal(api('/api/browser/teacher/open',{}).status,200);
assert.equal(api('/api/teacher').body.state.responses[task.id].text,task.model);
assert.equal(api('/api/export').body.state.responses[task.id].text,task.model);
assert.equal(api('/api/teacher/source',{}).status,409);
assert.equal(api('/api/attempt',{lessonId:lesson.id,questionId:lesson.questions[0].id,answer:''}).status,400);
assert.equal(api('/api/lessons/not-a-lesson').status,404);
console.log(JSON.stringify({passed:true,lessons:20,steps:100,correctAnswers:correct,incorrectAnswers:incorrect,writing:true,teacherView:true,export:true,errorStates:true}));
