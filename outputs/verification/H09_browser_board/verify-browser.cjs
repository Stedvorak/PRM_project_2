const fs = require('node:fs');
const path = require('node:path');
const out = path.resolve('outputs/verification/H09_browser_board');
(async () => {
  const targets = await (await fetch('http://127.0.0.1:9223/json/list')).json();
  const target = targets.find(t => t.type === 'page');
  if (!target) throw new Error('No real Edge page target');
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map(); let id = 0;
  const responses = [], exceptions = [];
  socket.addEventListener('message', e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id); pending.delete(m.id);
      m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result);
    }
    if (m.method === 'Network.responseReceived' && m.params.response.url.startsWith('http://192.168.4.1/'))
      responses.push({url:m.params.response.url,status:m.params.response.status});
    if (m.method === 'Runtime.exceptionThrown') exceptions.push(m.params.exceptionDetails);
  });
  await new Promise((resolve,reject) => {socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  const send = (method,params={}) => new Promise((resolve,reject) => {
    const next=++id; pending.set(next,{resolve,reject});socket.send(JSON.stringify({id:next,method,params}));
  });
  await send('Page.enable'); await send('Network.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:1450,deviceScaleFactor:1,mobile:false});
  const browser = await send('Browser.getVersion');
  await send('Page.navigate',{url:'http://192.168.4.1/'});
  await new Promise(r=>setTimeout(r,4500));
  const expression = `JSON.stringify(Object.fromEntries(['stateTitle','stateIdText','heroConfidenceText','statusText','signalStatus','deviceTime','valProbCalm','valProbFast','valProbUnattached','valProbShaking'].map(id=>[id,document.getElementById(id)?.textContent])))`;
  const snapshot = async () => JSON.parse((await send('Runtime.evaluate',{expression,returnByValue:true})).result.value);
  const before = await snapshot();
  await new Promise(r=>setTimeout(r,3000));
  const after = await snapshot();
  const screenshot = await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  fs.writeFileSync(path.join(out,'live-page.png'),Buffer.from(screenshot.data,'base64'));
  const html = await send('Runtime.evaluate',{expression:'document.documentElement.outerHTML',returnByValue:true});
  fs.writeFileSync(path.join(out,'rendered-page.html'),html.result.value);
  const report={source:'actual Microsoft Edge rendering of real ESP32 HTTP page',browser,before,after,responses,exceptions,
    liveStatusAdvanced:before.deviceTime!==after.deviceTime,liveSignalAdvanced:before.signalStatus!==after.signalStatus,
    connected:after.statusText.includes('Connected'),realSamplesRendered:after.signalStatus.includes('real samples'),
    apiStatusResponses:responses.filter(r=>r.url.endsWith('/api/status')&&r.status===200).length,
    apiSignalResponses:responses.filter(r=>r.url.endsWith('/api/signal')&&r.status===200).length};
  report.passed=report.liveStatusAdvanced&&report.liveSignalAdvanced&&report.connected&&report.realSamplesRendered&&exceptions.length===0;
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
  socket.close();
  if(!report.passed) process.exitCode=2;
})().catch(e=>{console.error(e);process.exitCode=2;});
