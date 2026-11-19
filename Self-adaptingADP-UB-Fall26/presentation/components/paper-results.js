/* Figure 2 from Pakiman et al. (2025), reproduced from the supplied PDF.
   Exact gap labels are data below; no upper/lower-bound samples are invented.
   The plot ink itself is revealed from the original raster reproduction. */
(function () {
  'use strict';
  const gaps = [[1837, 372, 218, 18, 10, 7], [1921, 364, 165, 10, 7, 5]];
  const observations = [
    'The initial approximation has a wide spread of policy costs and a large optimality gap.',
    'The first self-guided update reduces the reported gaps to 372% and 364%.',
    'The policy-cost bounds keep moving together; variation across trials remains substantial.',
    'By iteration 3, the reported gaps fall to 18% and 10%, and variability contracts sharply.',
    'The bounds become closer: reported gaps are 10% and 7%.',
    'At iteration 5, the reported gaps are 7% and 5%; both panels show much less variability.'
  ];
  const panels = [
    {viewBox:'90 30 990 635', x:252, right:1064, top:44, bottom:564, ends:[386,522,658,794,930,1064], strip:270, legend:[665,54,390,126]},
    {viewBox:'1085 30 960 635', x:1214, right:2025, top:44, bottom:564, ends:[1347,1483,1619,1755,1891,2025], strip:1230, legend:[1625,54,393,126]}
  ];
  let serial = 0;
  function svgNode(name, attrs) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', name);
    Object.entries(attrs || {}).forEach(([k,v]) => el.setAttribute(k,String(v)));
    return el;
  }
  function initSGFigure(root) {
    if (!root || root.dataset.sgReady === 'true') return;
    root.dataset.sgReady = 'true';
    const prefix = 'sg-fig2-' + (++serial);
    const asset = root.dataset.figureSource || 'assets/figures/self-guided-figure2.png';
    const reveals = [];
    root.querySelectorAll('.sg-plot').forEach((svg, i) => {
      const p = panels[i];
      svg.setAttribute('viewBox',p.viewBox);
      const defs = svgNode('defs');
      const source = svgNode('image',{id:prefix+'-source-'+i,href:asset,x:0,y:0,width:2100,height:690});
      defs.append(source);
      const clip = svgNode('clipPath',{id:prefix+'-clip-'+i});
      const reveal = svgNode('rect',{x:p.x,y:p.top,width:p.ends[0]-p.x,height:p.bottom-p.top,class:'sg-reveal'});
      clip.append(reveal);defs.append(clip);
      const legendClip = svgNode('clipPath',{id:prefix+'-legend-'+i});
      legendClip.append(svgNode('rect',{x:p.legend[0],y:p.legend[1],width:p.legend[2],height:p.legend[3]}));
      defs.append(legendClip);svg.append(defs);
      svg.append(svgNode('use',{href:'#'+source.id}));
      // Blank only the plotting area. Axes, cost labels, and q ticks stay visible.
      const grid = svgNode('svg',{x:p.x,y:p.top,width:p.right-p.x,height:p.bottom-p.top,viewBox:p.strip+' '+p.top+' 1 '+(p.bottom-p.top),preserveAspectRatio:'none',overflow:'hidden'});
      grid.append(svgNode('use',{href:'#'+source.id}));
      svg.append(grid);
      svg.append(svgNode('use',{href:'#'+source.id,'clip-path':'url(#'+clip.id+')'}));
      // Preserve the original legend independently of the revealed iteration.
      svg.append(svgNode('use',{href:'#'+source.id,'clip-path':'url(#'+legendClip.id+')'}));
      // Clip to the panel's viewBox as well as its viewport: meet scaling leaves
      // letterbox space where the neighboring panel would otherwise show.
      const bounds = p.viewBox.split(' ').map(Number);
      const panelClip = svgNode('clipPath',{id:prefix+'-panel-'+i,clipPathUnits:'userSpaceOnUse'});
      panelClip.append(svgNode('rect',{x:bounds[0],y:bounds[1],width:bounds[2],height:bounds[3]}));
      defs.append(panelClip);
      const cropped = svgNode('g',{'clip-path':'url(#'+panelClip.id+')'});
      [...svg.children].filter(child => child !== defs).forEach(child => cropped.append(child));
      svg.append(cropped);
      reveals.push(reveal);
    });
    let q = 0;
    const next = root.querySelector('[data-sg-next]');
    const previous = root.querySelector('[data-sg-prev]');
    const reset = root.querySelector('[data-sg-reset]');
    const steps = Array.from(root.querySelectorAll('[data-sg-step]'));
    function setIteration(n) {
      q = Math.max(0,Math.min(5,Math.trunc(Number(n)) || 0));
      root.dataset.iteration = String(q);
      reveals.forEach((rect,i) => rect.setAttribute('width',panels[i].ends[q]-panels[i].x));
      root.querySelector('[data-sg-iteration]').textContent = 'Iteration q = '+q;
      root.querySelectorAll('[data-sg-gap]').forEach((el,i) => el.textContent = gaps[i][q].toLocaleString('en-US')+'%');
      const observation = root.querySelector('[data-sg-observation]');
      if (observation) observation.textContent = observations[q];
      steps.forEach(btn => {
        const selected = Number(btn.dataset.sgStep) === q;
        if (selected) btn.setAttribute('aria-current','step'); else btn.removeAttribute('aria-current');
      });
      next.disabled = q === 5;
      previous.disabled = q === 0;
      reset.disabled = q === 0;
      root.dispatchEvent(new CustomEvent('sgfigurechange',{bubbles:true,detail:{iteration:q,gaps:[gaps[0][q],gaps[1][q]]}}));
    }
    next.addEventListener('click',() => setIteration(q+1));
    previous.addEventListener('click',() => setIteration(q-1));
    reset.addEventListener('click',() => setIteration(0));
    steps.forEach(btn => btn.addEventListener('click',() => setIteration(btn.dataset.sgStep)));
    root.addEventListener('keydown',e => {
      if (e.target.tagName !== 'BUTTON') return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault(); e.stopPropagation();
        setIteration(q+(e.key === 'ArrowRight'?1:-1));
      }
    });
    root.sgFigure = {setIteration,getIteration:() => q};
    setIteration(0);
  }
  window.initSGFigure = initSGFigure;
  function initAll() { document.querySelectorAll('.sg-figure').forEach(initSGFigure); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',initAll);
  else initAll();
})();


