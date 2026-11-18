import {esc} from './lib.js?v=68969ca6a5a3';
const lines={
 discover:['Useful expressions, ready for your next conversation. Your recall practice counts.','You made time to retrieve the language, Emmalyne. That is how it becomes easier to use.'],
 understand:['You worked through the meaning and the evidence. That is thoughtful reading.','One more text explored. Take a moment to notice what you understand more clearly now.'],
 build:['You turned a language pattern into your own words. Keep building on that.','Your own sentence is a worthwhile step. Revisit the feedback and let your next version grow.'],
 communicate:['You made space for another person’s perspective. Keep practising your response.','You have completed the communication practice. Notice one phrase you want to use again.'],
 apply:['You connected Chinese with a practical situation. That is progress worth keeping.','You put the language to work. Your reflection will help you choose what to practise next.'],
 unit:['Five steps completed, Emmalyne. You have another set of Chinese experiences to build on.'],
 review:['Another thoughtful recall saved. A little practice today makes a useful return tomorrow.','Remembering takes practice. You showed up and gave this expression another chance.'],
 correct:['Well reasoned, Emmalyne. Compare the explanation and keep that connection.','That response fits. You are making the language more usable, one choice at a time.'],
 retry:['You used the feedback to improve your answer. That is a learning achievement.'],
 writing:['Your Chinese response is submitted. Your ideas now have a place in your portfolio.','You expressed your own ideas in Chinese. Your teacher can now help you develop the next version.'],
 draft:['Your ideas are safely saved. You can return and build on them when you are ready.'],
 lesson:['Lesson completed, Emmalyne. Look back at what you can now express and give yourself credit for the work.']
};
const turns=new Map();
export function encouragement(kind='correct'){
 const messages=lines[kind]||lines.correct,n=turns.get(kind)||0;turns.set(kind,n+1);return messages[n%messages.length];
}
export function encouragementCard(title,message){return '<section class="learning-encouragement" role="status"><span aria-hidden="true">✦</span><div><h2>'+esc(title)+'</h2><p>'+esc(message)+'</p></div></section>';}
// Encouragement also appears during repeat practice; only real awards show XP.
export function celebrate(xp,message='Practice complete!'){
 document.querySelector('.xp-burst')?.remove();
 const el=document.createElement('div');el.className='xp-burst';el.setAttribute('role','status');
 el.textContent=message+(xp>0?' +'+xp+' XP':'');
 const stars=document.createElement('span');stars.className='reward-stars';stars.setAttribute('aria-hidden','true');
 for(let n=0;n<3;n++){const star=document.createElement('span');star.textContent='✦';stars.appendChild(star);}el.appendChild(stars);document.body.appendChild(el);
 setTimeout(()=>el.remove(),5500);
}
