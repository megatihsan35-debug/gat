const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();
for(const n of ['1','2','3','4']){const land=n==='4';const p=await b.newPage({viewport:{width:land?1587:1123,height:land?1123:1587}});
await p.goto('file:///home/claude/boards/out/p'+n+'.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
await p.addStyleTag({content:`@page{size:${land?'420mm 297mm':'297mm 420mm'};margin:0}`});
await p.pdf({path:'/home/claude/boards/out/s'+n+'.pdf',width:land?'420mm':'297mm',height:land?'297mm':'420mm',printBackground:true,pageRanges:'1'});await p.close();}
await b.close();})();
