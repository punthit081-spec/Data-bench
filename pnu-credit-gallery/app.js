const gallery=document.getElementById('gallery');
const viewer=document.getElementById('viewer');
const fullImage=document.getElementById('fullImage');
const caption=document.getElementById('caption');
let items=[];let current=0;
async function load(){
  const r=await fetch('gallery.json',{cache:'no-store'});
  items=await r.json();
  document.getElementById('count').textContent=items.length;
  const frag=document.createDocumentFragment();
  items.forEach((item,i)=>{
    const b=document.createElement('button'); b.className='card'; b.type='button';
    b.innerHTML=`<img loading="lazy" src="images/${item.file}" alt="เครดิตงานภาพที่ ${i+1}"><span>#${String(i+1).padStart(2,'0')}</span>`;
    b.addEventListener('click',()=>openViewer(i)); frag.appendChild(b);
  }); gallery.appendChild(frag);
}
function openViewer(i){current=i;const x=items[i];fullImage.src='images/'+x.file;fullImage.alt='เครดิตงานภาพที่ '+(i+1);caption.textContent=`ภาพ ${i+1} / ${items.length}`;viewer.classList.add('open');viewer.setAttribute('aria-hidden','false');document.body.style.overflow='hidden'}
function closeViewer(){viewer.classList.remove('open');viewer.setAttribute('aria-hidden','true');fullImage.src='';document.body.style.overflow=''}
function move(n){current=(current+n+items.length)%items.length;openViewer(current)}
viewer.querySelector('.close').addEventListener('click',closeViewer);
viewer.querySelector('.prev').addEventListener('click',()=>move(-1));
viewer.querySelector('.next').addEventListener('click',()=>move(1));
viewer.addEventListener('click',e=>{if(e.target===viewer)closeViewer()});
document.addEventListener('keydown',e=>{if(!viewer.classList.contains('open'))return;if(e.key==='Escape')closeViewer();if(e.key==='ArrowLeft')move(-1);if(e.key==='ArrowRight')move(1)});
let sx=0;viewer.addEventListener('touchstart',e=>sx=e.changedTouches[0].clientX,{passive:true});
viewer.addEventListener('touchend',e=>{const dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>55)move(dx>0?-1:1)},{passive:true});
document.addEventListener('contextmenu',e=>{if(e.target.closest('.gallery,.viewer'))e.preventDefault()});
load().catch(()=>{gallery.innerHTML='<p>ไม่สามารถโหลดรูปได้ กรุณารีเฟรชหน้าอีกครั้ง</p>'});