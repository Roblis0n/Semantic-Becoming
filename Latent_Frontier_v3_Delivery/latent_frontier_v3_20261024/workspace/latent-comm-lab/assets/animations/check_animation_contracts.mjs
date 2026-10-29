import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';import vm from 'node:vm';import assert from 'node:assert/strict';
const root=path.dirname(fileURLToPath(import.meta.url));await import('./animation_engine.js');const A=globalThis.FrontierAnimations,checks=[];
for(const [id,a]of Object.entries(A.data)){
 for(const st of a.steps){const f=A.frame(id,st.t);assert(f.description.includes(st.fact));assert(f.elements.some(e=>e.text?.includes('无模型实测')));checks.push({id,time:st.t,semantic_stage:true});}
 const html=await fs.readFile(path.join(root,id,'index.html'),'utf8'),script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
 for(const reduced of [false,true]){
  const els=Object.fromEntries(['#art','#seek','#time','#play','#explanation','#restart'].map(x=>[x,{value:0,max:0,textContent:'',innerHTML:''}]));let cb;let mql={matches:reduced,addEventListener:()=>{}};const c=vm.createContext({FrontierAnimations:A,document:{querySelector:x=>els[x]},matchMedia:()=>mql,requestAnimationFrame:f=>{cb=f;}});vm.runInContext(script,c);assert(els['#art'].innerHTML.includes('<svg'));assert.equal(+els['#seek'].max,a.duration);
  if(reduced)assert.equal(+els['#seek'].value,a.duration);else{els['#play'].onclick();cb(500);assert(+els['#seek'].value>0);els['#play'].onclick();}
  els['#seek'].value=a.duration;els['#seek'].oninput();assert.equal(+els['#seek'].value,a.duration);assert(els['#explanation'].textContent.includes('下一步'));els['#restart'].onclick();assert.equal(+els['#seek'].value,0);
  checks.push({id,dom_contract_mock:true,reduced_motion:reduced,play_pause_seek_restart:true,real_browser:false});
 }
}
const texts=(id,t)=>A.frame(id,t).elements.filter(e=>e.kind==='text').map(e=>e.text).join('\n');assert(texts('A04',9).includes('δ = 1/4'));assert(texts('A04',14).includes('δ = 4/17'));assert(texts('A04',14).includes('4δ = 16/17'));assert(texts('A05',22).includes('(1, 1)'));
await fs.writeFile(path.join(root,'animation_contract_checks.json'),JSON.stringify({status:'passed',checks,exact_dynamic_values:true,real_browser_verified:false,claim_boundary:'VM tests exercise deterministic state and mocked control callbacks. They are not real browser interaction tests.',research_state:'NOT_RUN'},null,2));console.log('Passed',checks.length,'deterministic stage/control checks; real browser remains unverified.');
