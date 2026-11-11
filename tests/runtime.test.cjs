const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../src/runtime.js'), 'utf8');

function boot(variables, withState = true) {
  const events = new Map();
  const context = { window: {}, document: {}, $: () => ({ on(names, handler) {
    for (const name of names.split(' ')) events.set(name, handler);
  } }) };
  if (withState) context.State = { variables };
  vm.runInNewContext(source, context);
  return { context, events, api: context.window.AngelTempleVowProtection };
}

test('anatomical history, old counts and unrelated values are never rewritten', () => {
  const variables = {
    temple_rank: 'priest', angelTempleVowProtection: true,
    player: { virginity: { vaginal: 'Someone', penile: false, oral: 'Other', temple: 'Someone' } },
    brokenVowCount: { Someone: 3 }, angel: 6, angelbuild: 20, purity: 500,
  };
  const { api } = boot(variables);
  assert.equal(api.enabled(), true);
  assert.deepEqual(variables.player.virginity, { vaginal: 'Someone', penile: false, oral: 'Other', temple: true });
  assert.equal(Object.hasOwn(variables, 'angelTempleVowProtection'), false);
  assert.deepEqual(variables.brokenVowCount, { Someone: 3 });
  assert.equal(variables.angel, 6);
  assert.equal(variables.angelbuild, 20);
  assert.equal(variables.purity, 500);
});

test('only the four supported ranks receive vow restoration', () => {
  for (const rank of ['prospective', 'initiate', 'monk', 'priest', 'none', '', undefined]) {
    const variables = { temple_rank: rank, player: { virginity: { temple: 'X' } } };
    boot(variables);
    assert.equal(variables.player.virginity.temple,
      ['prospective', 'initiate', 'monk', 'priest'].includes(rank) ? true : 'X');
  }
});

test('safe before State/player initialization and on load into a new variables object', () => {
  const { context, api, events } = boot(undefined, false);
  api.maintainVow();
  context.State = { variables: { angelTempleVowProtection: true } };
  api.maintainVow();
  assert.deepEqual(context.State.variables, {});
  context.State.variables = { temple_rank: 'initiate', player: { virginity: { temple: false } } };
  events.get(':passagestart.angelTempleVowProtection')();
  assert.equal(context.State.variables.player.virginity.temple, true);
  assert.ok(events.has(':storyready.angelTempleVowProtection'));
});

test('diagnostic disable stops restoration and is not persisted in saves', () => {
  const variables = { temple_rank: 'monk', player: { virginity: { temple: true } } };
  const { api } = boot(variables);
  api.setEnabled(false);
  variables.player.virginity.temple = 'X';
  api.maintainVow();
  assert.equal(api.enabled(), false);
  assert.equal(variables.player.virginity.temple, 'X');
  assert.equal(JSON.stringify(variables).includes('angelTempleVowProtection'), false);
  assert.equal(boot(variables).api.enabled(), true);
});
