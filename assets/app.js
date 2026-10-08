(function(){
var root=document.documentElement.dataset.root||'';
var box=document.getElementById('q'),res=document.getElementById('sres'),data=null;
function load(cb){if(data)return cb(data);fetch(root+'data/p.json').then(function(r){return r.json()}).then(function(d){data=d;cb(d)}).catch(function(){})}
function money(n){return '$'+Number(n).toLocaleString('zh-TW')}
function rar(n){var r=n>=1000000?['UR','ur']:n>=300000?['SSR','ssr']:n>=50000?['SR','sr']:n>=10000?['R','r']:['N','n'];var s=document.createElement('span');s.className='rar r-'+r[1];s.textContent=r[0];return s}
function img(p,big){if(p.mu)return p.mu;return p.m?'https://down-aws-tw.img.susercontent.com/file/'+p.m+(big?'':'_tn'):root+'img/'+p.i+'.webp'}
if(box){box.addEventListener('focus',function(){load(function(){})});
box.addEventListener('input',function(){var t=box.value.trim().toLowerCase();if(!t){res.classList.remove('on');return}
load(function(d){var hit=d.filter(function(p){return p.s.toLowerCase().indexOf(t)>=0}).slice(0,12);res.textContent='';
if(!hit.length){var no=document.createElement('p');no.style.padding='10px 14px';no.textContent='本站找不到「'+box.value+'」';res.appendChild(no)}
var cpa=document.createElement('a');cpa.href=root+'coupang.html#search';cpa.innerHTML='<span style="color:var(--cyan);font-weight:700">到酷澎館搜尋全站商品 ›</span>';res.appendChild(cpa);
hit.forEach(function(p){var a=document.createElement('a');a.href=root+'product.html#'+p.i;var im=document.createElement('img');im.src=img(p);im.alt='';im.loading='lazy';im.referrerPolicy='no-referrer';
var tx=document.createElement('span');tx.textContent=p.s;var pr=document.createElement('span');pr.className='sp';pr.textContent=money(p.p);a.appendChild(im);a.appendChild(tx);a.appendChild(pr);res.appendChild(a)});res.classList.add('on')})});
document.addEventListener('click',function(ev){if(!res.contains(ev.target)&&ev.target!==box)res.classList.remove('on')});}
window.__load=load;window.__money=money;window.__img=img;window.__rar=rar;
function cpLoad(el){var f=el.querySelector('.cpf');if(!f||f.firstChild)return;var w=Math.max(300,Math.min(2000,Math.round(f.clientWidth||680)));var i=document.createElement('iframe');i.width=w;i.height=140;i.setAttribute('frameborder','0');i.setAttribute('scrolling','no');i.referrerPolicy='unsafe-url';i.title='酷澎熱銷商品';
i.src='https://ads-partners.tw.coupang.com/widgets.html?id='+el.dataset.id+'&template=carousel&trackingCode=AF7017986&subId=&width='+w+'&height=140&tsource=';f.appendChild(i)}
window.__cpLoad=cpLoad;
var cps=document.querySelectorAll('.cpw');if(cps.length){if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){cpLoad(x.target);io.unobserve(x.target)}})},{rootMargin:'300px'});cps.forEach(function(c){io.observe(c)})}else cps.forEach(cpLoad)}
document.addEventListener('click',function(ev){var b=ev.target.closest('[data-cpw]');if(!b)return;var box=document.getElementById(b.dataset.target);if(!box)return;box.dataset.id=b.dataset.cpw;var f=box.querySelector('.cpf');f.textContent='';cpLoad(box);box.querySelector('.cpl').firstChild.textContent='酷澎熱銷・'+b.textContent;
document.querySelectorAll('[data-target="'+b.dataset.target+'"]').forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});if(window.gtag)gtag('event','coupang_tab',{cat:b.textContent})});
if(matchMedia('(hover:hover) and (pointer:fine)').matches&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
document.addEventListener('pointermove',function(e){var ph=e.target.closest&&e.target.closest('.it .ph');if(!ph)return;var r=ph.getBoundingClientRect(),x=(e.clientX-r.left)/r.width,y=(e.clientY-r.top)/r.height;
ph.style.setProperty('--ry',((x-.5)*16).toFixed(1)+'deg');ph.style.setProperty('--rx',((.5-y)*16).toFixed(1)+'deg');ph.style.setProperty('--mx',(x*100).toFixed(0)+'%');ph.style.setProperty('--my',(y*100).toFixed(0)+'%')});
document.addEventListener('pointerout',function(e){var ph=e.target.closest&&e.target.closest('.it .ph');if(ph&&!ph.contains(e.relatedTarget)){ph.style.setProperty('--rx','0deg');ph.style.setProperty('--ry','0deg')}});}
function ev(n,p){if(window.gtag)window.gtag('event',n,p)}
document.addEventListener('click',function(e){var a=e.target.closest('a[href]');if(a&&/(^https:\/\/(s\.)?shopee\.tw|coupang|oeya\.com\.tw)/.test(a.href)){var q=a.closest('.q');ev('shop_click',{placement:q?'quest':a.dataset.pl?a.dataset.pl:(a.classList.contains('cta')?(location.pathname.indexOf('/guides/')>=0?'guide':'product'):'other'),quest:q?q.dataset.qid:'',item_name:(a.querySelector('.t')||a).textContent.slice(0,90),link_url:a.href})}
var b=e.target.closest('.emb button');if(b){var q2=b.closest('.q');ev('media_open',{platform:b.dataset.p,quest:q2?q2.dataset.qid:'',creator:(b.querySelector('.au')||{}).textContent||''})}},true);
document.addEventListener('click',function(ev){var b=ev.target.closest('.emb button');if(!b)return;var p=b.dataset.p,box=b.parentNode,el;
if(p==='th'){el=document.createElement('blockquote');el.className='text-post-media';el.setAttribute('data-text-post-permalink',b.dataset.url);el.setAttribute('data-text-post-version','0');var a=document.createElement('a');a.href=b.dataset.url;a.textContent='Threads 貼文載入中…';el.appendChild(a);box.classList.add('on');b.replaceWith(el);var sc=document.createElement('script');sc.async=true;sc.src='https://www.threads.com/embed.js';document.body.appendChild(sc);setTimeout(function(){box.querySelectorAll('iframe').forEach(function(f){if(f.offsetHeight<40){f.style.height='560px'}})},6000);return}
el=document.createElement('iframe');el.title=b.getAttribute('aria-label');el.allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen';el.allowFullscreen=true;el.referrerPolicy='strict-origin-when-cross-origin';
el.src=p==='yt'?'https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1&rel=0':'https://www.tiktok.com/player/v1/'+b.dataset.id+'?autoplay=1&rel=0&description=1';
box.classList.add('on');b.replaceWith(el)});
})();