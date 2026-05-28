// test_utils.js — Node.js tests for utils.js
// Run with: node test_utils.js

'use strict';

const {
    empty, Wpawn, Wbishop, Wknight, Wrook, Wqueen, Wking, pieceDivider,
    Bpawn, Bbishop, Bknight, Brook, Bqueen, Bking,
    onGoing, drawRep, staleMate, blackWin, whiteWin,
    Move, LimitedSizeDict,
} = require('./utils.js');

let passed = 0, failed = 0;

function assert(condition, label) {
    if (condition) {
        console.log(`  PASS  ${label}`);
        passed++;
    } else {
        console.error(`  FAIL  ${label}`);
        failed++;
    }
}

// ── Piece constants ───────────────────────────────────────────────────────────
console.log('\n=== Piece constants ===');
assert(empty === 0,        'empty == 0');
assert(Wpawn === 1,        'Wpawn == 1');
assert(Wbishop === 2,      'Wbishop == 2');
assert(Wknight === 3,      'Wknight == 3');
assert(Wrook === 4,        'Wrook == 4');
assert(Wqueen === 5,       'Wqueen == 5');
assert(Wking === 6,        'Wking == 6');
assert(pieceDivider === 7, 'pieceDivider == 7');
assert(Bpawn === 8,        'Bpawn == 8');
assert(Bbishop === 9,      'Bbishop == 9');
assert(Bknight === 10,     'Bknight == 10');
assert(Brook === 11,       'Brook == 11');
assert(Bqueen === 12,      'Bqueen == 12');
assert(Bking === 13,       'Bking == 13');

// White pieces are < pieceDivider, black pieces are > pieceDivider
for (const p of [Wpawn, Wbishop, Wknight, Wrook, Wqueen, Wking])
    assert(p < pieceDivider, `white piece ${p} < pieceDivider`);
for (const p of [Bpawn, Bbishop, Bknight, Brook, Bqueen, Bking])
    assert(p > pieceDivider, `black piece ${p} > pieceDivider`);

// ── Game states ───────────────────────────────────────────────────────────────
console.log('\n=== Game states ===');
assert(onGoing === 0,   'onGoing == 0');
assert(drawRep === 1,   'drawRep == 1');
assert(staleMate === 2, 'staleMate == 2');
assert(blackWin === 3,  'blackWin == 3');
assert(whiteWin === 4,  'whiteWin == 4');

// ── Move encoding ─────────────────────────────────────────────────────────────
console.log('\n=== Move encoding ===');

// Basic round-trip for every combination of coordinates
let allOk = true;
for (let x1 = 0; x1 < 8; x1++)
for (let y1 = 0; y1 < 8; y1++)
for (let x2 = 0; x2 < 8; x2++)
for (let y2 = 0; y2 < 8; y2++) {
    const m = new Move(x1, y1, x2, y2);
    if (m.getX1() !== x1 || m.getY1() !== y1 ||
        m.getX2() !== x2 || m.getY2() !== y2 ||
        m.getAttacking() !== 0) {
        allOk = false;
        console.error(`  FAIL  round-trip (${x1},${y1})->(${x2},${y2}): got (${m.getX1()},${m.getY1()})->(${m.getX2()},${m.getY2()}) att=${m.getAttacking()}`);
    }
}
assert(allOk, 'Move round-trip for all 4096 coordinate pairs');

// isAttacking flag
const m1 = new Move(0, 0, 7, 7, 1);
assert(m1.getAttacking() === 1, 'constructor isAttacking=1');
const m2 = new Move(1, 2, 3, 4);
assert(m2.getAttacking() === 0, 'constructor isAttacking defaults to 0');
m2.setAttacking();
assert(m2.getAttacking() === 1, 'setAttacking() flips flag to 1');

// equals()
const ma = new Move(2, 3, 5, 6);
const mb = new Move(2, 3, 5, 6);
const mc = new Move(2, 3, 5, 7);
assert(ma.equals(mb), 'same-coord moves are equal');
assert(!ma.equals(mc), 'different-coord moves are not equal');
assert(!ma.equals(null), 'move.equals(null) is false');
assert(!ma.equals(42),   'move.equals(42) is false');

// A move with setAttacking differs from one without
const md = new Move(1, 1, 2, 2);
const me = new Move(1, 1, 2, 2);
me.setAttacking();
assert(!md.equals(me), 'quiet vs attacking move not equal');

// key() is unique for different moves
const keySet = new Set();
for (let x1 = 0; x1 < 8; x1++)
for (let y1 = 0; y1 < 8; y1++)
for (let x2 = 0; x2 < 8; x2++)
for (let y2 = 0; y2 < 8; y2++) {
    keySet.add(new Move(x1, y1, x2, y2).key());
    keySet.add(new Move(x1, y1, x2, y2, 1).key());
}
assert(keySet.size === 4096 * 2, `key() produces ${keySet.size} distinct values for 8192 moves`);

// ── LimitedSizeDict ───────────────────────────────────────────────────────────
console.log('\n=== LimitedSizeDict ===');

const d = new LimitedSizeDict(3);
d.set('a', 1); d.set('b', 2); d.set('c', 3);
assert(d.size === 3, 'size == 3 after 3 inserts');
assert(d.has('a') && d.has('b') && d.has('c'), 'has() returns true for all keys');
assert(d.get('b') === 2, 'get() returns correct value');

// Insert 4th entry: oldest ('a') should be evicted
d.set('d', 4);
assert(d.size === 3, 'size stays at max after eviction');
assert(!d.has('a'), "'a' evicted (FIFO)");
assert(d.has('b') && d.has('c') && d.has('d'), 'b, c, d present after eviction');

// Overwrite existing key — no eviction, no size growth
d.set('b', 99);
assert(d.size === 3, 'size unchanged on overwrite');
assert(d.get('b') === 99, 'overwrite updates value');
assert(d.has('c') && d.has('d'), 'c, d still present after overwrite');

d.clear();
assert(d.size === 0, 'clear() empties the dict');

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
