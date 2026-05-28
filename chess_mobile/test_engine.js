'use strict';
// Tests for the position layer of engine.js
// Run with: node test_engine.js

const {
    empty, Wpawn, Wbishop, Wknight, Wrook, Wqueen, Wking, pieceDivider,
    Bpawn, Bbishop, Bknight, Brook, Bqueen, Bking,
    onGoing, drawRep, staleMate, blackWin, whiteWin, Move,
} = require('./utils.js');
const { ChessEngine } = require('./engine.js');

let passed=0, failed=0;
function assert(cond, label) {
    if (cond) { console.log(`  PASS  ${label}`); passed++; }
    else { console.error(`  FAIL  ${label}`); failed++; }
}

// ── setupPieces ───────────────────────────────────────────────────────────────
console.log('\n=== setupPieces ===');
const e = new ChessEngine();
e.setupPieces();

assert(e.board[0]===Wrook   && e.board[7]===Wrook,   'White rooks on a1/h1');
assert(e.board[4]===Wking,                             'White king on e1');
assert(e.board[3]===Wqueen,                            'White queen on d1');
assert(e.board[56]===Brook  && e.board[63]===Brook,   'Black rooks on a8/h8');
assert(e.board[60]===Bking,                            'Black king on e8');
assert(e.board[8]===Wpawn   && e.board[15]===Wpawn,   'White pawns on rank 2');
assert(e.board[48]===Bpawn  && e.board[55]===Bpawn,   'Black pawns on rank 7');
assert(e.whiteKingPos[0]===4 && e.whiteKingPos[1]===0,'White king pos cached');
assert(e.blackKingPos[0]===4 && e.blackKingPos[1]===7,'Black king pos cached');
assert(e.rkMoved===0,                                  'rkMoved starts at 0');
assert(e.enPas[0]===-1,                                'enPas starts empty');
assert(e.whitesMove===true,                            'White to move first');

// ── getLegalMoves at start ────────────────────────────────────────────────────
console.log('\n=== getLegalMoves at start ===');
const startMoves = e.getLegalMoves();
assert(startMoves.length===20, `20 legal moves at start (got ${startMoves.length})`);

// White should have 16 pawn moves (2 per pawn × 8) + 4 knight moves
const pawnMoves   = startMoves.filter(m=>e.board[m.getX1()+m.getY1()*8]===Wpawn);
const knightMoves = startMoves.filter(m=>e.board[m.getX1()+m.getY1()*8]===Wknight);
assert(pawnMoves.length===16,   `16 pawn moves (got ${pawnMoves.length})`);
assert(knightMoves.length===4,  `4 knight moves (got ${knightMoves.length})`);

// No attacks at start
assert(startMoves.every(m=>m.getAttacking()===0), 'No captures at start');

// ── makeMove: pawn push ───────────────────────────────────────────────────────
console.log('\n=== makeMove: e2-e4 ===');
e.setupPieces();
const e2e4 = new Move(4, 1, 4, 3);
const state = e.makeMove(e2e4, true);
assert(state===onGoing,                        'Game ongoing after e2-e4');
assert(e.board[4+3*8]===Wpawn,                 'Pawn moved to e4');
assert(e.board[4+1*8]===empty,                 'e2 now empty');
assert(!e.whitesMove,                          'Now black to move');
assert(e.enPas[0]===4 && e.enPas[1]===3,      'En passant target set at e4');

// ── En passant capture ────────────────────────────────────────────────────────
console.log('\n=== En passant ===');
e.setupPieces();
// 1.e4 d5 2.e5 d4 — set up a position where white can capture ep
// Actually test the simpler case: 1.e4 e5 2.e4e5 no, let's test: white e5, black plays f5, then e5xf6
e.setupPieces();
// Move white pawn to e5 manually
e.board[4+4*8] = Wpawn; e.board[4+1*8] = empty;  // e pawn to e5
e.whitesMove = false;
// Black plays f5 (pawn from f7 to f5)
const f7f5 = new Move(5, 6, 5, 4);
e.makeMove(f7f5, false);
assert(e.enPas[0]===5 && e.enPas[1]===4,      'En passant set at f5 after f7-f5');
assert(e.whitesMove===true,                    'White to move');
const epCapture = new Move(4, 4, 5, 5);  // e5xf6
epCapture.setAttacking();
const legal = e.getLegalMoves();
const hasEp = legal.some(m=>m.getX1()===4&&m.getY1()===4&&m.getX2()===5&&m.getY2()===5&&m.getAttacking()===1);
assert(hasEp, 'En passant capture e5xf6 is legal');

// ── Castling ──────────────────────────────────────────────────────────────────
console.log('\n=== Castling ===');
const ec = new ChessEngine();
ec.setupPieces();
// Clear squares between king and kingside rook
ec.board[5] = empty; ec.board[6] = empty;
const moves = ec.getLegalMoves();
const hasCastle = moves.some(m=>m.getX1()===4&&m.getY1()===0&&m.getX2()===6&&m.getY2()===0);
assert(hasCastle, 'White kingside castling available when path clear');

