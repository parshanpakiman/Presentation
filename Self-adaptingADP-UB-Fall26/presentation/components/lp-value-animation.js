/* Constant downward shifts of an optimal value function are Bellman feasible. */
(() => {
  const root = document.querySelector('#s25');
  const stage = root?.querySelector('.lp-model-stage');
  if (!stage) return;
  const svg = stage.querySelector('.lp-value-chart svg');
  const expectation = stage.querySelector('.lp-value-expectation');
  const states = Array.from({length:161}, (_, i) => -4 + i / 10);
  const optimum = s => 35 + 4 * Math.max(2 - s, 0) +
    1.2 * Math.max(s - 2, 0) + 1.8 * Math.max(s - 8, 0);
  const x = s => 80 + (s + 4) * 60;
  const y = value => 290 - (value - 10) * 250 / 55;
  const points = offset => states.map(s => [x(s), y(optimum(s) - offset)]);
  const path = coordinates => coordinates.map(([px,py], i) =>
    (i ? 'L' : 'M') + px.toFixed(2) + ',' + py.toFixed(2)).join(' ');
  const target = points(0);
  svg.querySelector('[data-value-optimum]').setAttribute('d', path(target));
  [7,14,21].forEach(offset => {
    const guide = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    guide.setAttribute('d', path(points(offset)));
    svg.querySelector('[data-value-guides]').append(guide);
  });
  let frame, view, animationRunning = false;
  function setRunning(running) {
    animationRunning = running;
    stage.dataset.animating = String(running);
    svg.setAttribute('aria-busy', String(running));
  }
  function draw(fraction) {
    const offset = 21 * (1 - fraction);
    const current = points(offset);
    svg.querySelector('[data-value-moving]').setAttribute('d', path(current));
    svg.querySelector('[data-value-shade]').setAttribute('d',
      path(target) + current.slice().reverse().map(([px,py]) =>
        'L' + px.toFixed(2) + ',' + py.toFixed(2)).join(' ') + 'Z');
    const arrow = svg.querySelector('[data-value-push]');
    arrow.setAttribute('d', [-1,5,10].map(s =>
      'M' + x(s) + ',' + (y(optimum(s) - offset) - 5) + 'V' + (y(optimum(s)) + 7)).join(' '));
    arrow.style.opacity = offset > 3 ? '1' : '0';
    stage.dataset.progress = fraction.toFixed(3);
  }
  function animate() {
    cancelAnimationFrame(frame);
    setRunning(false);
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
      draw(1);
      return;
    }
    setRunning(true);
    const start = performance.now();
    function tick(now) {
      const fraction = Math.min(1, (now - start) / 6200);
      draw(fraction * fraction * (3 - 2 * fraction));
      if (fraction < 1) frame = requestAnimationFrame(tick);
      else setRunning(false);
    }
    draw(0);
    frame = requestAnimationFrame(tick);
  }
  function update() {
    const active = root.classList.contains('present');
    const next = stage.dataset.alwaysPlot === 'true' ||
      stage.querySelector('.lp-plot-step.visible') ? 'plot' : 'equation';
    stage.dataset.view = next;
    if (active && next === 'plot' && view !== 'plot') {
      if (expectation.classList.contains('visible')) draw(1);
      else animate();
    }
    if (!active || next !== 'plot') {
      cancelAnimationFrame(frame);
      setRunning(false);
    }
    view = active ? next : null;
  }
  stage.querySelector('.lp-value-replay').addEventListener('click', () => {
    if (expectation.classList.contains('visible')) window.Reveal?.navigateFragment(-1);
    animate();
  });
  setRunning(false);
  draw(1);
  if (!document.querySelector('.reveal')) return;
  function bind() {
    // Reveal's public API and native controls use different method references.
    const pending = () => Reveal.getCurrentSlide() === root && animationRunning;
    for (const name of ['next','right','down','navigateNext','navigateRight','navigateDown','nextFragment']) {
      const original = Reveal[name];
      Reveal[name] = function (...args) {
        if (pending()) return true;
        return original.apply(Reveal, args);
      };
    }
    for (const type of ['click','touchstart']) {
      document.addEventListener(type, event => {
        if (pending() && event.target.closest('.reveal .controls :is(.navigate-right,.navigate-down,.navigate-next)')) {
          event.preventDefault();
          event.stopImmediatePropagation();
        }
      }, {capture:true, passive:false});
    }
    document.addEventListener('keydown', event => {
      if (!pending() || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey ||
          Reveal.isOverview() || Reveal.isPaused()) return;
      if (event.target.closest('input,textarea,select,[contenteditable="true"],.slide-menu-wrapper')) return;
      if (event.key === ' ' && event.target.closest('button,a')) return;
      if (['ArrowRight','ArrowDown','PageDown',' ','n','N','l','L','j','J'].includes(event.key)) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    }, true);
    ['fragmentshown','fragmenthidden','slidechanged'].forEach(event => Reveal.on(event, update));
    update();
  }
  if (window.Reveal?.isReady()) bind();
  else window.Reveal?.on('ready', bind);
})();
