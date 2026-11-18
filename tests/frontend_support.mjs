import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {pronunciation,registerPronunciation} from '../public/pronunciation.js';
import {adventurePath} from '../public/adventure-ui.js';
import {encouragement,encouragementCard} from '../public/rewards.js';
const curriculum=JSON.parse(readFileSync(new URL('../data/curriculum.json',import.meta.url)));
let vocabulary=0;
for(const lesson of curriculum.lessons){
 registerPronunciation(lesson);
 for(const v of lesson.vocabulary){assert.equal(pronunciation(v.chinese).text,v.pinyin.trim(),v.id);vocabulary++;}
 for(const r of lesson.readings)for(const sentence of r.body){assert.ok(pronunciation(sentence).text);}
}
for(const [text,expected] of [['银行','yínháng'],['请问您住几晚？','qǐng wèn nín zhù jǐ wǎn ？'],['请把房卡还给前台。','qǐng bǎ fáng kǎ huán gěi qián tái 。']])assert.equal(pronunciation(text).text,expected,text);
assert.match(pronunciation('请把房卡还给前台。').source,/Automatic/);
const units=JSON.parse(readFileSync(new URL('../curriculum/learning_path.json',import.meta.url))).units;
for(const u of units)for(const s of u.steps){s.state='available';s.record={};}
const html=adventurePath({path:{units},nextStep:units[0].steps[0]});
assert.equal((html.match(/class="winding-stop /g)||[]).length,100);
assert.equal((html.match(/href="#\/step\//g)||[]).length,101);
assert.ok(!html.includes('learn-locked'));assert.ok(!html.includes('Locked'));
for(const stage of ['discover','understand','build','communicate','apply','review','retry','writing','draft','unit','lesson'])assert.ok(encouragement(stage).length>30);
assert.ok(!encouragementCard('<script>','<img>').includes('<script>'));
console.log(`Support checks passed: ${vocabulary} source pronunciations, all source reading paragraphs, contextual polyphones, 100 open card links and encouragement.`);
