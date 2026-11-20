(() => {
  const root = document.querySelector('.reveal #discounted-mdp .discounted-mdp-bridge');
  if (!root) return;
  const arrow = root.querySelector('.bridge-constraint-arrow');
  const path = arrow.querySelector('.bridge-constraint-path');
  const label = arrow.querySelector('.bridge-constraint-label');
  function draw() {
    const bounds = root.getBoundingClientRect();
    if (!bounds.width) return;
    const scale = root.offsetWidth / bounds.width;
    const equation = root.querySelector('.bridge-bellman .polished-math').getBoundingClientRect();
    const target = root.querySelector('.bridge-constraint-stage [data-c="2264"]').getBoundingClientRect();
    const equals = root.querySelector('.bridge-bellman [data-c="3D"]').getBoundingClientRect();
    const title = document.createRange();
    title.selectNodeContents(root.querySelector('.bridge-lp > h3'));
    const titleRight = (title.getBoundingClientRect().right - bounds.left) * scale;
    const targetX = (target.left + target.width / 2 - bounds.left) * scale;
    const targetY = (target.top - bounds.top) * scale - 5;
    const startY = (equation.bottom - bounds.top) * scale + 5;
    const sourceX = (equals.left + equals.width / 2 - bounds.left) * scale;
    const sourceY = (equals.bottom - bounds.top) * scale + 2;
    const routeX = Math.max(titleRight + 24, targetX + 55);
    arrow.setAttribute('viewBox', [0, 0, root.offsetWidth, root.offsetHeight].join(' '));
    path.setAttribute('d', 'M' + sourceX + ' ' + sourceY +
      ' C' + sourceX + ' ' + (sourceY + 18) + ' ' + routeX + ' ' + (startY - 18) + ' ' + routeX + ' ' + startY +
      ' V' + (targetY - 28) +
      ' Q' + routeX + ' ' + (targetY - 14) + ' ' + (routeX - 14) + ' ' + (targetY - 14) +
      ' H' + (targetX + 14) + ' Q' + targetX + ' ' + (targetY - 14) + ' ' + targetX + ' ' + targetY);
    label.setAttribute('x', routeX + 18);
    label.setAttribute('y', (startY + targetY) / 2 + 7);
    const quantifier = root.querySelector('.bridge-constraint-stage [data-c="2200"]').getBoundingClientRect();
    const row = root.querySelector('.bridge-constraint-stage [data-c="2200"]').closest('[data-mml-node="mtr"]').getBoundingClientRect();
    const underlineX = (quantifier.left - bounds.left) * scale - 2;
    const underlineEnd = (row.right - bounds.left) * scale;
    const underlineY = (row.bottom - bounds.top) * scale + 5;
    root.querySelector('.bridge-universal-underline').setAttribute('d',
      'M' + underlineX + ' ' + underlineY + ' H' + underlineEnd);
    const variable = root.querySelector('.bridge-constraint-stage [data-mml-node="munder"] [data-c="1D449"]').getBoundingClientRect();
    const variableX = (variable.left - bounds.left) * scale - 1.5;
    const variableEnd = (variable.right - bounds.left) * scale + 1.5;
    const variableY = (variable.bottom - bounds.top) * scale + 4;
    root.querySelector('.bridge-variable-underline').setAttribute('d',
      'M' + variableX + ' ' + variableY + ' H' + variableEnd);


  }
  const schedule = () => requestAnimationFrame(draw);
  new ResizeObserver(schedule).observe(root);
  function bind() {
    ['slidechanged', 'fragmentshown', 'fragmenthidden', 'resize'].forEach(event => Reveal.on(event, schedule));
    schedule();
  }
  if (window.Reveal?.isReady()) bind();
  else window.Reveal?.on('ready', bind);
})();
