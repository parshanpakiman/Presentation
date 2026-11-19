/* Run the actual UI handlers against a minimal DOM to check the lesson sequence.
 * Browser inspection separately checks the rendered layout. No browser is used here.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const Session = require('../assets/demos/audience-choice-state.js');
const root = path.join(__dirname, '../assets/demos');
const dataContext = {window: {}};
vm.runInNewContext(fs.readFileSync(path.join(root, 'audience-choice-data.js'), 'utf8'), dataContext);
const data = dataContext.window.AUDIENCE_CHOICE_DATA;
class Element {
  constructor() { this.attrs = {}; this.listeners = {}; this.children = []; this.style = {}; this.dataset = {}; this.classList = {toggle() {}}; }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  replaceChildren(...nodes) { this.children = nodes; }
  append(node) { this.children.push(node); }
  click() { assert.ok(!this.disabled, 'Cannot activate a disabled button'); this.listeners.click(); }
}
const ids = new Map([...fs.readFileSync(path.join(root, 'audience-choice.html'), 'utf8').matchAll(/\bid="([^"]+)"/g)].map(match => [match[1], new Element()]));
const periods = [0, 1].map(period => Object.assign(new Element(), {dataset: {period: String(period)}}));
const stages = Object.fromEntries(['choose', 'refine', 'result'].map(stage => [stage, new Element()]));
const storage = new Map();
const document = {
  getElementById(id) { assert.ok(ids.has(id), 'Missing UI element ' + id); return ids.get(id); },
  createElement() { return new Element(); },
  querySelectorAll(selector) { assert.equal(selector, '[data-period]'); return periods; },
  querySelector(selector) { const stage = selector.match(/data-stage-label="([^"]+)"/)[1]; return stages[stage]; }
};
function load() {
  for (const element of ids.values()) element.listeners = {};
  for (const element of periods) element.listeners = {};
  vm.runInNewContext(fs.readFileSync(path.join(root, 'audience-choice.js'), 'utf8'), {
    window: {AUDIENCE_CHOICE_DATA: data, AudienceChoiceSession: Session}, document,
    localStorage: {getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value)}
  });
}
const el = id => ids.get(id);
function choose(label) {
  const candidate = el('addition-options').children.find(button => button.innerHTML.includes('<strong>' + label + '</strong>'));
  assert.ok(candidate, 'Missing candidate ' + label);
  candidate.click();
  assert.ok(el('add').textContent.includes(label));
  el('add').click();
}
load();
assert.equal(el('choose-view').hidden, false);
assert.equal(el('current-objective').textContent, '0');
assert.match(el('support-counts').innerHTML, /1 of 5/);
el('start').click();
choose('Product 2 only');
assert.equal(el('current-objective').textContent, '22');
el('continue').click();
periods[1].click();
choose('Product 2 only');
assert.equal(el('current-objective').textContent, '49');
assert.equal(el('demo-title').textContent, 'Same LP objective, fewer assortments');
assert.equal((el('support-counts').innerHTML.match(/2 of 5/g) || []).length, 2);
assert.match(el('progression-rows').innerHTML, /All feasible assortments/);
el('continue').click();
el('pricing').click();
assert.match(el('pricing-message').textContent, /no improvement/);
choose('Product 3 only');
assert.equal(el('current-objective').textContent, '49');
assert.match(el('result-insight').textContent, /did not improve/);
load();
assert.equal(el('choose-view').hidden, false);
assert.equal(el('resume').hidden, false);
el('resume').click();
assert.equal(el('current-objective').textContent, '49');
assert.match(el('support-counts').innerHTML, /3 of 5/);
console.log('Verified the actual UI handlers: start small, independent periods, 0 → 22 → 49, small collection, no gain, fresh load, and resume.');
