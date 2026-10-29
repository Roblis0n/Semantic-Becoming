import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath,pathToFileURL} from 'node:url';import {createRequire} from 'node:module';
const root=path.dirname(fileURLToPath(import.meta.url));const require=createRequire(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright','package.json'));const {chromium}=require('playwright');
const report={scope:'Offline HTML animation sources on the dot cloud computer; not an external website',browser:'Chromium via installed Playwright',checks:[],research_state:'NOT_RUN'};
let browser;
try{
 browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 for(const id of ['A01','A02','A03','A04','A05']){
  const page=await browser.newPage({viewport:{width:1280,height:950}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto(pathToFileURL(path.join(root,id,'index.html')).href);await page.waitForSelector('#art svg');
  const initial=await page.locator('#art svg').textContent();if(!initial.includes('无模型实测'))throw Error(id+' missing research disclosure');
  await page.locator('#play').click();await page.waitForTimeout(350);await page.locator('#play').click();const progressed=Number(await page.locator('#seek').inputValue());if(!(progressed>0))throw Error(id+' failed play');
  await page.locator('#seek').evaluate(el=>{el.value=el.max;el.dispatchEvent(new Event('input'));});const final=await page.locator('#art svg').textContent();await page.screenshot({path:path.join(root,id,'browser_final.png')});
  const hiddenOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);if(hiddenOverflow)throw Error(id+' page overflow');
  await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await page.waitForSelector('#art svg');const reduced=await page.locator('#seek').inputValue();if(Number(reduced)!==Number(await page.locator('#seek').getAttribute('max')))throw Error(id+' reduced-motion failure');
  report.checks.push({id,loaded:true,play_pause:true,scrub_final:true,reduced_motion_final:true,horizontal_overflow:false,script_errors:errors,final_text:final});if(errors.length)throw Error(id+' script errors');await page.close();
 }
 report.status='passed';
}catch(e){report.status='blocked_or_failed';report.error=String(e);process.exitCode=1;}finally{if(browser)await browser.close();await fs.writeFile(path.join(root,'browser_qa.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,checks:report.checks.length,error:report.error}));}
