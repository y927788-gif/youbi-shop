// Paste into the console context of https://affiliate.shopee.tw/offer/product_offer (javascript_tool). Defines window.__H.
// H.prep(TAB, FROM, TO): open TAB, select pages FROM..TO (max 5 pages = 100 items) and open the 批量取得連結 dialog.
// Then do REAL clicks: Sub_id1 field (783,212) → type "web" → 取得連結 button (1005,563) → wait 7 s (CSV lands in D:\ComfyUI).
// The dialog's position depends on the window size: after the first prep(), call H.rects() (CSS px) and multiply by
// (screenshot coordinate-frame width / innerWidth) to get click coordinates. 10/6 values: frame 1568 wide, innerWidth 1872 → (784,239) and (1011,598).
// Theme keywords: real click on the search box (find 輸入關鍵字搜尋) → triple_click → type keyword → Return → wait 3 s → H.prep(keyword, FROM, TO).
// prep() refuses (returns 'same-results…') if a keyword search didn't refresh the list (10/6: 5 batches repeated the previous keyword).
// Then await H.clearSel(). After all batches: H.save() downloads youbi_harvest_<ts>.json (images, discounts, tag = keyword-pN).
window.__H={};
const H=window.__H;
H.sleep=ms=>new Promise(r=>setTimeout(r,ms));
H.$$=(s,r=document)=>[...r.querySelectorAll(s)];
H.firstId=()=>{const a=document.querySelector('a[href*="/offer/product_offer/"]');return a?(a.getAttribute('href').match(/product_offer\/(\d+)/)||[])[1]:null};
H.activePage=()=>{const a=document.querySelector('.PaginationNoTotal__wrap .page-page.active');return a?+a.innerText.trim():0};
H.waitChange=async prev=>{for(let i=0;i<40;i++){await H.sleep(250);const f=H.firstId();if(f&&f!==prev)return true}return false};
H.selCount=()=>{const m=document.body.innerText.match(/(\d+)\s*\/\s*100\s*已選擇/);return m?+m[1]:0};
H.clearSel=async()=>{if(!H.selCount())return 0;const s=H.$$('.batch-bar span').find(e=>/^取\s*消$/.test(e.innerText.trim()));if(s){(s.closest('button')||s).click();await H.sleep(800);const ok=H.$$('.ant-modal-confirm button, .ant-modal button').find(b=>/^確\s*定$/.test(b.innerText.trim()));if(ok){ok.click();await H.sleep(700)}}return H.selCount()};
H.scrape=(tab,page)=>H.$$('a[href*="/offer/product_offer/"]').map(a=>{const id=(a.getAttribute('href').match(/product_offer\/(\d+)/)||[])[1];const t=a.innerText.split('\n').map(s=>s.trim()).filter(Boolean);const img=(a.querySelector('img')||{}).src||'';const disc=(a.innerText.match(/([\d.]+)\s*\n?\s*折/)||[])[1]||'';const price=(a.innerText.match(/\$([\d,.]+)/)||[])[1]||'';const sold=(a.innerText.match(/已售出\s*([\d.,萬+]+)/)||[])[1]||'';const comm=(a.innerText.match(/分潤率\s*([\d.]+%)/)||[])[1]||'';const name=t.find(s=>s.length>8&&!/^\$|已售出|分潤率|取得連結|^[\d.]+$|^折$/.test(s))||'';return {id,name,img:img.split('/').pop().replace(/\.webp$/,''),price,sold,disc,comm,tag:tab+'-p'+page}});
H.items=[];
H.prep=async(TAB,FROM,TO)=>{if(location.pathname.includes('captcha'))return 'captcha';await H.clearSel();
 const cur=(H.$$('[class*=active]').map(e=>e.innerText.trim()).find(t=>t===TAB));
 if(!cur){const tab=H.$$('[role=tab], [class*=tab] span, [class*=Tab] span').find(t=>t.innerText.trim()===TAB);if(tab){const p=H.firstId();tab.click();await H.waitChange(p);await H.sleep(800)}}
 if(H.activePage()>FROM){const one=H.$$('.PaginationNoTotal__wrap .page-page').find(e=>e.innerText.trim()==='1');if(one){const p=H.firstId();one.click();await H.waitChange(p);await H.sleep(600)}}
 while(H.activePage()<FROM){const p=H.firstId();const nx=document.querySelector('.PaginationNoTotal__wrap .page-next');if(!nx||nx.classList.contains('disabled'))return 'end';nx.click();if(!await H.waitChange(p))return 'stuck';await H.sleep(600)}
 const st=H.firstId();if(st&&st===H.prevStart)return 'same-results: the list did not change since the last batch (search not refreshed?) - search again';H.prevStart=st;
 let n=0;for(let pg=FROM;pg<=TO;pg++){const s=H.scrape(TAB,pg);H.items.push(...s);n+=s.length;const cb=document.querySelector('.batch-bar input[type=checkbox]');if(cb&&!cb.checked){cb.click();await H.sleep(400)}
  if(pg<TO){const p=H.firstId();const nx=document.querySelector('.PaginationNoTotal__wrap .page-next');if(!nx||nx.classList.contains('disabled'))break;nx.click();if(!await H.waitChange(p))break;await H.sleep(1200+Math.random()*1200)}}
 H.$$('button').find(b=>b.innerText.trim()==='批量取得連結').click();await H.sleep(1200);
 return {tab:TAB,page:H.activePage(),scraped:n,selected:H.selCount(),modal:getComputedStyle(document.querySelector('.ant-modal-wrap')).display}};
H.save=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(H.items)],{type:'application/json'}));a.download='youbi_harvest_'+Date.now()+'.json';document.body.appendChild(a);a.click();a.remove();return H.items.length};
H.rects=()=>{const m=H.$$('.ant-modal').find(x=>x.getBoundingClientRect().width>0)||document.querySelector('.ant-modal');const sub=[...m.querySelectorAll('input')].find(i=>/SportShoes/.test(i.placeholder||''));const ok=[...m.querySelectorAll('button')].find(b=>b.innerText.trim()==='取得連結');const r=e=>{const b=e.getBoundingClientRect();return [Math.round(b.x+b.width/2),Math.round(b.y+b.height/2)]};return {sub:r(sub),ok:r(ok),vw:innerWidth,vh:innerHeight}};
'ok'
