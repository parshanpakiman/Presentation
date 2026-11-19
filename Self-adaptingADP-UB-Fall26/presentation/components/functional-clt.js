/* A finite-dimensional Gaussian-process illustration, not an optimized FALP CLT. */
(() => {
  'use strict';
  const root = document.querySelector('[data-functional-clt]');
  if (!root) return;
  const svg = root.querySelector('.fclt-chart'), ns = 'http://www.w3.org/2000/svg';
  const counts = [1, 4, 16, 64, 256], runs = 32, modes = 6, points = 113;
  const states = Array.from({length:points}, (_,i) => i/(points-1));
  const basis = s => [.65,.5*Math.cos(Math.PI*s),.5*Math.sin(Math.PI*s),.28*Math.cos(2*Math.PI*s),.28*Math.sin(2*Math.PI*s),.16*Math.sin(3*Math.PI*s)];
  const target = s => .8+1.3*s-.7*Math.exp(-(((s-.48)/.16)**2))+.22*Math.sin(3*Math.PI*s);
  const phi = states.map(basis), truth = states.map(target);
  const dot = (a,b) => a.reduce((v,x,k)=>v+x*b[k],0);
  const sigma = s => Math.sqrt(dot(basis(s),basis(s)));
  const gaussian = () => Math.sqrt(-2*Math.log(Math.max(Number.MIN_VALUE,Math.random())))*Math.cos(2*Math.PI*Math.random());
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const x = s => 58+650*s, y = v => 277-(v+1.7)/5.4*230;
  const rx = z => 952+z*38, floor = 277;
  let prefix, raw, n = 1, probe = .68, frame = 0, timer = 0, playing = false, generation = 0;
  let destination = 1, bound = false;
  function el(tag, attrs={}, text, parent=svg) {
    const node = document.createElementNS(ns,tag);
    Object.entries(attrs).forEach(([k,v])=>node.setAttribute(k,String(v)));
    if (text!==undefined) node.textContent=text;
    parent.append(node);return node;
  }
  const colors = () => {const c=getComputedStyle(root);return Object.fromEntries(['ink','muted','axis','line','target','estimate','new'].map(k=>[k,c.getPropertyValue('--fclt-'+k).trim()]));};
  const c=colors();
  // Build persistent SVG marks once; only data geometry changes during playback.
  const defs=el('defs');
  el('rect',{x:58,y:32,width:650,height:245},undefined,el('clipPath',{id:'fclt-function-clip'},undefined,defs));
  el('rect',{x:820,y:35,width:270,height:260},undefined,el('clipPath',{id:'fclt-normal-clip'},undefined,defs));
  [0,1,2].forEach(v=>el('line',{x1:58,x2:708,y1:y(v),y2:y(v),stroke:c.line,'stroke-width':1}));
  el('path',{d:'M58 32V277H708',stroke:c.axis,fill:'none','stroke-width':1.2});
  el('text',{x:58,y:20},'Value function');
  el('text',{x:383,y:330,'text-anchor':'middle'},'State s');
  el('text',{x:58,y:304,'text-anchor':'middle'},'0');
  el('text',{x:708,y:304,'text-anchor':'middle'},'1');
  el('path',{d:'M820 48V277H1090',stroke:c.axis,fill:'none','stroke-width':1.2});
  const peakLabel=el('text',{x:813,y:78,'text-anchor':'end',style:'font-size:14px'});
  el('text',{x:952,y:330,'text-anchor':'middle'},'Value at this state');
  const centerLabel=el('text',{x:952,y:304,'text-anchor':'middle',class:'fclt-math-label'},'V*(s₀)');
  const functions=el('g',{'clip-path':'url(#fclt-function-clip)'});
  const band=el('path',{fill:c.estimate,'fill-opacity':.07,stroke:'none'},undefined,functions);
  const paths=Array.from({length:runs},(_,i)=>el('path',{fill:'none',stroke:c.estimate,'stroke-width':i===0?2.8:1.3,'stroke-opacity':i===0?.95:.28},undefined,functions));
  const fresh=Array.from({length:3},()=>el('path',{fill:'none',stroke:c.new,'stroke-width':1.8,opacity:0},undefined,functions));
  const reference=el('path',{fill:'none',stroke:c.target,'stroke-width':3,'stroke-dasharray':'8 5',d:truth.map((v,i)=>(i?'L':'M')+x(states[i]).toFixed(2)+','+y(v).toFixed(2)).join(' ')},undefined,functions);
  const probeLine=el('line',{y1:35,y2:277,stroke:c.target,'stroke-width':1,'stroke-opacity':.6});
  const probeDot=el('circle',{r:5,fill:c.target,stroke:'#30353b','stroke-width':2});
  const probeLabel=el('text',{y:304,'text-anchor':'middle',class:'fclt-math-label'},'s₀');
  const hit=el('rect',{x:58,y:32,width:650,height:245,fill:'transparent',tabindex:0,role:'slider','aria-label':'Selected state','aria-valuemin':0,'aria-valuemax':1,'aria-valuenow':probe,style:'cursor:crosshair'});
  const normalGroup=el('g',{'clip-path':'url(#fclt-normal-clip)'});
  const normalFill=el('path',{fill:c.estimate,'fill-opacity':.14,stroke:'none'},undefined,normalGroup);
  const normalPath=el('path',{stroke:c.estimate,'stroke-width':3,fill:'none'},undefined,normalGroup);
  el('line',{x1:rx(0),x2:rx(0),y1:48,y2:277,stroke:c.target,'stroke-width':2,'stroke-dasharray':'5 5'});
  const dots=Array.from({length:runs},(_,i)=>el('circle',{r:i===0?4:2.6,fill:c.estimate,'fill-opacity':i===0?1:.55},undefined,normalGroup));
  const spreadLabel=el('text',{x:952,y:54,'text-anchor':'middle',style:'font-size:17px'});
  const screenReader=el('desc',{},undefined);
  function drawData() {
    generation++;
    raw=Array.from({length:runs},()=>Array.from({length:256},()=>Array.from({length:modes},gaussian)));
    prefix=raw.map(samples=>{const sum=Array(modes).fill(0);return [Array(modes).fill(0),...samples.map((v,i)=>v.map((z,k)=>(sum[k]+=z)/(i+1)))];});
    root.dataset.generation=String(generation);
  }
  function coefficient(run, value) {
    const lo=Math.max(1,Math.floor(value)), hi=Math.min(256,Math.ceil(value)), t=value-lo;
    return prefix[run][lo].map((v,k)=>v*(1-t)+prefix[run][hi][k]*t);
  }
  function curve(coeff) {return states.map((s,i)=>(i?'L':'M')+x(s).toFixed(2)+','+y(truth[i]+dot(coeff,phi[i])).toFixed(2)).join(' ');}
  function render(value, flash=0) {
    n=Math.max(1,Math.min(256,value));
    const scale=1/Math.sqrt(n), coeffs=Array.from({length:runs},(_,r)=>coefficient(r,n));
    paths.forEach((p,i)=>p.setAttribute('d',curve(coeffs[i])));
    const upper=states.map((s,i)=>[x(s),y(truth[i]+1.96*sigma(s)*scale)]);
    const lower=states.map((s,i)=>[x(s),y(truth[i]-1.96*sigma(s)*scale)]).reverse();
    band.setAttribute('d',[...upper,...lower].map(([a,b],i)=>(i?'L':'M')+a.toFixed(2)+','+b.toFixed(2)).join(' ')+'Z');
    fresh.forEach((p,i)=>{p.setAttribute('d',curve(raw[i][Math.min(255,Math.ceil(n)-1)]));p.setAttribute('opacity',String(flash*.46));});
    const sd=sigma(probe)*scale, peak=1/(sd*Math.sqrt(2*Math.PI));
    const profile=Array.from({length:181},(_,i)=>{const z=(-4.5+i*9/180)*sd;return [rx(z),floor-194*Math.exp(-.5*(z/sd)**2)];});
    // Include the exact center so the narrowest density has an accurate peak.
    profile.push([rx(0),floor-194]);profile.sort((a,b)=>a[0]-b[0]);
    const d=profile.map(([a,b],i)=>(i?'L':'M')+a.toFixed(2)+','+b.toFixed(2)).join(' ');
    normalPath.setAttribute('d',d);normalFill.setAttribute('d',`M${rx(-3.5)},${floor} ${d.replace(/^M/,'L')} L${rx(3.5)},${floor}Z`);
    peakLabel.textContent=peak.toFixed(2);
    spreadLabel.textContent='Spread ∝ 1/√N';
    dots.forEach((p,i)=>{p.setAttribute('cx',rx(dot(coeffs[i],basis(probe))).toFixed(2));p.setAttribute('cy',String(270-i%4*6));});
    probeLine.setAttribute('x1',x(probe));probeLine.setAttribute('x2',x(probe));
    probeDot.setAttribute('cx',x(probe));probeDot.setAttribute('cy',y(target(probe)));
    probeLabel.setAttribute('x',x(probe));hit.setAttribute('aria-valuenow',probe.toFixed(2));
    centerLabel.textContent='V*(s₀)';
    root.querySelector('[data-fclt-spread]').textContent=scale.toFixed(2);
    const active=counts.reduce((a,v)=>n>=v-.01?v:a,1);
    root.querySelectorAll('[data-fclt-stage]').forEach(e=>{if(Number(e.dataset.fcltStage)===active)e.setAttribute('aria-current','step');else e.removeAttribute('aria-current');});
    root.dataset.featureCount=String(Math.round(n));root.dataset.spread=String(scale);
    root.dataset.selectedState=String(probe);root.dataset.normalVariance=String(sd*sd);
    root.dataset.scaledVariance=String(sd*sd*n);
    screenReader.textContent=`${Math.round(n)} independent contributions per average. Standard deviation is ${scale.toFixed(3)} of its initial value. Selected state ${probe.toFixed(2)}.`;
  }
  function stop() {playing=false;clearTimeout(timer);cancelAnimationFrame(frame);root.dataset.animating='false';root.querySelector('[data-fclt-play]').textContent='Animate';}
  function animate(value) {
    cancelAnimationFrame(frame);destination=value;const from=n, began=performance.now();
    const duration=reduced?0:1700;
    root.dataset.animating='true';
    function tick(now) {
      const t=duration?Math.min(1,(now-began)/duration):1, ease=t*t*(3-2*t);
      render(from+(value-from)*ease,Math.sin(Math.PI*t));
      if(t<1)frame=requestAnimationFrame(tick);else {root.dataset.animating='false';render(value);}
    }
    frame=requestAnimationFrame(tick);
  }
  function stage() {return [...root.querySelectorAll('[data-fclt-n].visible')].reduce((i,e)=>Math.max(i,counts.indexOf(Number(e.dataset.fcltN))),0);}
  function sync(instant=false) {const next=stage();if(instant) {cancelAnimationFrame(frame);root.dataset.animating='false';render(counts[next]);} else animate(counts[next]);}
  function replay() {
    stop();cancelAnimationFrame(frame);drawData();
    if(window.Reveal?.isReady()&&root.closest('.reveal')) {const s=Reveal.getIndices();Reveal.slide(s.h,s.v,-1);}
    cancelAnimationFrame(frame);destination=1;root.dataset.animating='false';if(!root.closest('.reveal'))root.querySelector('.fclt-conclusion').classList.remove('visible');render(1);
  }
  function playStep() {
    if(!playing)return;
    const conclusion=root.querySelector('.fclt-conclusion');
    if(conclusion.classList.contains('visible')) {stop();return;}
    if(root.closest('.reveal')) Reveal.next();
    else {const next=counts.indexOf(Math.round(n))+1;if(next<counts.length)animate(counts[next]);else {conclusion.classList.add('visible');stop();return;}}
    timer=setTimeout(playStep,reduced?350:2600);
  }
  root.querySelector('[data-fclt-play]').addEventListener('click',()=>{
    if(playing){stop();return;}
    if(n>=256){replay();}
    playing=true;root.querySelector('[data-fclt-play]').textContent='Pause';
    if(Math.abs(n-destination)>.01){animate(destination);timer=setTimeout(playStep,reduced?350:2600);}else playStep();
  });
  root.querySelector('[data-fclt-replay]').addEventListener('click',replay);
  function select(clientX) {const p=svg.createSVGPoint();p.x=clientX;p.y=0;const local=p.matrixTransform(svg.getScreenCTM().inverse());probe=Math.max(.02,Math.min(.98,(local.x-58)/650));render(n);}
  let dragging=false;
  hit.addEventListener('pointerdown',e=>{dragging=true;hit.setPointerCapture(e.pointerId);select(e.clientX);});
  hit.addEventListener('pointermove',e=>{if(dragging)select(e.clientX);});
  hit.addEventListener('pointerup',()=>{dragging=false;});hit.addEventListener('pointercancel',()=>{dragging=false;});
  hit.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();e.stopPropagation();probe=e.key==='Home'?.02:e.key==='End'?.98:Math.max(.02,Math.min(.98,probe+(e.key==='ArrowRight'?.02:-.02)));render(n);});
  function bind() {
    if(bound)return;bound=true;
    Reveal.on('fragmentshown',e=>{if(e.fragment.matches('[data-fclt-n]'))sync();});
    Reveal.on('fragmenthidden',e=>{if(e.fragment.matches('[data-fclt-n]'))sync();});
    Reveal.on('slidechanged',()=>{stop();cancelAnimationFrame(frame);if(Reveal.getCurrentSlide().id==='feature-monte-carlo')sync(true);});
    sync(true);
  }
  drawData();render(1);root.dataset.ready='true';
  if(window.Reveal?.isReady())bind();else if(window.Reveal)Reveal.on('ready',bind);
})();
