const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const jobs=JSON.parse(process.argv[2]);
for(const [out,qs] of jobs){const u=new URLSearchParams(qs);const W=+(u.get('w')||1600),H=+(u.get('h')||1000);
const p=await b.newPage({viewport:{width:W,height:H}});p.on('console',m=>console.log('C',m.text().slice(0,200)));p.on('pageerror',e=>console.log('PERR',e.message));
await p.goto('http://localhost:8765/render.html?'+qs);await p.waitForFunction('window.__done===true',null,{timeout:900000});
await p.screenshot({path:out,omitBackground:true});await p.close();console.log('ok',out);}
await b.close();})();
