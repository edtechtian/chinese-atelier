// Rewards report only actual server-awarded XP. No synthetic progress or scores.
export function celebrate(xp,message='Practice complete!'){
 if(!xp)return;
 document.querySelector('.xp-burst')?.remove();
 const el=document.createElement('div');el.className='xp-burst';el.setAttribute('role','status');
 el.textContent=message+' +'+xp+' XP';
 const stars=document.createElement('span');stars.className='reward-stars';stars.setAttribute('aria-hidden','true');
 for(let n=0;n<3;n++){const star=document.createElement('span');star.textContent='✦';stars.appendChild(star);}el.appendChild(stars);document.body.appendChild(el);
 const total=document.querySelector('[data-xp-total]');if(total){const old=Number(total.dataset.xpTotal||0);total.textContent=old+xp;total.dataset.xpTotal=old+xp;}
 setTimeout(()=>el.remove(),2600);
}