/* Exact printed tables are embedded so the deck works without fetch or Python. */
(() => {
  'use strict';
  const paperData = {"citation":{"title":"Self-Guided Approximate Linear Programs: Randomized Multi-Shot Approximation of Discounted Cost Markov Decision Processes","authors":["Parshan Pakiman","Selvaprabu Nadarajah","Negar Soheili","Qihang Lin"],"journal":"Management Science","year":2025,"volume":71,"issue":4,"pages":"3384–3404","doi":"10.1287/mnsc.2020.00038","published_online":"2024-07-23"},"figure2":{"pdf_page":18,"journal_page":3400,"q":[0,1,2,3,4,5],"panels":[{"params":[1,8,2,5],"gaps":[1837,372,218,18,10,7]},{"params":[1,8,2,2],"gaps":[1921,364,165,10,7,5]}],"note":"Upper and lower bound distributions over ten trials. Gap percentages transcribed exactly from printed figure; raw samples unavailable. Do not infer basis-count mapping from displayed q ticks."},"table4":{"pdf_page":17,"journal_page":3399,"gamma":0.95,"c_l":1000,"columns":["c_h","c_d","c_b","sigma","ALP_LNS_policy","FALP600_policy","FALP1000_policy","SG6007_policy","ALP_LNS_LB","FALP600_LB","FALP1000_LB","SG6007_LB"],"rows":[[1,8,2,5,45.6,13.0,33.0,7.4,26.7,0.9,1.3,0],[1,8,2,2,43.6,6.1,14.6,4.8,19.2,2.2,1.4,0],[1,2,8,5,110.0,11.4,31.9,7.1,24.1,1.5,1.1,0],[1,2,8,2,48.3,7.0,10.6,5.1,17.9,1.5,1.4,0],[2,8,5,5,43.4,14.5,38.4,8.1,31.3,1.5,1.1,0],[2,8,5,2,8.9,9.1,13.9,6.5,25.1,2.6,2.1,0]],"average_policy":[50.0,10.2,23.7,6.5],"average_LB":[24.1,1.7,1.4,0],"policy_gap_definition":"100*(UB-bestLB)/bestLB","LB_gap_definition":"100*(bestLB-LB)/bestLB","runtime_minutes":[5,33,106,74]},"table5":{"pdf_page":20,"journal_page":3402,"columns":["J","p_init","LSM_policy","ALP_DFM_policy","FALP500_policy","SG5006_policy","LSM_UB","ALP_DFM_UB","FALP500_UB","SG5006_UB"],"rows":[[4,90,6.6,4.8,0.9,0.8,0,13.3,1.5,1.3],[4,100,6.4,6.4,1.9,1.9,0.7,7.5,0,0],[4,110,6.6,8.0,8.4,5.3,0,2.6,992.0,3.6],[8,90,6.2,6.1,4.1,4.0,0,4.1,5.8,5.4],[8,100,5.5,7.0,7.8,4.2,0,0.7,6.0,0.6],[8,110,3.9,6.4,9.5,3.1,0.6,0.1,172.5,0],[16,90,4.9,6.3,3.3,3.3,0,0,0.5,0.4],[16,100,3.4,5.5,2.4,2.3,0.6,0,0.3,0],[16,110,2.8,5.2,2.4,2.1,0.6,1054.4,0.2,4.0]],"average_policy":[5.2,6.2,4.5,3.0],"reported_average_UB":[0.3,9.1,130.8,1.6],"policy_gap_definition":"100*(bestUB-LB)/bestUB","UB_gap_definition":"100*(UB-bestUB)/bestUB","runtime_minutes":[2.4,5.1,99.5,117.9],"caution":"Printed ALP_DFM upper-bound-gap average 9.1 does not equal arithmetic mean of printed rows due to final 1054.4 entry; preserve reported value with note or omit this average. Reward-maximization case reverses policy-bound direction relative to inventory."}};
  const labels = {
    inventory: ['ALP<sup>LNS</sup>', 'FALP<sub>600</sub>', 'FALP<sub>1000</sub>', 'Self-guided<br>FALP<sub>600,7</sub>'],
    options: ['LSM', 'ALP<sup>DFM</sup>', 'FALP<sub>500</sub>', 'Self-guided<br>FALP<sub>500,6</sub>']
  };
  function cell(tag, text, attrs) {
    const el = document.createElement(tag);
    if (text !== null) el.textContent = text;
    Object.entries(attrs || {}).forEach(([name,value]) => el.setAttribute(name,String(value)));
    return el;
  }
  function initTable(root) {
    if (root.dataset.paperReady === 'true') return;
    const kind = root.dataset.paperTable;
    if (!(kind in labels)) return;
    const data = kind === 'inventory' ? paperData.table4 : paperData.table5;
    const output = root.querySelector('.paper-table-output');
    const formula = root.querySelector('.paper-table-formula');
    if (!output) return;
    root.dataset.paperReady = 'true';
    output.setAttribute('aria-live','polite');
    output.setAttribute('aria-atomic','true');
    const buttons = Array.from(root.querySelectorAll('[data-paper-metric]'));
    let metric = 'policy';
    const progressive = root.hasAttribute('data-paper-reveal-columns');
    const hideCaption = root.hasAttribute('data-paper-hide-caption');
    function updateColumns() {
      if (!progressive) return;
      const reading = !root.closest('.reveal');
      const count = reading ? 4 : Math.max(0, ...Array.from(root.querySelectorAll('[data-paper-column-step].visible'),
        step => Number(step.dataset.paperColumnStep) + 1));
      root.dataset.paperRevealedColumns = String(count);
      root.querySelectorAll('[data-paper-column]').forEach(column => {
        const visible = Number(column.dataset.paperColumn) < count;
        column.classList.toggle('paper-column-hidden', !visible);
        column.setAttribute('aria-hidden', String(!visible));
      });
    }
    function bindColumns() {
      if (!progressive || !window.Reveal) return;
      for (const name of ['fragmentshown','fragmenthidden']) Reveal.on(name, event => {
        if (!root.contains(event.fragment)) return;
        if (event.fragment.hasAttribute('data-paper-bound-step')) {
          draw(name === 'fragmentshown' ? 'bound' : 'policy');
        } else updateColumns();
      });
      Reveal.on('slidechanged', updateColumns);
      if (root.querySelector('[data-paper-bound-step].visible')) draw('bound');
      else updateColumns();
    }
    function draw(nextMetric) {
      metric = nextMetric === 'bound' ? 'bound' : 'policy';
      root.dataset.paperCurrentMetric = metric;
      buttons.forEach(button => button.setAttribute('aria-pressed',String(button.dataset.paperMetric === metric)));
      const table = cell('table',null,{class:'method-table paper-result-table'});
      const captionText = (kind === 'inventory' ? 'Table 4: ten-dimensional inventory control' : 'Table 5: Bermudan options pricing') + ' — ' +
        (metric === 'policy' ? 'policy optimality gaps (%)' : (kind === 'inventory' ? 'lower-bound gaps (%)' : 'upper-bound gaps (%)'));
      if (!hideCaption) table.append(cell('caption',captionText));
      else table.setAttribute('aria-label', captionText);
      const thead = cell('thead');
      const headingRow = cell('tr');
      const instanceHeading = cell('th',null,{scope:'col'});
      instanceHeading.innerHTML = kind === 'inventory' ? '(c<sub>h</sub>, c<sub>d</sub>, c<sub>b</sub>, σ)' : '(J, initial price)';
      headingRow.append(instanceHeading);
      labels[kind].forEach((label,i) => {
        const heading = cell('th',null,{scope:'col',class:i===3?'paper-guided':''});
        heading.innerHTML = label;
        headingRow.append(heading);
      });
      thead.append(headingRow);table.append(thead);
      const tbody = cell('tbody');
      const offset = kind === 'inventory' ? (metric === 'policy' ? 4 : 8) : (metric === 'policy' ? 2 : 6);
      data.rows.forEach(rowData => {
        const row = cell('tr');
        const instance = kind === 'inventory' ? '('+rowData.slice(0,4).join(', ')+')' : '('+rowData.slice(0,2).join(', ')+')';
        row.append(cell('th',instance,{scope:'row'}));
        const values = rowData.slice(offset,offset+4);
        const best = Math.min(...values);
        values.forEach((value,i) => {
          const classes = [i===3?'paper-guided':'',value===best?'paper-best':''].filter(Boolean).join(' ');
          row.append(cell('td',value.toFixed(1),{class:classes}));
        });
        tbody.append(row);
      });
      table.append(tbody);
      const tfoot = cell('tfoot');
      // The printed Table 5 bound averages are inconsistent with its printed rows.
      // Preserve the instance rows but deliberately omit all averages in that view.
      const averages = metric === 'policy' ? data.average_policy : (kind === 'inventory' ? data.average_LB : null);
      if (averages) {
        const row = cell('tr',null,{class:'paper-average'});
        row.append(cell('th','Reported average',{scope:'row'}));
        averages.forEach((value,i) => row.append(cell('td',value.toFixed(1),{class:i===3?'paper-guided':''})));
        tfoot.append(row);
      }
      const runtime = cell('tr',null,{class:'paper-runtime'});
      runtime.append(cell('th','Runtime (minutes)',{scope:'row'}));
      data.runtime_minutes.forEach((value,i) => runtime.append(cell('td',kind==='inventory'?String(value):value.toFixed(1),{class:i===3?'paper-guided':''})));
      tfoot.append(runtime);table.append(tfoot);
      if (progressive) table.querySelectorAll('tr').forEach(row => {
        Array.from(row.children).slice(1).forEach((column,i) => column.dataset.paperColumn = String(i));
      });
      output.replaceChildren(table);
      updateColumns();
      const formulaText = kind === 'inventory'
        ? (metric === 'policy' ? 'Policy gap = 100 × (policy cost − best lower bound) / best lower bound.' : 'Lower-bound gap = 100 × (best lower bound − method lower bound) / best lower bound.')
        : (metric === 'policy' ? 'Policy gap = 100 × (best upper bound − policy value) / best upper bound.' : 'Upper-bound gap = 100 × (method upper bound − best upper bound) / best upper bound.');
      if (formula) {
        formula.textContent = formulaText + ' Smaller gaps are better.';
        if (kind === 'options' && metric === 'bound') {
          formula.textContent += ' Averages omitted because the printed table contains an inconsistency.';
        }
      }
      root.dispatchEvent(new CustomEvent('papertablechange',{bubbles:true,detail:{kind,metric}}));
    }
    buttons.forEach(button => button.addEventListener('click',() => draw(button.dataset.paperMetric)));
    root.paperTable = {setMetric:draw,getMetric:() => metric};
    draw('policy');
    if (window.Reveal?.isReady()) bindColumns();
    else window.Reveal?.on('ready', bindColumns);
  }
  function bindFigureNavigation() {
    const deck = window.Reveal;
    if (!deck || window.PAPER_RESULTS_NAVIGATION_READY || !document.querySelector('.sg-figure')) return;
    function intercept() {
      const slide = deck.getCurrentSlide();
      if (slide?.id !== 'sg-paper-figure2' || deck.isOverview() || deck.isPaused()) return false;
      const figure = slide.querySelector('.sg-figure');
      if (!figure?.sgFigure || figure.sgFigure.getIteration() >= 5) return false;
      figure.sgFigure.setIteration(figure.sgFigure.getIteration()+1);
      return true;
    }
    for (const name of ['next','right','down','navigateNext','navigateRight','navigateDown']) {
      const original = deck[name];
      if (typeof original === 'function') deck[name] = function (...args) {
        if (!intercept()) return original.apply(deck,args);
      };
    }
    document.addEventListener('click',event => {
      if (event.target.closest('.reveal .controls :is(.navigate-right,.navigate-down,.navigate-next)') && intercept()) {
        event.preventDefault();event.stopImmediatePropagation();
      }
    },true);
    document.addEventListener('keydown',event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || deck.isOverview() || deck.isPaused()) return;
      if (event.target.closest('input,textarea,select,[contenteditable="true"],.slide-menu-wrapper')) return;
      if (event.key === ' ' && event.target.closest('button,a')) return;
      if (['ArrowRight','ArrowDown','PageDown',' ','n','N','l','L','j','J'].includes(event.key) && intercept()) {
        event.preventDefault();event.stopImmediatePropagation();
      }
    },true);
    window.PAPER_RESULTS_NAVIGATION_READY = true;
  }
  function start() {
    document.querySelectorAll('[data-paper-table]').forEach(initTable);
    if (window.Reveal?.isReady()) bindFigureNavigation();
    else if (window.Reveal?.on) window.Reveal.on('ready',bindFigureNavigation);
    else window.addEventListener('load',bindFigureNavigation,{once:true});
    window.PAPER_RESULTS_READY = true;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',start,{once:true});
  else start();
})();
