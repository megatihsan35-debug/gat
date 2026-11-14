const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1123,height:1587}});
for(const n of ['1','2']){await p.goto('file:///home/claude/boards/out/board'+n+'.html');await p.evaluate(()=>document.fonts.ready);
await p.addStyleTag({content:'@page{size:297mm 420mm;margin:0} html,body{width:1123px;height:1587px;overflow:hidden}'});await p.waitForTimeout(300);
await p.pdf({path:'/home/claude/boards/out/b'+n+'.pdf',preferCSSPageSize:true,printBackground:true});}
await b.close();})();
