// Real browsers, real downloads, a stopped server, and a fresh-context restore.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn, spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = path.resolve(process.env.TLR_SOURCE_ROOT || path.join(path.dirname(fileURLToPath(import.meta.url)), '..'));
const require = createRequire(pathToFileURL(path.join(root, 'package.json')));
const playwright = require('playwright');
const python = process.env.PYTHON || 'python';
const browserNames = (process.env.TLR_BROWSERS || 'chromium').split(',');
assert(browserNames.length && browserNames.every(name => ['chromium', 'firefox'].includes(name)), 'Choose Chromium or Firefox.');
assert.equal(new Set(browserNames).size, browserNames.length, 'No duplicate browser runs.');
const place = fs.mkdtempSync(path.join(os.tmpdir(), 'last-release-browser-'));
let attempts = 0, fixtureAccounts = 0;
const browserVersions = {};
const start = Date.now();

function runPython(...args) {
  const result = spawnSync(python, args, {cwd:root, encoding:'utf8', timeout:30000});
  assert.equal(result.status, 0, result.stderr || result.error?.message || 'Python command failed.');
  return result.stdout;
}
function readPayload(file) {
  const html = fs.readFileSync(file, 'utf8');
  const embedded = html.match(/<script id="notebook-data" type="application\/octet-stream">([^<]+)<\/script>/);
  assert(embedded, 'The downloaded file must contain its data.');
  return JSON.parse(Buffer.from(embedded[1], 'base64').toString('utf8'));
}
async function offlineContext(browser) {
  const context = await browser.newContext({acceptDownloads:true});
  await context.setOffline(true);
  context.httpAttempts=0;
  context.on('request', request => { if (/^https?:/i.test(request.url())) context.httpAttempts++; });
  await context.addInitScript(() => {
    window.__offlinePolicyViolations=[];
    document.addEventListener('securitypolicyviolation', event => {
      if (/^https?:/i.test(event.blockedURI)) window.__offlinePolicyViolations.push(event.blockedURI);
    });
  });
  return context;
}
async function observedAttempts(context) {
  let count=context.httpAttempts;
  for(const page of context.pages()) count+=await page.evaluate(()=>window.__offlinePolicyViolations?.length || 0);
  return count;
}
async function closeOffline(context) {
  attempts+=await observedAttempts(context);
  await context.close();
}
async function openEdition(context, file) {
  const page = await context.newPage(), errors=[];
  page.on('pageerror', error => errors.push(error.message));
  page.on('dialog', dialog => dialog.accept());
  await page.goto(pathToFileURL(file).href);
  await page.waitForFunction(() => document.querySelector('#connection-label').textContent.includes('Offline edition'));
  assert.equal(errors.length,0,'Offline code must execute without errors.');
  assert.equal(await page.evaluate(() => window.INJECTED),undefined,'Note contents must stay inert.');
  return page;
}
async function waitCount(page, count) {
  await page.waitForFunction(value => document.querySelector('#note-count').textContent === String(value), count);
}
async function saveBackup(page, filename) {
  const waiting = page.waitForEvent('download');
  await page.locator('#save-backup').click();
  const download = await waiting;
  await download.saveAs(filename);
  assert.equal(await download.failure(), null);
  return JSON.parse(fs.readFileSync(filename,'utf8'));
}
async function exerciseEdition(browser, file, suffix) {
  const original = readPayload(file), count=original.notes.length;
  assert(original.account,'Private edition must have an account.');
  const context = await offlineContext(browser);
  const page = await openEdition(context,file);
  await waitCount(page,count);
  const note = original.notes[0];
  if (note) {
    await page.locator('#search').fill(note.body.slice(0,15));
    assert(await page.locator(`button[data-note-id="${note.id}"]`).count(),'Search must find body text.');
    await page.locator('#search').fill('');
    await page.locator(`button[data-note-id="${note.id}"]`).click();
    assert.equal(await page.locator('#note-body').inputValue(),note.body,'Original text must be exact.');
  }
  await page.locator('#new-note').click();
  await page.locator('#note-title').fill('After the goodbye');
  await page.locator('#note-body').fill('Written with no server. Café 🌱');
  await page.locator('#save-note').click();
  await waitCount(page,count+1);
  await page.locator('#delete-note').click();
  await waitCount(page,count);
  if (!note) {
    await page.locator('#new-note').click();
    await page.locator('#note-title').fill('My first surviving thought');
    await page.locator('#note-body').fill('Starting from an empty notebook.');
    await page.locator('#save-note').click();
    await waitCount(page,1);
  }
  const edited = note || {id:await page.locator('.note-item[aria-current=true]').getAttribute('data-note-id'), body:'Starting from an empty notebook.'};
  await page.locator(`button[data-note-id="${edited.id}"]`).click();
  const newBody=edited.body+'\nStill here after the goodbye 🌱';
  await page.locator('#note-body').fill(newBody);
  // A backup must never silently omit an unsaved editor draft.
  await page.locator('#save-backup').click();
  await page.waitForFunction(() => document.querySelector('#message').textContent.includes('Save the note'));
  await page.locator('#save-note').click();
  await page.waitForFunction(() => document.querySelector('#save-state').textContent.includes('Changes are in memory'));
  const backupFile=path.join(place,`backup-${suffix}.json`), backup=await saveBackup(page,backupFile);
  assert.equal(backup.account.id,original.account.id);
  assert.equal(backup.notes.find(n=>n.id===edited.id).body,newBody);
  const invalids = [
    {...backup,account:{...backup.account,id:'00000000-0000-4000-8000-000000000099'}},
    {...backup,notes:[backup.notes[0],backup.notes[0]]},
    {...backup,notes:backup.notes.map((n,i)=>i ? n : {...n,body:'é'.repeat(8193)})}
  ];
  for (let i=0;i<invalids.length;i++) {
    const bad=path.join(place,`invalid-${suffix}-${i}.json`);
    fs.writeFileSync(bad,JSON.stringify(invalids[i]));
    await page.locator('#open-backup').setInputFiles(bad);
    await page.waitForFunction(() => /another account|duplicate|16 KiB/.test(document.querySelector('#message').textContent));
    assert.equal(await page.locator('#note-body').inputValue(),newBody,'Failed import must leave work intact.');
    await waitCount(page,backup.notes.length);
  }
  // Native labels, keyboard navigation, and unsaved-work notices are part of the promise.
  await page.locator('#search').focus();
  await page.keyboard.press('Tab');
  assert(await page.evaluate(()=>document.activeElement.tagName==='BUTTON'));
  for (const id of ['search','note-title','note-body']) assert(await page.locator(`label[for="${id}"]`).count());
  const notice=await page.evaluate(()=>{
    document.querySelector('#note-body').value += ' an unsaved draft';
    document.querySelector('#note-body').dispatchEvent(new Event('input',{bubbles:true}));
    const event=new Event('beforeunload',{cancelable:true});
    window.dispatchEvent(event); return event.defaultPrevented;
  });
  assert(notice,'Unsaved work must have an unload warning.');
  await closeOffline(context);
  const fresh=await offlineContext(browser), restored=await openEdition(fresh,file);
  await restored.locator('#open-backup').setInputFiles(backupFile);
  await restored.waitForFunction(()=>document.querySelector('#message').textContent.includes('Backup restored'));
  await restored.locator(`button[data-note-id="${edited.id}"]`).click();
  assert.equal(await restored.locator('#note-body').inputValue(),newBody,'An edit must survive a new browser context.');
  const roundTrip=await saveBackup(restored,path.join(place,`roundtrip-${suffix}.json`));
  assert.deepEqual(roundTrip,backup,'Restoring must preserve every note and timestamp.');
  await closeOffline(fresh);
}
async function liveDownloadAndStop(browser,name) {
  const db=path.join(place,`live-${name}.sqlite3`), keysFile=path.join(place,`keys-${name}.json`);
  runPython(path.join(root,'app.py'),'seed','--db',db,'--keys',keysFile);
  const keys=JSON.parse(fs.readFileSync(keysFile,'utf8'));
  const server=spawn(python,[path.join(root,'app.py'),'serve','--db',db,'--port','0'],{cwd:root,stdio:['ignore','pipe','pipe']});
  let stdout='', stderr='';
  server.stderr.on('data',chunk=>stderr+=chunk);
  const exited=new Promise(resolve=>server.once('exit',(code,signal)=>resolve({code,signal})));
  const url=await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error('Own server failed to start: '+stderr)),10000);
    server.stdout.on('data',chunk=>{stdout+=chunk;const match=stdout.match(/http:\/\/127\.0\.0\.1:\d+/);if(match){clearTimeout(timer);resolve(match[0]);}});
    server.once('error',error=>{clearTimeout(timer);reject(error);});
    server.once('exit',()=>{clearTimeout(timer);reject(Error('Own server exited before startup: '+stderr));});
  });
  const files=[];
  try {
    for (const alias of ['Alice','Bob']) {
      const context=await browser.newContext({acceptDownloads:true}), page=await context.newPage();
      page.on('dialog',dialog=>dialog.accept());
      await page.goto(url);
      await page.locator('#access-token').fill(keys[alias].token);
      await page.getByRole('button',{name:'Open notebook',exact:true}).click();
      await waitCount(page,3);
      const expected=await (await fetch(url+'/api/notes',{headers:{Authorization:'Bearer '+keys[alias].token}})).json();
      const waiting=page.waitForEvent('download');
      await page.locator('#download-edition').click();
      const download=await waiting, file=path.join(place,`private-${name}-${alias}.html`);
      await download.saveAs(file);
      const payload=readPayload(file);
      assert.deepEqual(payload.notes,expected.notes,'Live download must preserve exactly this account.');
      assert.equal(payload.account.id,keys[alias].id);
      assert(!JSON.stringify(payload).includes((alias==='Alice'?'BOB':'ALICE')+'_PRIVATE_CANARY'));
      for (const account of Object.values(keys)) assert(!JSON.stringify(payload).includes(account.token));
      files.push(file); await context.close();
    }
  } finally {
    // This PID is the disposable child created above, never the owner's server.
    server.kill();
    await exited;
  }
  await assert.rejects(fetch(url+'/api/status'),'The original fixture server must be unreachable.');
  for(let i=0;i<files.length;i++) {await exerciseEdition(browser,files[i],`${name}-fixture-${i}`);fixtureAccounts++;}
}
async function emptyReader(browser,name) {
  const out=path.join(place,'public-'+name);
  runPython(path.join(root,'release.py'),'public','--root',root,'--out',out);
  const context=await offlineContext(browser), page=await openEdition(context,path.join(out,'index.html'));
  await waitCount(page,0);
  const backup=path.join(place,'empty-import-'+name+'.json');
  fs.writeFileSync(backup,JSON.stringify({version:1,account:{id:'00000000-0000-4000-8000-000000000123',alias:'Empty account'},notes:[]}));
  await page.locator('#open-backup').setInputFiles(backup);
  await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('Backup restored'));
  await page.locator('#new-note').click();
  await page.locator('#note-title').fill('A new beginning');
  await page.locator('#note-body').fill('The empty reader can keep going.');
  await page.locator('#save-note').click();
  await waitCount(page,1);
  assert.equal((await saveBackup(page,path.join(place,'empty-saved-'+name+'.json'))).notes.length,1);
  await closeOffline(context);
}

