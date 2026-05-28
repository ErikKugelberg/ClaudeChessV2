"""
build_html.py — assembles chess_mobile.html from utils.js + engine.js + the UI template.
Run from any directory: python chess_mobile/build_html.py
Output: chess_mobile/chess_mobile.html
"""
import os, pathlib

HERE    = pathlib.Path(__file__).parent
ROOT    = HERE.parent
OUT     = HERE / 'chess_mobile.html'

utils_src  = (HERE / 'utils.js').read_text(encoding='utf-8')
engine_src = (HERE / 'engine.js').read_text(encoding='utf-8')

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = r"""
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #1a1a2e;
  color: #eee;
  font-family: system-ui, -apple-system, sans-serif;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: max(env(safe-area-inset-top), 8px) 8px max(env(safe-area-inset-bottom), 8px);
  gap: 8px;
}

h1 {
  font-size: 1.15rem;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: #d4af37;
  margin-top: 4px;
}

:root {
  --sq: min(calc(96vw / 8), calc((100dvh - 185px) / 8), 74px);
}

#status {
  font-size: 0.95rem;
  color: #ddd;
  min-height: 1.4em;
  text-align: center;
}

#board-wrap {
  position: relative;
  user-select: none;
  -webkit-user-select: none;
}

#board {
  display: grid;
  grid-template-columns: repeat(8, var(--sq));
  grid-template-rows: repeat(8, var(--sq));
  border: 2px solid #444;
  touch-action: manipulation;
}

.sq {
  width: var(--sq);
  height: var(--sq);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  font-size: calc(var(--sq) * 0.80);
  line-height: 1;
  -webkit-tap-highlight-color: transparent;
}

.sq.light { background: #f0d9b5; }
.sq.dark  { background: #b58863; }

.sq.selected  { background: #f6f669 !important; }
.sq.last-from { background: rgba(155,199,0,0.45) !important; }
.sq.last-to   { background: rgba(155,199,0,0.45) !important; }

.piece {
  pointer-events: none;
  position: relative;
  z-index: 1;
}
.piece.wp { color: #fff;  text-shadow: 0 1px 3px #222, 0 0 2px #555; }
.piece.bp { color: #111;  text-shadow: 0 1px 2px rgba(255,255,255,0.7); }

/* Legal move: dot for quiet square, ring for capture */
.sq.legal-quiet::after {
  content: '';
  position: absolute;
  width: 32%;
  height: 32%;
  border-radius: 50%;
  background: rgba(0,0,0,0.22);
  pointer-events: none;
}
.sq.legal-capture::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: calc(var(--sq) * 0.1) solid rgba(0,0,0,0.22);
  pointer-events: none;
  z-index: 2;
}

/* Coordinate labels on edge squares */
.rank-label, .file-label {
  position: absolute;
  font-size: calc(var(--sq) * 0.21);
  font-weight: 700;
  line-height: 1;
  pointer-events: none;
  z-index: 3;
}
.rank-label { top: 2px; left: 2px; }
.file-label { bottom: 2px; right: 2px; }
.sq.light .rank-label, .sq.light .file-label { color: #b58863; }
.sq.dark  .rank-label, .sq.dark  .file-label  { color: #f0d9b5; }

/* Blocks board interaction while bot is thinking */
#thinking-overlay {
  display: none;
  position: absolute;
  inset: 0;
  cursor: wait;
  z-index: 10;
}
#thinking-overlay.active { display: block; }

#info {
  font-size: 0.78rem;
  color: #999;
  text-align: center;
  min-height: 1.1em;
}

#controls {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
}

button {
  background: #d4af37;
  color: #1a1a2e;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}
button:active { opacity: 0.75; }

select {
  background: #252540;
  color: #eee;
  border: 1px solid #555;
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 0.88rem;
}

.side-btns { display: flex; gap: 4px; }
.side-btn {
  background: #252540;
  color: #bbb;
  border: 1px solid #555;
  border-radius: 6px;
  padding: 7px 12px;
  font-size: 0.85rem;
  font-weight: 400;
  cursor: pointer;
}
.side-btn.active {
  background: #d4af37;
  color: #1a1a2e;
  border-color: #d4af37;
  font-weight: 700;
}

#result-banner {
  display: none;
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(10,10,30,0.92);
  color: #fff;
  padding: 28px 44px;
  border-radius: 14px;
  font-size: 1.3rem;
  font-weight: 700;
  text-align: center;
  z-index: 100;
  box-shadow: 0 6px 40px rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  min-width: 240px;
}
#result-banner.show { display: block; }
#result-banner button { margin-top: 18px; width: 100%; font-size: 1rem; }
"""

