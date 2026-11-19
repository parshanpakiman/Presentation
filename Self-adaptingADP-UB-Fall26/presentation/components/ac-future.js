/* Three illustrative mechanisms; the middle sketch solves only alpha and beta. */
(() => {
  'use strict';
  const root=document.querySelector('[data-ac-future]');if(!root)return;
  const style=getComputedStyle(root),c=Object.fromEntries(['bg','ink','muted','grid','policy','kernel','constraint','successor'].map(k=>[k,style.getPropertyValue('--ac-'+k).trim()]));
  const canvases=Object.fromEntries([...root.querySelectorAll('[data-ac-plot]')].map(e=>[e.dataset.acPlot,e.getContext('2d')]));if(Object.values(canvases).some(v=>!v))return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,durations=[0,4400,7200,4800];
  const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)),ease=x=>x*x*(3-2*x);
  let seed=111;const random=()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t^=t+Math.imul(t^t>>>7,61|t);return((t^t>>>14)>>>0)/4294967296;};
  const samples=Array.from({length:46},()=>[random(),random(),random()]);
  const cells=Array.from({length:320},(_,i)=>({x:(i%20+.5)/20,y:(Math.floor(i/20)+.5)/16}));
  const densityScores=cells.map(p=>.16+2.8*Math.exp(-((p.x-.31)**2+(p.y-.65)**2)/.022)+1.7*Math.exp(-((p.x-.75)**2+(p.y-.34)**2)/.035));
  const densityTotal=densityScores.reduce((a,b)=>a+b,0),proposal=densityScores.map(x=>x/densityTotal);
  const xs=Array.from({length:121},(_,i)=>i/120),knots=Array.from({length:3},()=>{const u=random();let total=0,index=proposal.findIndex(p=>(total+=p)>=u);return (index%20+random())/20;}),feature=(x,z)=>Math.exp(-(((x-z)/.095)**2));
  const base=xs.map(x=>.5+.12*x+.10*Math.sin(6*x));
  const target=xs.map((x,i)=>base[i]+.30*feature(x,knots[0])-.22*feature(x,knots[1])+.26*feature(x,knots[2]));
  const fits=[];let aggregate=base;
  for(const z of knots){
    const phi=xs.map(x=>feature(x,z)),sum=f=>xs.reduce((v,_,i)=>v+f(i),0);
    const a=sum(i=>aggregate[i]**2),b=sum(i=>aggregate[i]*phi[i]),d=sum(i=>phi[i]**2),u=sum(i=>aggregate[i]*target[i]),v=sum(i=>phi[i]*target[i]),det=a*d-b*b;
    if(det<=0)throw Error('Two-parameter convex sketch is not strictly convex.');
    const alpha=(d*u-b*v)/det,beta=(a*v-b*u)/det,next=aggregate.map((y,i)=>alpha*y+beta*phi[i]);
    fits.push({old:aggregate,phi,alpha,beta,next});aggregate=next;
  }
  const nodes=Array.from({length:35},(_,i)=>{const x=.07+(i%7)*.143,y=.09+Math.floor(i/7)*.205;const score=.08+.85*Math.exp(-((x-.8)**2+(y-.69)**2)/.045)+.65*Math.exp(-((x-.32)**2+(y-.3)**2)/.027);return{x,y,score};});
  let phase=0,progress=0,frame=0,timer=0,playing=false,advancing=false,bound=false;
  function begin(ctx){ctx.setTransform(2,0,0,2,0,0);ctx.clearRect(0,0,380,260);}
  function line(ctx,pts,color,width=1,alpha=1,dash=[]){ctx.save();ctx.globalAlpha=alpha;ctx.strokeStyle=color;ctx.lineWidth=width;ctx.setLineDash(dash);ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();ctx.restore();}
  function dot(ctx,x,y,r,color,alpha=1){ctx.save();ctx.globalAlpha=alpha;ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,2*Math.PI);ctx.fill();ctx.restore();}
  function text(ctx,s,x,y,color=c.muted,size=16,align='left'){ctx.font=`${size}px "Avenir Next", "Segoe UI", sans-serif`;ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(s,x,y);}
  function axes(ctx,xLabel,yLabel){line(ctx,[[44,27],[44,216],[359,216]],c.grid,1,.8);text(ctx,xLabel,201,247,c.muted,16,'center');ctx.save();ctx.translate(15,121);ctx.rotate(-Math.PI/2);text(ctx,yLabel,0,0,c.muted,16,'center');ctx.restore();}
  function sampling(t){const ctx=canvases.sampling;begin(ctx);const w=ease(t),mass=proposal.map(p=>(1-w)/320+w*p),max=Math.max(...mass),xy=p=>[44+p[0]*315,216-p[1]*189];
    cells.forEach((p,i)=>{ctx.globalAlpha=.06+.56*mass[i]/max;ctx.fillStyle=c.policy;ctx.fillRect(44+p.x*315-315/40,216-p.y*189-189/32,315/20+.2,189/16+.2);});ctx.globalAlpha=1;
    const visits=Array.from({length:32},(_,i)=>{const x=.12+.74*i/31;return xy([x,.5+.18*Math.sin(7*x)]);});line(ctx,visits,c.policy,1.6,.8,[4,3]);
    for(const p of [[.31,.65],[.75,.34]]){const [x,y]=xy(p);line(ctx,[[x-4,y-4],[x+4,y+4]],c.constraint,2);line(ctx,[[x-4,y+4],[x+4,y-4]],c.constraint,2);dot(ctx,x+11,y-9,3,c.successor);}
    const cdf=[];proposal.reduce((v,p,i)=>(cdf[i]=v+p),0);
    samples.forEach(([u,jx,jy])=>{let i=cdf.findIndex(p=>u<=p);if(i<0)i=319;const target=[(i%20+jx)/20,(Math.floor(i/20)+jy)/16],p=[u*(1-w)+target[0]*w,jx*(1-w)+target[1]*w],[x,y]=xy(p);dot(ctx,x,y,3,c.kernel,.92);});
    axes(ctx,'Feature center z₁','Feature center z₂');dot(ctx,54,12,3,c.kernel);text(ctx,'New feature draws',63,17,c.kernel,15);
    root.querySelector('[data-ac-status="sampling"]').textContent=t<.02?'Uniform feature draws':t<1?'Update where features are sampled':'Feedback-directed feature draws';
    root.dataset.samplingMass=String(mass.reduce((a,b)=>a+b,0));root.dataset.samplingEntropy=String(-mass.reduce((a,p)=>a+p*Math.log(p),0));
  }
  function oneAtATime(t,active){const ctx=canvases.aggregate;begin(ctx);const index=active?Math.min(2,Math.floor(t*3)):0,within=t===1?1:t*3-index,fit=fits[index],fraction=active?ease(clamp(within/.76)):0,alpha=1+(fit.alpha-1)*fraction,beta=fit.beta*fraction;
    const x=s=>44+315*s,y=v=>216-165*v,scaled=fit.old.map(v=>alpha*v),current=scaled.map((v,i)=>v+beta*fit.phi[i]);
    line(ctx,[[44,27],[44,216],[359,216]],c.grid,1,.8);
    for(let k=0;k<index;k++)line(ctx,xs.map((s,i)=>[x(s),y(fits[k].old[i])]),c.muted,1,.15);
    ctx.save();ctx.fillStyle=c.kernel;ctx.globalAlpha=.17;ctx.beginPath();xs.forEach((s,i)=>i?ctx.lineTo(x(s),y(current[i])):ctx.moveTo(x(s),y(current[i])));[...xs].reverse().forEach((s,j)=>ctx.lineTo(x(s),y(scaled[xs.length-1-j])));ctx.closePath();ctx.fill();ctx.restore();
    line(ctx,xs.map((s,i)=>[x(s),y(fit.old[i])]),c.muted,2,.9,[5,4]);line(ctx,xs.map((s,i)=>[x(s),y(current[i])]),c.kernel,3,.95);
    const cx=x(knots[index]),ci=Math.round(knots[index]*120);dot(ctx,cx,y(current[ci]),4,c.kernel);
    text(ctx,'Fixed aggregate',53,17,c.muted,15);text(ctx,'+ 1 feature',257,17,c.kernel,15);text(ctx,'State s',201,247,c.muted,16,'center');ctx.save();ctx.translate(15,124);ctx.rotate(-Math.PI/2);text(ctx,'Approximation',0,0,c.muted,16,'center');ctx.restore();
    root.querySelector('[data-ac-status="aggregate"]').textContent=!active?'Fix the current approximation':within<.76?`Fix aggregate → add feature ${index+1}`:t<1?'Fix the result → add the next feature':'Fix the updated aggregate; repeat';
    root.dataset.optimizedParameters=String(active?2:0);root.dataset.activeRandomFeatures=String(active?1:0);root.dataset.correctionRound=String(active?index+1:0);root.dataset.aggregateScale=String(alpha);
  }
  function learning(t){const ctx=canvases.constraints;begin(ctx);axes(ctx,'State s','Action a');const learned=ease(t),normalizer=nodes.reduce((a,p)=>a+Math.exp(3.3*p.score*learned),0);let maxWeight=0;
    nodes.forEach((p,i)=>{const weight=Math.exp(3.3*p.score*learned)/normalizer;maxWeight=Math.max(maxWeight,weight);const x=44+p.x*315,y=216-p.y*189,importance=(1-learned)*.14+learned*p.score,uncertainty=(1-learned)*.85+.15*(1-p.score)*learned;
      ctx.save();ctx.globalAlpha=.40;ctx.strokeStyle=c.muted;ctx.setLineDash([2,3]);ctx.beginPath();ctx.arc(x,y,4+8*uncertainty,0,2*Math.PI);ctx.stroke();ctx.restore();dot(ctx,x,y,3+10*importance,c.constraint,.3+.65*importance);
      if(t>0&&t<1&&importance>.35){const angle=t*12+i;dot(ctx,x+13*Math.cos(angle),y+13*Math.sin(angle),2.7,c.successor,.9);}
    });
    dot(ctx,57,11,4,c.constraint);text(ctx,'Importance',67,17,c.constraint,15);line(ctx,[[195,12],[215,12]],c.muted,1,.8,[2,3]);text(ctx,'Uncertainty',222,17,c.muted,15);
    root.querySelector('[data-ac-status="constraints"]').textContent=t<.02?'Start without importance information':t<1?'Learn importance; focus observations':'Identify the restrictive constraints';root.dataset.maxConstraintWeight=String(maxWeight);root.dataset.constraintWeightMass=String(nodes.reduce((a,p)=>a+Math.exp(3.3*p.score*learned)/normalizer,0));
  }
  function render(stage,t){phase=stage;progress=t;sampling(stage===0?0:stage===1?t:1);oneAtATime(stage<2?0:stage===2?t:1,stage>=2);learning(stage<3?0:t);root.dataset.stage=String(stage);root.dataset.progress=t.toFixed(3);}
  function stop(freeze=false){playing=false;clearTimeout(timer);if(freeze){cancelAnimationFrame(frame);root.dataset.animating='false';}root.querySelector('[data-ac-play]').textContent='Play all';}
  function activeStage(){return root.closest('.reveal')?Math.max(0,...Array.from(root.querySelectorAll('[data-ac-stage].visible'),e=>Number(e.dataset.acStage))):phase;}
  function setStage(next,animate=true,start=0){cancelAnimationFrame(frame);phase=next;progress=start;root.querySelectorAll('[data-ac-idea]').forEach(e=>{if(Number(e.dataset.acIdea)===next)e.setAttribute('aria-current','step');else e.removeAttribute('aria-current');});if(!animate||reduced||next===0){root.dataset.animating='false';render(next,1);return;}root.dataset.animating='true';const began=performance.now()-start*durations[next];function tick(now){const t=clamp((now-began)/durations[next]);render(next,t);if(t<1)frame=requestAnimationFrame(tick);else root.dataset.animating='false';}frame=requestAnimationFrame(tick);}
  function replay(){stop();cancelAnimationFrame(frame);if(root.closest('.reveal')&&window.Reveal?.isReady()){const i=Reveal.getIndices();Reveal.slide(i.h,i.v,-1);}cancelAnimationFrame(frame);setStage(0,false);}
  function autoplay(){if(!playing)return;if(phase>=3){stop();return;}advancing=true;if(root.closest('.reveal'))Reveal.next();else setStage(phase+1);advancing=false;timer=setTimeout(autoplay,reduced?450:durations[phase]+700);}
  root.querySelector('[data-ac-play]').addEventListener('click',()=>{if(playing){stop(true);return;}if(phase>=3&&progress>=1)replay();playing=true;root.querySelector('[data-ac-play]').textContent='Pause';if(phase>0&&progress<1){const remaining=1-progress;setStage(phase,true,progress);timer=setTimeout(autoplay,reduced?450:durations[phase]*remaining+700);}else autoplay();});root.querySelector('[data-ac-replay]').addEventListener('click',replay);
  function bind(){if(bound)return;bound=true;for(const name of ['fragmentshown','fragmenthidden'])Reveal.on(name,e=>{if(root.contains(e.fragment)){if(!advancing)stop();setStage(activeStage(),name==='fragmentshown');}});Reveal.on('slidechanged',()=>{stop();cancelAnimationFrame(frame);root.dataset.animating='false';if(Reveal.getCurrentSlide().id==='sg-future-features')setStage(activeStage(),false);});setStage(activeStage(),false);}
  if(root.closest('.reveal')){setStage(0,false);if(window.Reveal?.isReady())bind();else window.Reveal?.on('ready',bind);}else setStage(3,false);root.dataset.ready='true';
})();
