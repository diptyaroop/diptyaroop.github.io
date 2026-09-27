const vm=require('node:vm');const fs=require('node:fs');const assert=require('node:assert/strict');
const code=fs.readFileSync(require('node:path').join(__dirname,'../assets/js/scholar.js'),'utf8');
const valid={scholar_id:'QkURxEAAAAAJ',citations:350,h_index:9,checked_at:new Date().toISOString()};
async function run(responses,expected,hostname='diptyaroop.github.io'){
 const values={'#scholar-verified':{dateTime:'2026-09-27',textContent:'27 Sep 2026'},'#scholar-stale':{textContent:''},'[data-scholar="citations"]':{textContent:'342'},'[data-scholar="h_index"]':{textContent:'8'}};
 let calls=[];const context={document:{querySelector:s=>values[s],addEventListener:()=>{},hidden:false},location:{hostname},setInterval:()=>{},setTimeout,clearTimeout,AbortController,Intl,Date,fetch:async url=>{calls.push(url);let r=responses.shift();if(r instanceof Error)throw r;return {ok:true,json:async()=>r};}};
 vm.runInNewContext(code,context);await new Promise(resolve=>setTimeout(resolve,30));
 assert.equal(values['[data-scholar="citations"]'].textContent,expected);
 return {values,calls};
}
(async()=>{
 await run([valid],'350');
 const fallback=await run([new Error('offline'),valid],'350');assert.equal(fallback.calls.length,2);
 await run([{...valid,citations:'999'},new Error('offline')],'342');
 await run([{...valid,scholar_id:'wrong'},new Error('offline')],'342');
 await run([{...valid,checked_at:'2020-01-01'},new Error('offline')],'342');
 const local=await run([valid],'350','127.0.0.1');assert.deepEqual(local.calls,['assets/data/scholar.json']);
 console.log('6 client checks passed: updates, failure fallback, invalid values, identity, stale dates, local preview.');
})();