async function dependencyCanary(browser,name) {
  const template=fs.readFileSync(path.join(place,'public-'+name,'sample.html'),'utf8');
  const old=template.match(/<script id="notebook-code">([\s\S]*?)<\/script>/)[1];
  const code=old+'\nfetch("https://offline-canary.invalid/resource").catch(()=>{});\n';
  const hash=crypto.createHash('sha256').update(code).digest('base64');
  const broken=template.replace(old,code).replace(/script-src 'sha256-[^']+'/,"script-src 'sha256-"+hash+"'");
  const file=path.join(place,'blocked-dependency-'+name+'.html');fs.writeFileSync(file,broken);
  const context=await offlineContext(browser), page=await openEdition(context,file);
  await page.waitForFunction(()=>window.__offlinePolicyViolations.length>0);
  assert(await observedAttempts(context)>0,'A dependency attempt blocked by CSP must still be detected.');
  // This deliberately failing synthetic canary is excluded from the passing edition's metric.
  await context.close();
}

try {
  for (const name of browserNames) {
    let options={headless:true};
    if (name==='chromium' && process.env.TLR_CHROMIUM_EXECUTABLE) options.executablePath=process.env.TLR_CHROMIUM_EXECUTABLE;
    else if (name==='chromium' && !fs.existsSync(playwright.chromium.executablePath())) options.channel='chrome';
    const browser=await playwright[name].launch(options);
    browserVersions[name]=browser.version();
    try {
      await liveDownloadAndStop(browser,name);
      await emptyReader(browser,name);
      await dependencyCanary(browser,name);
      if(process.env.TLR_CANDIDATE) {
        const candidate=process.env.TLR_CANDIDATE, manifest=JSON.parse(fs.readFileSync(path.join(candidate,'manifest.json'),'utf8'));
        for(let i=0;i<manifest.accounts.length;i++) await exerciseEdition(browser,path.join(candidate,manifest.accounts[i].file),`${name}-candidate-${i}`);
      }
    } finally { await browser.close(); }
    console.log(`${name}: private downloads, stopped server, offline CRUD, backup and fresh-context restore passed.`);
  }
  assert.equal(attempts,0,'Every offline HTTP(S) attempt is a failure.');
  const candidate=process.env.TLR_CANDIDATE;
  const manifestBytes=candidate?fs.readFileSync(path.join(candidate,'manifest.json')):null;
  const report={version:1,browsers:browserNames,browser_versions:browserVersions,accounts_checked:candidate?JSON.parse(manifestBytes).accounts.length:2,
    fixture_accounts_checked:fixtureAccounts,http_attempts:attempts,original_fixture_server_stopped:true,
    manifest_sha256:manifestBytes?crypto.createHash('sha256').update(manifestBytes).digest('hex'):null,
    duration_ms:Date.now()-start};
  const reportPath=process.env.TLR_BROWSER_REPORT||path.join(root,'test-results/browser-report.json');
  fs.mkdirSync(path.dirname(reportPath),{recursive:true});fs.writeFileSync(reportPath,JSON.stringify(report,null,2));
  console.log(`Zero offline HTTP(S) attempts. Browser evidence: ${reportPath}`);
} finally {
  // The temporary directory was created by this process, under the system temp root.
  const resolved=path.resolve(place), tempRoot=path.resolve(os.tmpdir())+path.sep;
  assert(resolved.startsWith(tempRoot)&&path.basename(resolved).startsWith('last-release-browser-'));
  fs.rmSync(resolved,{recursive:true,force:true});
}