# ── Main game JS ───────────────────────────────────────────────────────────────
GAME_JS = r"""
'use strict';

// ── Piece Unicode symbols ──────────────────────────────────────────────────────
// Index by piece ID: empty=0,Wpawn=1,Wbishop=2,Wknight=3,Wrook=4,Wqueen=5,Wking=6,
//                   div=7,Bpawn=8,Bbishop=9,Bknight=10,Brook=11,Bqueen=12,Bking=13
const PIECE_CHAR = ['','♙','♗','♘','♖','♕','♔','','♟','♝','♞','♜','♛','♚'];

// ── Web Worker (bot runs in background thread) ─────────────────────────────────
const _utilsSrc  = document.getElementById('utils-src').textContent;
const _engineSrc = document.getElementById('engine-src').textContent;

const _workerHandler = `
'use strict';
self.onmessage = function(evt) {
    const {state, timeLimit} = evt.data;
    const eng = new ChessEngine();
    eng.board              = state.board;
    eng.whitesMove         = state.whitesMove;
    eng.rkMoved            = state.rkMoved;
    eng.enPas              = state.enPas;
    eng.nonPawnCount       = state.nonPawnCount;
    eng.boardHistory       = state.boardHistory;
    eng.boardHistoryCounts = state.boardHistoryCounts;
    eng.whiteKingPos       = state.whiteKingPos;
    eng.blackKingPos       = state.blackKingPos;
    const [move, depth, elapsed, whiteEval] = eng.botMove(timeLimit);
    self.postMessage({
        moveData:  move ? move.data : null,
        depth:     depth - 1,
        elapsed:   elapsed,
        whiteEval: whiteEval,
        nodes:     eng.i
    });
};
`;

const _wBlob = new Blob([_utilsSrc, '\n', _engineSrc, '\n', _workerHandler],
                         {type: 'application/javascript'});
const _wUrl  = URL.createObjectURL(_wBlob);
let _worker  = null;

function _getWorker() {
    if (!_worker) {
        _worker = new Worker(_wUrl);
        _worker.onmessage = onWorkerMessage;
        _worker.onerror   = err => {
            console.error('Worker error:', err);
            setThinking(false);
        };
    }
    return _worker;
}

// ── Game state ─────────────────────────────────────────────────────────────────
const engine   = new ChessEngine();
let playWhite  = true;   // human plays white
let thinking   = false;
let gameOver   = false;
let selected   = -1;     // selected board square index, -1 = none
let legalDests = new Set();
let lastFrom   = -1;
let lastTo     = -1;
let lastDepth  = 0;
let lastNodes  = 0;
let lastEval   = null;

// ── DOM refs ───────────────────────────────────────────────────────────────────
const boardEl   = document.getElementById('board');
const statusEl  = document.getElementById('status');
const infoEl    = document.getElementById('info');
const overlayEl = document.getElementById('thinking-overlay');

// sqEls[sq] → the <div> for board square sq
const sqEls = new Array(64);

// ── Board rendering ────────────────────────────────────────────────────────────
function buildBoard() {
    boardEl.innerHTML = '';
    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            // Convert visual (row, col) to board coords
            const y  = playWhite ? (7 - row) : row;
            const x  = playWhite ? col : (7 - col);
            const sq = y * 8 + x;
            const isLight = (x + y) % 2 !== 0;

            const div = document.createElement('div');
            div.className = 'sq ' + (isLight ? 'light' : 'dark');
            div.dataset.sq = sq;

            // Rank label on leftmost column
            if (col === 0) {
                const rl = document.createElement('span');
                rl.className = 'rank-label';
                rl.textContent = y + 1;
                div.appendChild(rl);
            }
            // File label on bottom row
            if (row === 7) {
                const fl = document.createElement('span');
                fl.className = 'file-label';
                fl.textContent = 'abcdefgh'[x];
                div.appendChild(fl);
            }

            div.addEventListener('click', () => onSquareClick(sq));
            boardEl.appendChild(div);
            sqEls[sq] = div;
        }
    }
}

function renderBoard() {
    for (let sq = 0; sq < 64; sq++) {
        const el = sqEls[sq];
        if (!el) continue;

        // Update piece
        const piece = engine.board[sq];
        const existing = el.querySelector('.piece');
        if (existing) existing.remove();

        if (piece !== empty) {
            const span = document.createElement('span');
            span.className = 'piece ' + (piece < pieceDivider ? 'wp' : 'bp');
            span.textContent = PIECE_CHAR[piece];
            el.appendChild(span);
        }

        // Highlights
        el.classList.remove('selected', 'last-from', 'last-to', 'legal-quiet', 'legal-capture');
        if (sq === selected)          el.classList.add('selected');
        else if (sq === lastFrom)     el.classList.add('last-from');
        else if (sq === lastTo)       el.classList.add('last-to');
        if (legalDests.has(sq)) {
            el.classList.add(piece !== empty ? 'legal-capture' : 'legal-quiet');
        }
    }
}

// ── Click / tap handling ───────────────────────────────────────────────────────
function onSquareClick(sq) {
    if (thinking || gameOver) return;
    if (engine.whitesMove !== playWhite) return;  // not human's turn

    // Clicking the selected square deselects
    if (sq === selected) {
        selected = -1;
        legalDests.clear();
        renderBoard();
        return;
    }

    // Clicking a legal destination: make the move
    if (selected !== -1 && legalDests.has(sq)) {
        doHumanMove(selected, sq);
        return;
    }

    // Otherwise try to select this square if it has our piece
    const piece = engine.board[sq];
    const isOwn = playWhite
        ? (piece > 0 && piece < pieceDivider)
        : (piece > pieceDivider);
    if (!isOwn) { selected = -1; legalDests.clear(); renderBoard(); return; }

    selected = sq;
    legalDests.clear();
    const fx = sq & 7, fy = sq >> 3;
    for (const m of engine.getLegalMoves()) {
        if (m.getX1() === fx && m.getY1() === fy)
            legalDests.add(m.getX2() + m.getY2() * 8);
    }
    renderBoard();
}

function doHumanMove(fromSq, toSq) {
    const fx = fromSq & 7, fy = fromSq >> 3;
    const tx = toSq   & 7, ty = toSq   >> 3;

    const move = engine.getLegalMoves().find(m =>
        m.getX1()===fx && m.getY1()===fy && m.getX2()===tx && m.getY2()===ty
    );
    if (!move) return;

    lastFrom = fromSq;
    lastTo   = toSq;
    selected = -1;
    legalDests.clear();

    const state = engine.makeMove(move, true);
    renderBoard();
    updateStatus();

    if (state !== onGoing) { handleGameOver(state); return; }
    startBotThinking();
}

// ── Bot integration ────────────────────────────────────────────────────────────
function startBotThinking() {
    setThinking(true);
    const timeLimit = parseFloat(document.getElementById('sel-diff').value);
    _getWorker().postMessage({
        timeLimit,
        state: {
            board:              Array.from(engine.board),
            whitesMove:         engine.whitesMove,
            rkMoved:            engine.rkMoved,
            enPas:              engine.enPas.slice(),
            nonPawnCount:       engine.nonPawnCount,
            boardHistory:       engine.boardHistory.slice(),
            boardHistoryCounts: Object.assign({}, engine.boardHistoryCounts),
            whiteKingPos:       engine.whiteKingPos.slice(),
            blackKingPos:       engine.blackKingPos.slice(),
        }
    });
}

function onWorkerMessage(evt) {
    setThinking(false);
    if (gameOver) return;

    const {moveData, depth, elapsed, whiteEval, nodes} = evt.data;

    if (moveData === null) {
        // botMove found no moves
        const moves  = engine.getLegalMoves();
        const gState = moves.length === 0
            ? (engine._kingChecked(engine.whitesMove)
               ? (engine.whitesMove ? blackWin : whiteWin)
               : staleMate)
            : drawRep;
        handleGameOver(gState);
        return;
    }

    // Reconstruct Move from encoded integer and apply
    const botMv  = new Move(0,0,0,0);
    botMv.data   = moveData;

    lastFrom  = botMv.getX1() + botMv.getY1() * 8;
    lastTo    = botMv.getX2() + botMv.getY2() * 8;
    lastDepth = depth;
    lastNodes = nodes;
    lastEval  = whiteEval;

    const gState = engine.makeMove(botMv, true);
    renderBoard();
    updateStatus();
    updateInfo();

    if (gState !== onGoing) handleGameOver(gState);
}

function setThinking(val) {
    thinking = val;
    overlayEl.classList.toggle('active', val);
    if (val) statusEl.textContent = 'Thinking…';
}

// ── Game flow ──────────────────────────────────────────────────────────────────
function startNewGame() {
    if (thinking && _worker) {
        // Terminate and recreate so we don't get stale responses
        _worker.terminate();
        _worker = null;
    }
    gameOver   = false;
    thinking   = false;
    selected   = -1;
    legalDests.clear();
    lastFrom   = -1;
    lastTo     = -1;
    lastDepth  = 0;
    lastNodes  = 0;
    lastEval   = null;
    overlayEl.classList.remove('active');

    engine.setupPieces();
    buildBoard();
    renderBoard();
    updateStatus();
    updateInfo();

    // If human plays black, bot moves first
    if (!playWhite) startBotThinking();
}

function handleGameOver(state) {
    gameOver = true;
    let msg;
    if      (state === drawRep)   msg = '½–½  Draw by repetition';
    else if (state === staleMate) msg = '½–½  Stalemate';
    else if (state === whiteWin)  msg = '1–0  White wins!';
    else if (state === blackWin)  msg = '0–1  Black wins!';
    else                          msg = 'Game over';

    statusEl.textContent = msg;
    document.getElementById('result-text').textContent = msg;
    document.getElementById('result-banner').classList.add('show');
}

function updateStatus() {
    if (gameOver) return;
    const inCheck = engine._kingChecked(engine.whitesMove);
    const who     = engine.whitesMove ? 'White' : 'Black';
    statusEl.textContent = inCheck ? `${who} to move — Check!` : `${who} to move`;
}

function updateInfo() {
    if (lastEval === null) { infoEl.textContent = ''; return; }
    const sign  = lastEval >= 0 ? '+' : '';
    const pawn  = (lastEval / 100).toFixed(2);
    const kn    = (lastNodes / 1000).toFixed(1);
    infoEl.textContent = `Depth ${lastDepth}  ·  Eval ${sign}${pawn}  ·  ${kn}k nodes`;
}

// ── Controls ───────────────────────────────────────────────────────────────────
document.getElementById('btn-new').addEventListener('click', startNewGame);

document.getElementById('btn-white').addEventListener('click', () => {
    playWhite = true;
    document.getElementById('btn-white').classList.add('active');
    document.getElementById('btn-black').classList.remove('active');
    startNewGame();
});
document.getElementById('btn-black').addEventListener('click', () => {
    playWhite = false;
    document.getElementById('btn-white').classList.remove('active');
    document.getElementById('btn-black').classList.add('active');
    startNewGame();
});

// Close result banner and start new game
document.getElementById('btn-play-again').addEventListener('click', () => {
    document.getElementById('result-banner').classList.remove('show');
    startNewGame();
});

// ── Boot ───────────────────────────────────────────────────────────────────────
startNewGame();
"""

