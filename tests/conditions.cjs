// Test the emitted SugarCube expressions, not a separate imitation of the rules.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { events, core, daily, max } = JSON.parse(fs.readFileSync(0, 'utf8'));

function expression(tag) {
  return tag.replace(/^<<(?:if|elseif|=)\s+/, '').replace(/>>$/, '')
    .replace(/\s+\?[^]*$/, '')
    .replace(/\$([A-Za-z_]\w*)/g, 'v.$1')
    .replace(/\b_sydneyVirgin\b/g, 'sydneyVirgin')
    .replace(/\b_args\b/g, 'args')
    .replace(/\b(?:isnot|is|and|or|not|gte)\b/g,
      token => ({ isnot: '!==', is: '===', and: '&&', or: '||', not: '!', gte: '>=' }[token]));
}

function context(active, virgin, npcVow, available, enoughFame) {
  return {
    window: { AngelTempleVowProtection: { enabled: () => active } },
    v: { player: { virginity: { penile: virgin, vaginal: virgin, temple: false },
      penisExist: true, vaginaExist: true, temple_virginity: false },
      angel: 0, templePromised: '', brothelVirginityIntro: undefined,
      brothelVirginityState: 'ok', rng: 2, avery_fate: false, averySeen: [] },
    C: { npc: { Sydney: { virginity: { temple: npcVow } } } },
    sydneyVirgin: virgin, unableTakeVirginity: () => !available,
    fameSum: () => enoughFame ? 100 : 99, playerChastity: () => true,
    playerBellyVisible: () => false, args: ['X', 'vaginal'],
  };
}

let comparisons = 0;
for (const [name, old, patched] of events) {
  for (const virgin of [false, true]) for (const npc of [false, true])
    for (const available of [false, true]) for (const enoughFame of [false, true]) {
      const c = context(false, virgin, npc, available, enoughFame);
      assert.equal(vm.runInNewContext(expression(patched), c), vm.runInNewContext(expression(old), c), name);
      comparisons++;
    }
}

function evaluate(name, active, mutate = () => {}) {
  const rule = events.find(row => row[0] === name);
  const c = context(active, false, true, false, true);
  mutate(c);
  return vm.runInNewContext(expression(rule[2]), c);
}
assert.equal(evaluate('Temple Test', true), true);
assert.equal(evaluate('Sydney Temple Test 2', true), true);
assert.equal(evaluate('Sydney Temple Test 2', true, c => { c.C.npc.Sydney.virginity.temple = false; }), false);
assert.equal(evaluate("Briar's Office Show", true), true);
assert.equal(evaluate("Briar's Office Show", true, c => { c.fameSum = () => 99; }), false);
assert.equal(evaluate('Widgets Brothel', true, c => { c.v.brothelVirginityIntro = true; }), true);
assert.equal(evaluate('Widgets Brothel', true, c => { c.v.brothelVirginityIntro = true; c.v.brothelVirginityState = 'lie'; }), false);
assert.equal(evaluate('Underground Intro', true), true);
const bodyRule = events.find(row => row[0] === 'Underground Intro' && row[1].includes('vaginaExist'));
const noBody = context(true, false, true, false, true);
noBody.v.player.penisExist = noBody.v.player.vaginaExist = false;
assert.equal(vm.runInNewContext(expression(bodyRule[2]), noBody), false);
assert.equal(evaluate('Mansion Talk Chat 2', true), false);
assert.equal(evaluate('Mansion Talk Chat 2', true, c => { c.v.player.virginity.temple = true; }), true);

const vow = core.find(row => row[0] === 'Widgets Combat' && row[1].startsWith('<<if'));
const purity = core.find(row => row[0] === 'Widgets Combat' && row[1].startsWith('<<case'));
for (const active of [false, true]) {
  const c = context(active, false, true, true, true);
  c.v.player.virginity.temple = true;
  assert.equal(vm.runInNewContext(expression(vow[2] + '>>'), c), !active);
  const purityCondition = purity[2].slice(purity[2].indexOf('<<if')) + '>>';
  c.$_taker = 'X';
  // The shared expression parser maps $_taker to v._taker.
  c.v._taker = 'X';
  assert.equal(vm.runInNewContext(expression(purityCondition), c), !active);
  for (const virgin of [false, true]) {
    const V = { player: { virginity: { vaginal: virgin, penile: virgin } }, virginityProtected: false };
    const sandbox = { V, window: c.window };
    assert.equal(vm.runInNewContext(`let dailyPurity = 0; ${daily} dailyPurity;`, sandbox), active || virgin ? 2 : 0);
    assert.equal(vm.runInNewContext(`${max} max;`, sandbox), active || virgin ? 1000 : 999);
  }
}
console.log(`${comparisons} inactive-equivalence cases plus active eligibility and purity assertions passed`);
