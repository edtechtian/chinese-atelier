// Execute the actual reflection renderer without a browser or network.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../public/app.js', import.meta.url), 'utf8');
const curriculum = JSON.parse(fs.readFileSync(new URL('../data/curriculum.json', import.meta.url), 'utf8'));
const start = source.indexOf('function lessonReflection(l) {');
const end = source.indexOf('\nexport function sourceSlide', start);
assert.ok(start >= 0 && end > start, 'Locate the application reflection renderer');
const fixture = {
  B: {state: {attempts: [], responses: {}}},
  progress: () => ({sections: [], completed: false, reflection: ''}),
  sections: Array(8).fill(null),
  esc: value => String(value ?? '').replaceAll('<', '&lt;'),
  rubric: () => '<section>Criterion guidance</section>',
  sectionFooter: () => '<footer>Next section</footer>',
  icon: () => '',
};
vm.createContext(fixture);
vm.runInContext(source.slice(start, end), fixture);
for (const lesson of curriculum.lessons) {
  fixture.lesson = lesson;
  const html = vm.runInContext('lessonReflection(lesson)', fixture);
  assert.ok(html.includes('data-form="reflection"'), lesson.id + ' has a reflection form');
  assert.ok(html.includes('Complete this lesson'), lesson.id + ' has a completion control');
  assert.ok(!html.includes('undefined'), lesson.id + ' has no unresolved template value');
}
console.log('Reflection renderer passed for all 20 lessons.');
