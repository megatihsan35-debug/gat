const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();
for(const n of (process.argv[2]||'1,2,3,4,5').split(',')){
const p=await b.newPage({viewport:{width:1587,height:1123},deviceScaleFactor:+(process.argv[3]||1)});
await p.goto('file:///home/claude/boards/out/s'+n+'.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
await p.screenshot({path:'/home/claude/boards/out/s'+n+'.png'});await p.close();}
await b.close();})();