# ── HTML template ─────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>Chess</title>
  <style>{CSS}</style>
</head>
<body>

<h1>♟ Chess</h1>
<div id="status">White to move</div>

<div id="board-wrap">
  <div id="board"></div>
  <div id="thinking-overlay"></div>
</div>

<div id="info"></div>

<div id="controls">
  <button id="btn-new">New Game</button>
  <select id="sel-diff" title="Bot thinking time">
    <option value="0.3">Easy (0.3 s)</option>
    <option value="1.0" selected>Medium (1 s)</option>
    <option value="3.0">Hard (3 s)</option>
  </select>
  <div class="side-btns">
    <button class="side-btn active" id="btn-white">White</button>
    <button class="side-btn"        id="btn-black">Black</button>
  </div>
</div>

<div id="result-banner">
  <div id="result-text"></div>
  <button id="btn-play-again">Play Again</button>
</div>

<!-- utils.js — executed as script AND readable as text for the worker blob -->
<script type="text/javascript" id="utils-src">
{utils_src}
</script>

<!-- engine.js — executed as script AND readable as text for the worker blob -->
<script type="text/javascript" id="engine-src">
{engine_src}
</script>

<script>
{GAME_JS}
</script>

</body>
</html>"""

OUT.write_text(HTML, encoding='utf-8')
print(f"Built {OUT}  ({OUT.stat().st_size // 1024} KB)")
