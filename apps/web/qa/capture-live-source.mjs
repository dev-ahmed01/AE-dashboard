// Capture only public same-origin static files from the owner's approved Netlify deployment.
// Keep the source graph and binary assets intact so the dashboard can render the same page.
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';

const site='https://admirable-kitsune-933239.netlify.app';
const origin=new URL(site).origin;
const dest=path.resolve('apps/web/public/accom-live');
const visited=new Set();
const manifest=[];
const queue=['/'];
const maxFiles=300,maxBytes=35000000;
let total=0;
const supported=/\.(?:html?|css|js|mjs|cjs|json|svg|png|webp|jpe?g|gif|ico|woff2?|ttf|otf|mp4|webm|avif|txt)$/i;
const htmlAttrs=/(?:src|href|poster|data-src|srcset)\s*=\s*["']([^"']+)["']/gi;
const cssRefs=/url\(\s*["']?([^)'"]+)["']?\s*\)|@import\s*["']([^"']+)["']/gi;
const jsRefs=/(?:from\s*|import\s*\(|new\s+URL\s*\()\s*["'`]([^"'`]+)["'`]/gi;
const assetRefs=/["'`](\/?assets\/[^"'`?\s)]+)["'`]/gi;
function local(u,base){
 try{
  const url=new URL(u,base);
  if(url.origin!==origin || /^(?:data:|mailto:|tel:|javascript:)/.test(u))return null;
  let name=decodeURIComponent(url.pathname);
  if(!name||name==='/')name='/index.html';
  if(name.includes('..')||name.includes('\\')||name.startsWith('/.'))return null;
  // Don't pull arbitrary navigable pages, API calls, or Netlify internals.
  if(name!='/index.html' && !supported.test(name))return null;
  return name;
 }catch{return null;}
}
function collect(s,base){
 for(const pattern of [htmlAttrs,cssRefs,jsRefs,assetRefs]){
  pattern.lastIndex=0;
  for(const m of s.matchAll(pattern)){
   const candidate=m[1]||m[2];
   if(!candidate)continue;
   for(const raw of (pattern===htmlAttrs&&m[0].startsWith('srcset')?candidate.split(',').map(x=>x.trim().split(/\s+/)[0]):[candidate])){
    const resolved=local(raw,base);
    if(resolved&&!visited.has(resolved)&&!queue.includes(resolved))queue.push(resolved);
   }
  }
 }
}
while(queue.length){
 if(visited.size>maxFiles||total>maxBytes)throw Error('Mirror size limit exceeded');
 const sourcePath=queue.shift();
 if(visited.has(sourcePath))continue;
 visited.add(sourcePath);
 const url=sourcePath==='/index.html'?site+'/':site+sourcePath;
 const res=await fetch(url,{redirect:'follow',headers:{'User-Agent':'Accom-Approved-Source-Capture/1.0'}});
 if(!res.ok){console.log('SKIPPED',sourcePath,res.status);continue}
 const bytes=Buffer.from(await res.arrayBuffer());
 if(bytes.length>10000000)throw Error('Individual asset too large: '+sourcePath);
 total+=bytes.length;
 const output=path.join(dest,sourcePath.slice(1));
 await mkdir(path.dirname(output),{recursive:true});
 await writeFile(output,bytes);
 const mime=res.headers.get('content-type')||'';
 manifest.push({path:sourcePath,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),type:mime});
 if(/(?:html|css|javascript|json|text)/.test(mime)||/\.(?:html?|css|js|mjs|json|svg)$/i.test(sourcePath)){
  collect(bytes.toString('utf8'),url);
 }
 console.log('CAPTURED',sourcePath,bytes.length);
}
if(!manifest.find(x=>x.path==='/index.html'))throw Error('Main HTML was not captured');
const html=await readFile(path.join(dest,'index.html'),'utf8');
for(const phrase of ['A closer look at the spaces','Payments & fees','Student reviews']){
 if(!html.includes(phrase))throw Error('Deployed source missing expected phrase: '+phrase);
}
const sections=[...html.matchAll(/<section\b[^>]*>/gi)].map(x=>x[0].slice(0,160));
await writeFile(path.join(dest,'source-manifest.json'),JSON.stringify({
  source:site, captured:new Date().toISOString(), count:manifest.length,
  totalBytes:total,sections,files:manifest,
},null,2));
console.log('CAPTURE COMPLETE',JSON.stringify({count:manifest.length,total,sections:sections.length}));
