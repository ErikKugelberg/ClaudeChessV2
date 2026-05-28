// utils.js — port of utils.py
// Piece IDs, game state constants, Move class, LimitedSizeDict

'use strict';

// ── Piece IDs ─────────────────────────────────────────────────────────────────
const empty        = 0;
const Wpawn        = 1;
const Wbishop      = 2;
const Wknight      = 3;
const Wrook        = 4;
const Wqueen       = 5;
const Wking        = 6;
const pieceDivider = 7;
const Bpawn        = 8;
const Bbishop      = 9;
const Bknight      = 10;
const Brook        = 11;
const Bqueen       = 12;
const Bking        = 13;

// ── Game states ───────────────────────────────────────────────────────────────
const onGoing  = 0;
const drawRep  = 1;
const staleMate = 2;
const blackWin = 3;
const whiteWin = 4;

// ── Move ──────────────────────────────────────────────────────────────────────
// Packs x1,y1,x2,y2,isAttacking into a single 16-bit integer.
// Bit layout: x1[2:0] | y1[5:3] | x2[8:6] | y2[11:9] | isAttacking[12]
class Move {
    constructor(x1, y1, x2, y2, isAttacking = 0) {
        this.data = 0;
        this.data |= (x1 & 7);
        this.data |= (y1 & 7) << 3;
        this.data |= (x2 & 7) << 6;
        this.data |= (y2 & 7) << 9;
        this.data |= (isAttacking ? 1 : 0) << 12;
    }

    getX1() { return  this.data & 0b111; }
    getY1() { return (this.data >>> 3) & 0b111; }
    getX2() { return (this.data >>> 6) & 0b111; }
    getY2() { return (this.data >>> 9) & 0b111; }
    getAttacking() { return (this.data >>> 12) & 1; }
    setAttacking() { this.data |= 1 << 12; }

    equals(other) {
        return other instanceof Move && this.data === other.data;
    }

    // Unique integer key usable in Maps / Sets
    key() { return this.data; }
}

// ── LimitedSizeDict ───────────────────────────────────────────────────────────
// Fixed-capacity Map with FIFO eviction (matches Python LimitedSizeDict).
class LimitedSizeDict {
    constructor(maxSize) {
        this._maxSize = maxSize;
        this._map = new Map();
    }

    has(key) { return this._map.has(key); }

    get(key) { return this._map.get(key); }

    set(key, value) {
        if (!this._map.has(key) && this._map.size >= this._maxSize) {
            // Delete the oldest entry (Map preserves insertion order)
            this._map.delete(this._map.keys().next().value);
        }
        this._map.set(key, value);
    }

    get size() { return this._map.size; }

    clear() { this._map.clear(); }
}

// ── Exports ───────────────────────────────────────────────────────────────────
// Works in both browser (globals on window) and Web Worker (globals on self),
// and in Node.js for testing.
const _exports = {
    empty, Wpawn, Wbishop, Wknight, Wrook, Wqueen, Wking, pieceDivider,
    Bpawn, Bbishop, Bknight, Brook, Bqueen, Bking,
    onGoing, drawRep, staleMate, blackWin, whiteWin,
    Move, LimitedSizeDict,
};

if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = _exports;
} else {
    // Browser / Worker — attach to global scope
    Object.assign(typeof globalThis !== 'undefined' ? globalThis : self, _exports);
}
