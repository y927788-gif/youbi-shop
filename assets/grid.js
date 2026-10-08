document.addEventListener('DOMContentLoaded',function(){
var root=document.documentElement.dataset.root||'';var fixedCat=document.body.dataset.cat||'';
var grid=document.getElementById('grid'),more=document.getElementById('more'),sort=document.getElementById('sort'),band=document.getElementById('band'),cnt=document.getElementById('cnt'),chips=document.querySelectorAll('[data-filter]');
var cat=fixedCat,shown=0,list=[],STEP=/\/(index\.html)?$/.test(location.pathname)?24:48;more.textContent='再看 '+STEP+' 件';
function card(p){var a=document.createElement('a');a.className='it';a.href=root+'product.html#'+p.i;
var ph=document.createElement('div');ph.className='ph';var im=document.createElement('img');im.src=window.__img(p);im.alt=p.s;im.loading='lazy';im.referrerPolicy='no-referrer';im.width=400;im.height=400;ph.appendChild(im);if(!p.sh)ph.appendChild(window.__rar(p.q||0));
if(p.d){var o=document.createElement('span');o.className='off';var b=document.createElement('b');b.textContent=p.d;o.appendChild(b);o.appendChild(document.createTextNode('折'));ph.appendChild(o)}
if(p.v){var v=document.createElement('span');v.className='vid';v.textContent='▶ REEL';ph.appendChild(v)}
if(p.dr||p.lw){var dp=document.createElement('span');dp.className='drop';dp.textContent=p.dr?'↓'+p.dr+'%':'30天最低';ph.appendChild(dp)}
var tg=document.createElement('span');tg.className='tag';var d=document.createElement('span');d.className='d';d.textContent='$';var val=document.createElement('span');val.className='v';val.textContent=Number(p.p).toLocaleString('zh-TW');tg.appendChild(d);tg.appendChild(val);
var n=document.createElement('span');n.className='n';n.textContent=p.s;var s=document.createElement('span');s.className='s';s.textContent=p.sh?'品牌官網':'銷量戰力';var sb=document.createElement('b');sb.textContent=p.sh||p.sold;s.appendChild(sb);
a.appendChild(ph);a.appendChild(tg);a.appendChild(n);a.appendChild(s);return a}
function apply(){window.__load(function(d){var b=band.value;list=d.filter(function(p){return (!cat||p.c===cat)&&(b==='all'||(b==='a'&&p.p<100)||(b==='b'&&p.p>=100&&p.p<500)||(b==='c'&&p.p>=500&&p.p<2000)||(b==='d'&&p.p>=2000))});
var k=sort.value;list.sort(function(x,y){return k==='hot'?y.n-x.n:k==='sold'?(y.q||0)-(x.q||0):k==='off'?((x.d||10)-(y.d||10)):k==='low'?x.p-y.p:y.p-x.p});
grid.textContent='';shown=0;page();cnt.textContent='共 '+list.length+' 件'})}
function page(){list.slice(shown,shown+STEP).forEach(function(p){grid.appendChild(card(p))});shown+=STEP;more.hidden=shown>=list.length}
more.addEventListener('click',page);sort.addEventListener('change',apply);band.addEventListener('change',apply);
chips.forEach(function(c){c.addEventListener('click',function(){cat=c.dataset.filter;chips.forEach(function(x){x.setAttribute('aria-pressed',String(x===c))});apply()})});
apply();
});