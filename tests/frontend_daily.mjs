// Render every actual microstep against production data; no browser or invented curriculum.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=new URL('../',import.meta.url),c=JSON.parse(fs.readFileSync(new URL('data/curriculum.json',root))),path=JSON.parse(fs.readFileSync(new URL('curriculum/learning_path.json',root)));
const source=fs.readFileSync(new URL('public/daily.js',root),'utf8').replace(/^import .*;\n/gm,'').replaceAll('export async function','async function').replaceAll('export function','function');
const escape=v=>String(v??'').replaceAll('<','&lt;');
const d={path:structuredClone(path),settings:{dailyGoal:10,weeklyGoal:4,timeZone:'Asia/Bangkok'},date:'2026-10-30',completedSteps:0,completedUnits:0,xp:0,reviewCounts:{due:0,overdue:0,upcoming:0,mastered:0,needsPractice:0},reviewLimit:4,week:[],badges:[],dailyChallenge:{id:'hospitality-welcome',title:'A welcome with a question'},reminders:[],activeSeconds:0,streak:0,weeklyActiveDays:0,nextStep:null};
for(const u of d.path.units)for(const s of u.steps){s.state='available';s.record={startedAt:'2026-10-30T01:00:00Z'};}
const adventure=await import(new URL('public/adventure-ui.js',root));
const visual=await import(new URL('public/visual.js',root));
let calls=0;
const box={dashboardView:adventure.dashboardView,adventurePath:adventure.adventurePath,prepareVisual:async()=>{},visualRecallCard:visual.visualRecallCard,unitVisualIntro:visual.unitVisualIntro,vocabularyPicture:visual.vocabularyPicture,celebrate:()=>{},esc:escape,icon:()=>'',date:v=>String(v??''),sourceRefs:i=>(i.sourceRefs||[]).join(' / '),notice:v=>'<aside>'+v+'</aside>',empty:(t,p)=>'<section>'+t+p+'</section>',toast:()=>{},localStorage:{getItem:()=>null,removeItem:()=>{}},api:async p=>{calls++;if(p==='/api/learning')return d;if(p==='/api/learning/session')return{sessionId:'test-session'};if(p.includes('/reviews'))return{counts:d.reviewCounts,items:[],limit:4};if(p.includes('/phrases'))return{themes:['Tourism'],items:[]};if(p.includes('/challenges'))return{items:[],work:{}};if(p.includes('/teacher/learning'))return{dashboard:d,reviewAttempts:0,objectiveSuccessRate:null,reviewSuccessRate:null,selfRated:0,retention:{new:0},support:[],items:[],grammarErrors:[],work:[]};throw Error(p);}};
vm.createContext(box);vm.runInContext(source+'\nthis.dailyExports={dailyView,teacherLearningView,microPortfolio};',box);
const B={criteria:c.criteria,state:{learning:{work:{},srs:{}},activity:[]}},ctx={B,loadLesson:async id=>c.lessons.find(l=>l.id===id),setActiveLesson:()=>{},questionCard:q=>'<form>'+escape(q.prompt)+'</form>',taskCard:t=>'<article>'+escape(t.prompt)+'</article>'};
let count=0;
for(const u of path.units)for(const s of u.steps){const html=await box.dailyExports.dailyView(ctx,['step',s.id]);assert.ok(html.includes('data-form="learn-step"'),s.id);assert.ok(!html.includes('undefined'),s.id+' unresolved value');assert.ok(html.includes(u.title));count++;}
for(const route of [[],['path'],['review'],['review','short'],['phrasebook'],['challenges'],['reminders'],['step','missing-step']]){const html=await box.dailyExports.dailyView(ctx,route);assert.ok(html.length>30);assert.ok(!html.includes('undefined'),String(route));}
assert.ok((await box.dailyExports.teacherLearningView(B)).includes('100'));assert.ok(box.dailyExports.microPortfolio(B).includes('hospitality'));
console.log('Daily render checks passed for all 100 steps, eight route states and teacher analytics.');
const libSource=fs.readFileSync(new URL('public/lib.js',root),'utf8');
const dates=await import('data:text/javascript;base64,'+Buffer.from(libSource).toString('base64'));
dates.setTimeZone('Asia/Bangkok');assert.ok(dates.date('2026-10-31T02:00:00Z').includes('09:00'));
dates.setTimeZone('Europe/Berlin');assert.ok(dates.date('2026-10-31T02:00:00Z').includes('03:00'));
console.log('Review timestamps render in the selected learning time zone.');
