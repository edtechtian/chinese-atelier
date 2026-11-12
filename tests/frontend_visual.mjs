import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=new URL('../',import.meta.url),data=JSON.parse(fs.readFileSync(new URL('curriculum/visual_learning.json',root))),curriculum=JSON.parse(fs.readFileSync(new URL('data/curriculum.json',root)));
const text=fs.readFileSync(new URL('public/visual.js',root),'utf8').replace(/^import .*;\n/gm,'').replaceAll('export async function','async function').replaceAll('export function','function');
const esc=v=>String(v??'').replaceAll('<','&lt;');
const B={state:{visualLearning:{attempts:[],responses:{}}}},ctx={B};
const box={api:async p=>p==='/api/visual'?data:{config:data,progress:B.state.visualLearning},esc,icon:()=>'',sourceRefs:x=>(x.sourceRefs||[]).join(' / '),notice:x=>x,empty:(a,b)=>a+b,date:x=>x,toast:()=>{},celebrate:()=>{},localStorage:{getItem:()=>null}};
vm.createContext(box);vm.runInContext(text+'\nthis.exports={visualView,visualRecallCard,teacherVisualPanel,visualPortfolio};',box);
let count=0;
for(const unit of data.units)for(const a of unit.activities){const html=await box.exports.visualView(ctx,['visual',unit.id,a.id]);assert.ok(html.includes('data-id="'+a.id+'"'),a.id);assert.ok(!html.includes('undefined'),a.id);assert.ok(html.includes('pending teacher review'));count++;}
for(const mode of ['', 'hotel','thailand','dialogue','not-a-unit']){const html=await box.exports.visualView(ctx,['visual',mode]);assert.ok(html.length>30);assert.ok(!html.includes('undefined'));}
for(const l of curriculum.lessons)for(const v of l.vocabulary){const html=box.exports.visualRecallCard(v,false);assert.ok(html.includes(v.chinese));assert.ok(html.includes('learn-review'));assert.ok(!html.includes('undefined'));}
assert.ok((await box.exports.teacherVisualPanel()).includes('20 source-linked units'));
assert.ok(box.exports.visualPortfolio(B).includes('saved picture descriptions'));
console.log('Visual render checks passed: '+count+' activities, 268 source cards, four modes, teacher panel, portfolio and unknown-unit state.');
