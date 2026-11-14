const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const n=process.argv[2]||'1';const sc=+(process.argv[3]||1);
const p=await b.newPage({viewport:{width:1123,height:1587},deviceScaleFactor:sc});
await p.goto('file:///home/claude/boards/out/board'+n+'.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
await p.screenshot({path:'/home/claude/boards/out/board'+n+(sc>1?'_hi':'')+'.png'});
const over=await p.evaluate(()=>{const r=[];document.querySelectorAll('div,p,table').forEach(e=>{if(e.scrollHeight>e.clientHeight+1&&getComputedStyle(e).height!=='auto'&&e.style.height)r.push(e.textContent.slice(0,40))});return r});
console.log('overflow',JSON.stringify(over));await b.close();})();
