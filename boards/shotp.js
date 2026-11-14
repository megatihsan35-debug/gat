const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();
for(const n of (process.argv[2]||'1,2,3,4').split(',')){const land=n==='4';const W=land?1587:1123,H=land?1123:1587;
const p=await b.newPage({viewport:{width:W,height:H},deviceScaleFactor:+(process.argv[3]||1)});
await p.goto('file:///home/claude/boards/out/p'+n+'.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
await p.screenshot({path:'/home/claude/boards/out/p'+n+((process.argv[3]||'1')!=='1'?'_hi':'')+'.png'});await p.close();}
await b.close();})();
