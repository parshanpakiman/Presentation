/* Exercise the persistent choice controller without a browser. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.join(__dirname, '../assets/demos');
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(root, 'audience-choice-data.js'), 'utf8'), context);
const data = context.window.AUDIENCE_CHOICE_DATA;
const Session = require(path.join(root, 'audience-choice-state.js'));
for (let initial = 0; initial <= 4; initial++) {
  const session = new Session(data);
  session.start(initial);
  const start = session.key();
  const before = session.current().objective;
  while (session.best()?.score > 1e-7) {
    const { period, action } = session.best();
    session.add(period, action);
    assert.ok(session.current().objective >= before - 1e-7);
    assert.ok(session.history.length <= 8);
  }
  assert.equal(session.current().objective, 49);
  const restored = new Session(data, JSON.parse(JSON.stringify(session.serialize())));
  assert.equal(restored.key(), session.key());
  assert.equal(restored.current().policy, session.current().policy);
  assert.equal(restored.history.length, session.history.length);
  assert.equal(session.initial, initial);
  if (initial !== 2) assert.notEqual(session.key(), start);
  session.reset();
  assert.equal(session.stage, 'choose');
  assert.equal(session.key(), '0-0');
}
const invalid = new Session(data, { version: 1, started: true, initial: 9 });
assert.equal(invalid.stage, 'choose');
const duplicate = new Session(data);
duplicate.start(1);
assert.throws(() => duplicate.add(0, 1), /omitted/);
// The revised lesson: recover the full LP objective with fewer assortments,
// then demonstrate that another feasible option need not increase the objective.
const guided = new Session(data);
guided.start(0);
assert.deepEqual([guided.ids(0).length, guided.ids(1).length], [1, 1]);
guided.add(0, 2);
assert.equal(guided.current().objective, 22);
assert.deepEqual([guided.ids(0).length, guided.ids(1).length], [2, 1]);
guided.add(1, 2);
assert.equal(guided.current().objective, data.states['15-15'].objective);
assert.deepEqual([guided.ids(0).length, guided.ids(1).length], [2, 2]);
guided.add(1, 3);
assert.equal(guided.current().objective, 49);
assert.deepEqual([guided.ids(0).length, guided.ids(1).length], [2, 3]);
console.log('Validated all five starts, guided refinement, persistence, reset, and invalid choices.');
