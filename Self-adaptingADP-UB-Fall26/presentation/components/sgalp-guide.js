(() => {
 const root=document.querySelector('[data-sg-guide]');if(!root)return;
 const ns='http://www.w3.org/2000/svg',n=120,xs=Array.from({length:n+1},(_,i)=>i/n);
 const base=xs.map(x=>.9+.15*x+.18*Math.cos(2*Math.PI*x));
 const guided1=base.map((v,i)=>v+.48*Math.sin(Math.PI*xs[i])**2),guided2=guided1.map((v,i)=>v+.32*Math.sin(2*Math.PI*xs[i])**2);
 const guided3=guided2.map((v,i)=>v+.24*Math.sin(Math.PI*xs[i])**2);
 const free1=base.map((v,i)=>v+.2+.4*Math.sin(2*Math.PI*xs[i])),free2=free1.map((v,i)=>v+.17+.3*Math.cos(2*Math.PI*xs[i]));
 const free3=free2.map((v,i)=>v+.14+.26*Math.sin(4*Math.PI*xs[i]));
 if(guided3.some((v,i)=>v<guided2[i]-1e-10)||guided1.some((v,i)=>v<base[i]-1e-10)||guided2.some((v,i)=>v<guided1[i]-1e-10))throw new Error('Guide floor violation.');root.dataset.verified='true';
// Illustrative upper reference shared by both plots and every round.
const optimal=xs.map(x=>2.17+.26*Math.sin(2*Math.PI*x+.5)+.07*x);
const approximations=[base,guided1,guided2,guided3,free1,free2,free3];
if (approximations.some(curve=>curve.some((value,i)=>value>=optimal[i]))) {
  throw new Error('Approximation exceeds the optimal value reference.');
}
// Include the upper reference when choosing the fixed vertical range.
 const allValues=[...approximations.flat(),...optimal];
 const valueMin=Math.min(0,...allValues),valueMax=Math.max(...allValues);
 const range=(valueMax-valueMin)*1.12||1;
 const plotY=v=>256-228*(v-valueMin)/range;
 if(allValues.some(v=>plotY(v)<20||plotY(v)>265))throw new Error('Comparison curve exceeds the plot area.');
 function add(svg,tag,attrs,text){const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));if(text)e.textContent=text;svg.append(e);return e;}
function markDips(svg,floor,values,x,y) {
  let points=[];
  function flush() {
    if (points.length<2) return;
    const top=points.map(([i,high],j)=>(j?'L':'M')+x(i)+','+y(high)).join(' ');
    const bottom=[...points].reverse().map(([i,,low])=>'L'+x(i)+','+y(low)).join(' ');
    add(svg,'path',{class:'sg-dip-region',d:top+' '+bottom+' Z',fill:'#efaa635c'});
    const left=x(points[0][0]),right=x(points.at(-1)[0]);
    add(svg,'rect',{class:'sg-dip-axis-band',x:left,y:270,width:right-left,height:12,rx:2,fill:'#d77624'});
    points=[];
  }
  for (let i=0;i<=n;i++) {
    const gap=floor[i]-values[i];
    const previousGap=i>0?floor[i-1]-values[i-1]:0;
    if (i>0&&(gap>0)!==(previousGap>0)) {
      const fraction=previousGap/(previousGap-gap);
      const crossing=floor[i-1]+fraction*(floor[i]-floor[i-1]);
      points.push([i-1+fraction,crossing,crossing]);
    }
    if (gap>0) points.push([i,floor[i],values[i]]);
    else if (points.length>1) flush();
  }
  flush();
}
 function graph(svg,floor,values,guided){svg.replaceChildren();const purple='#78508d',color=svg.hasAttribute('data-sg-guided')?purple:'#226a85',x=i=>40+490*i/n,y=plotY,path=vs=>vs.map((v,i)=>(i?'L':'M')+x(i)+','+y(v)).join(' ');
  add(svg,'path',{d:'M40 18V276H530',fill:'none',stroke:'#acbec6'});add(svg,'text',{x:285,y:306,'text-anchor':'middle','font-size':22,fill:'#6d848e'},'state');
  if(guided){add(svg,'path',{d:path(floor)+' L530 276H40Z',fill:'#ead8b6','fill-opacity':.6});add(svg,'text',{x:285,y:263,'text-anchor':'middle','font-size':22,fill:'#8b642d'},'Below the previous VFA');}
  else if (root.dataset.stage!=='0') markDips(svg,floor,values,x,y);
  if(root.dataset.stage!=='0')add(svg,'path',{d:path(floor),fill:'none',stroke:'#8a96a1','stroke-width':2,'stroke-dasharray':'5 4'});add(svg,'path',{d:path(values),fill:'none',stroke:color,'stroke-width':3});
  add(svg,'path',{class:'sg-optimal-curve',d:path(optimal),fill:'none',stroke:'#253444','stroke-width':2.5});
  if(guided)[0,n/2,n].forEach(i=>{if(Math.abs(values[i]-floor[i])<1e-8)add(svg,'circle',{cx:x(i),cy:y(values[i]),r:4,fill:'white',stroke:purple,'stroke-width':1.7});});
 }
 function stage(){if(!root.closest('.reveal'))return 3;return Math.max(0,...[...root.querySelectorAll('.sg-round-step.visible')].map(e=>Number(e.dataset.round)));}
 let animation,last=-1;
 function draw(s,t){root.dataset.stage=String(s);if(s===0){graph(root.querySelector('[data-sg-guided]'),base,base,false);graph(root.querySelector('[data-sg-unguided]'),base,base,false);return;}const prevG=s>=3?guided2:s>=2?guided1:base,nextG=s>=3?guided3:s>=2?guided2:guided1,prevF=s>=3?free2:s>=2?free1:base,nextF=s>=3?free3:s>=2?free2:free1;
 graph(root.querySelector('[data-sg-guided]'),prevG,prevG.map((v,i)=>v+t*(nextG[i]-v)),true);graph(root.querySelector('[data-sg-unguided]'),prevF,prevF.map((v,i)=>v+t*(nextF[i]-v)),false);root.dataset.stage=String(s);root.dataset.progress=t.toFixed(3);}
 function update(animate){const s=stage();if(s===last)return;last=s;cancelAnimationFrame(animation);if(!animate||s===0||matchMedia('(prefers-reduced-motion: reduce)').matches){draw(s,s===0?0:1);return;}const start=performance.now();function frame(now){const t=Math.min(1,(now-start)/1800);draw(s,t);if(t<1)animation=requestAnimationFrame(frame);}animation=requestAnimationFrame(frame);}
 function bind(){Reveal.on('fragmentshown',()=>update(true));Reveal.on('fragmenthidden',()=>update(false));Reveal.on('slidechanged',()=>{cancelAnimationFrame(animation);last=-1;update(false);});}
 if(window.Reveal?.isReady())bind();else window.Reveal?.on('ready',bind);update(false);
})();