// After castling, rook should move to f1
const castle = new Move(4, 0, 6, 0);
ec.makeMove(castle, false);
assert(ec.board[6]===Wking, 'King moved to g1 after castling');
assert(ec.board[5]===Wrook, 'Rook moved to f1 after castling');
assert(ec.board[4]===empty, 'e1 now empty');
assert(ec.board[7]===empty, 'h1 now empty');
assert(ec.rkMoved & 16,     'rkMoved bit 4 set (white king moved)');

// ── Queen-side castling ───────────────────────────────────────────────────────
console.log('\n=== Queenside castling ===');
const eq = new ChessEngine();
eq.setupPieces();
eq.board[1]=empty; eq.board[2]=empty; eq.board[3]=empty;  // clear b1,c1,d1
const qMoves = eq.getLegalMoves();
const hasQCastle = qMoves.some(m=>m.getX1()===4&&m.getY1()===0&&m.getX2()===2&&m.getY2()===0);
assert(hasQCastle, 'White queenside castling available');
const qCastle = new Move(4, 0, 2, 0);
eq.makeMove(qCastle, false);
assert(eq.board[2]===Wking, 'King moved to c1 after queenside castling');
assert(eq.board[3]===Wrook, 'Rook moved to d1 after queenside castling');
assert(eq.board[0]===empty, 'a1 now empty');

// ── _kingChecked ──────────────────────────────────────────────────────────────
console.log('\n=== _kingChecked ===');
const ek = new ChessEngine();
ek.setupPieces();
assert(!ek._kingChecked(true),  'White king not in check at start');
assert(!ek._kingChecked(false), 'Black king not in check at start');

// Place enemy queen adjacent to white king
ek.board[4] = Bqueen;  // d1 — replaces white queen but threatens king on e1
// Actually white king is on e1 (sq 4). Put a black rook at e8 and clear the file.
ek.setupPieces();
for (let y=1;y<=6;y++) ek.board[4+y*8]=empty;  // clear e file
ek.board[4+7*8] = Brook;  // Brook at e8
assert(ek._kingChecked(true), 'White king in check from rook on open file');

// ── Check detection: no false positives ──────────────────────────────────────
ek.setupPieces();
ek.board[4+7*8] = Brook;  // Brook on e-file but it's blocked by black pawns on rank 7
assert(!ek._kingChecked(true), 'White king NOT in check (black own pieces block)');

// ── Promotion ─────────────────────────────────────────────────────────────────
console.log('\n=== Promotion ===');
const ep = new ChessEngine();
ep.setupPieces();
// Put a white pawn on e7 (one step from promotion)
ep.board[4+6*8] = Wpawn; ep.board[4+1*8] = empty;
ep.board[4+7*8] = empty;  // clear the target square (black's e8 has a bishop normally)
ep.board[2+7*8] = empty; ep.board[5+7*8] = empty;  // also clear to avoid confusion
ep.whitesMove = true;
const promoMoves = ep.getLegalMoves().filter(m=>m.getX1()===4&&m.getY1()===6&&m.getX2()===4&&m.getY2()===7);
assert(promoMoves.length===1, 'Pawn promotion move found');
ep.makeMove(promoMoves[0], false);
assert(ep.board[4+7*8]===Wqueen, 'Pawn promoted to queen');

// ── evaluatePosition at start ─────────────────────────────────────────────────
console.log('\n=== evaluatePosition ===');
const ee = new ChessEngine();
ee.setupPieces();
const startEval = ee.evaluatePosition();
// At start, position should be roughly 0 (symmetric) plus tempo bonus
assert(Math.abs(startEval) < 100, `Start eval near 0 (got ${startEval})`);

// Material imbalance: remove a black pawn
ee.setupPieces();
ee.board[48] = empty;  // remove black a-pawn
const materialEval = ee.evaluatePosition();
assert(materialEval > 50, `White ahead after removing black pawn (eval=${materialEval})`);

// ── Stalemate detection ───────────────────────────────────────────────────────
console.log('\n=== Stalemate ===');
const es = new ChessEngine();
es.setupPieces();
// Set up a stalemate: black king in corner with no moves, not in check
es.board = new Array(64).fill(empty);
es.board[63] = Bking;  es.blackKingPos=[7,7];
es.board[4]  = Wking;  es.whiteKingPos=[4,0];
es.board[53] = Wqueen; // queen on f7, covers f8 and g8, not giving check
es.whitesMove = false;
es.rkMoved = 0b111111;  // no rooks present in this test position — mark all castling lost
const sLegal = es.getLegalMoves();
assert(sLegal.length===0, `Stalemate: 0 legal moves for black (got ${sLegal.length})`);
assert(!es._kingChecked(false), 'Black king not in check in stalemate');

// ── _undoMove correctness ──────────────────────────────────────────────────────
console.log('\n=== _undoMove ===');
const eu = new ChessEngine();
eu.setupPieces();
const snap = eu.board.slice();
const mv = new Move(4,1,4,3);
const rec = eu._saveState(mv);
eu.makeMove(mv);
eu._undoMove(rec);
assert(eu.board.join(',')===snap.join(','), 'Board restored after undo');
assert(eu.whitesMove===true,               'Turn restored after undo');
assert(eu.enPas[0]===-1,                   'enPas restored after undo');

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
