# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

```powershell
# Standard benchmark: 10 games, 0.5s per move — use this for all bot2 evaluations
python botFighter.py --games 10 --time-limit 0.5

# GUI viewer: watch bots play or play against bot2 interactively
python chessViewer.py
```

Both scripts require `matplotlib`, `numpy`, and standard library only.

## Folder Layout

```
ClaudeChessV2/
├── bot1.py, bot2.py, botFighter.py, chessViewer.py  ← runnable scripts
├── utils.py          ← shared types/constants (must stay in root; bot1.py imports it)
├── CLAUDE.md, README.md, .gitignore, stockfish.exe
├── chess_mobile/     ← mobile web UI (see section below)
├── docs/             ← diagrams, PDF report, FuturePlans.txt
├── logs/             ← all benchmark .log files (botFighter writes here automatically)
└── tools/            ← utility/debug scripts (attack_table_diagram.py, evalTest.py, etc.)
```

## Architecture

The project is a Python chess engine with two bot implementations that compete against each other.

### Core Types — `utils.py`

- Piece constants: `empty=0`, white pieces `Wpawn..Wking` (1–6), `pieceDivider=7`, black pieces `Bpawn..Bking` (8–13)
- Game state constants: `onGoing`, `drawRep`, `staleMate`, `blackWin`, `whiteWin`
- `Move` — packs `x1,y1,x2,y2,isAttacking` into a single `int16` using bit shifts; use `getX1()..getAttacking()` accessors
- `LimitedSizeDict` — fixed-capacity dict with FIFO eviction; used as a transposition/eval cache
- Board layout: flat 64-element list indexed as `board[y*8 + x]`, origin at bottom-left (white's side)

### Bot Engines

**`bot1.py` (`chessBoard1`)** — frozen baseline. Never modify this file. It uses full `board.copy()` for search undo and calls `evaluatePosition()` per candidate move for ordering (expensive but effective tree shape).

**`bot2.py` (`chessBoard2`)** — the engine under active development. Key differences from bot1:
- `UndoRecord` class stores only changed squares (2–4 pairs) instead of copying all 64 elements on every search node
- `_saveState(move)` / `_undoMove(rec)` implement the incremental undo
- `whiteKingPos` / `blackKingPos` are tracked incrementally so `_kingChecked()` doesn't scan all 64 squares
- Move ordering uses MVV-LVA for captures (`1_000_000 + 10*victim - attacker`) and history heuristic for quiet moves; `_history[from][to]` is incremented by `(depth+1)²` at each beta-cutoff

Both bots expose the same interface:
- `setupPieces()` — reset to starting position
- `makeMove(move, frfr=False)` — apply a move; returns game state code
- `botMove(depthLimit, timeLimit)` — iterative-deepening search; returns `(move, depth, elapsed, evaluation)`
- `getLegalMoves()` — list of `Move` objects for the side to move
- `getPosition()` — returns current board list
- `_kingChecked(white)` — returns bool
- Public stats after `botMove()`: `.i` (leaf nodes evaluated), `.prunings` (beta cutoffs)

### Two-Bot Synchronisation

During a bot-vs-bot game, each bot independently tracks the full position. After bot A plays a move, `bot_B.makeMove(move, frfr=True)` is called to sync B's state. The `frfr=True` flag skips legality checking (trust the move came from the opponent's engine). After each full move, `white_bot.getPosition() == black_bot.getPosition()` is asserted.

### Benchmark Harness — `botFighter.py`

CLI script that runs N games with alternating colors (bot1=white on odd games) and writes structured per-move logs. Access internal stats via `bot.i` and `bot.prunings` as public attributes — `botMove()` itself returns only a 4-tuple.

**Benchmark protocol:** Always run `--games 10 --time-limit 0.5`. Run benchmarks in the background so they don't block. After each implementation, check: (1) no crashes, (2) avg_depth increases or avg_nodes/move decreases, (3) win rate does not drop significantly below ~55%.

### Search Architecture — bot2

bot2 uses **negamax** (not dual-branch minimax). Scores are always relative to the side to move (positive = good for current player). Key implications:
- `evaluatePosition()` returns a white-positive absolute score; bot2 negates it when it's black's turn at leaf nodes
- Alpha/beta window is passed as `(-beta, -alpha)` on recursive calls and the result is negated
- **Timeout sentinel**: uses `self._stop_search` flag rather than returning `±inf`. When time expires, the flag is set and every ancestor node breaks without incorporating the timed-out score. This prevents `-inf` being negated to `+inf` and corrupting the search.

**Implemented and working:**
- Incremental undo (`UndoRecord`) and king position tracking
- `nonPawnCount` tracked incrementally in `_movePieces` / `_undoMove` (avoids O(64) scan per null-move guard)
- `boardHistoryCounts` O(1) dict alongside `boardHistory` list (avoids O(game_length) `.count()` per node)
- MVV-LVA capture ordering + history heuristic for quiet moves
- Killer move heuristic (2 killers per depth, 128-slot array, reset each `botMove()`)
- TT hash-move ordering (3-tuple: depth, eval, best_move); 2_000_000 priority in `_sortMoves`
- TT cleared per-iteration in `botMove()`: prevents cross-depth parity contamination (odd-depth tempo +17 vs even-depth −17 causes ~86 cp swing that corrupts cross-depth TT hits)
- `findBestMove` strict improvement tracking (`if score > best_score`) prevents fail-high lower-bounds from spuriously displacing the true best move
- Null move pruning (negamax, R=2, placed BEFORE `getLegalMoves()` so pruned nodes skip the expensive call; guards: `remaining > R`, not in check, `nonPawnCount > 4`)
- LMR — Late Move Reductions (thresholds: `move_idx ≥ 5`, `remaining ≥ 3`, quiet move, not in check; probe with `allow_null=False` to prevent cascading null move inside LMR)
- Stand-pat at `remaining==0`: player can choose not to capture; returns early if `stand_pat ≥ beta`; filters losing captures (`victim_value × 3 < attacker_value`)
- Evaluation: passed pawns (rank-scaled bonus), rooks on open/semi-open files (+50/+25), isolated pawn penalty (−20), doubled pawn penalty, bishop pair bonus (+30 cp), king safety pawn shield (+15 for pawn immediately ahead, +7 for pawn two ranks ahead, middlegame only)
- En passant MVV-LVA fix: en passant captures now correctly ordered with other captures (use pawn value as victim_val since destination square is empty)
- `_toString` uses `bytes(board)` instead of big-integer bit-shifting: 18× faster (0.25µs vs 4.5µs per call)
- Precomputed attack tables in `evaluatePosition()`: `_KNIGHT_ATTACKS[64]`, `_KING_ATTACKS[64]`, `_WPAWN_ATTACKS[64]`, `_BPAWN_ATTACKS[64]` (bitboards per square), `_ROOK_RAYS[64]`, `_BISHOP_RAYS[64]`, `_QUEEN_RAYS[64]` (pre-stored index lists per ray). Eliminated all `_getMoves()` calls from eval. Avg depth improved 7.12→7.57.
- **Absolute pin detection in `getLegalMoves()`**: Pre-computes pinned squares via O(64) ray-trace from king before iterating candidates. Non-pinned, non-king pieces skip `_legalMove()` entirely (~20 saved calls per node). En passant captures always check legality (can expose rank pin). King moves and pinned pieces still call `_legalMove()` as before.
- **Quiescence search (`_quiesce`)**: Called at `depth==0` instead of `evaluatePosition()`. Stand-pat + recursive capture search until no good captures remain. Filters losing captures (SEE: `victim×3 < attacker`). MVV-LVA sorted. `depth==0` check moved before TT lookup to avoid wasted hash per leaf. Also fixed en passant capture missing `setAttacking()` flag in `getLegalMoves()`. Result: **100% win rate (10W 0D 0L)**, blunders 34→9, avg depth 8.07.

**Reverted — do not re-implement without fixing the root cause:**
- **Aspiration windows**: ±50 cp window always fails due to ~86 cp parity oscillation between even/odd depths; causes 2× work and TT contamination (narrow-window stale entries pollute full-window retry). Do NOT re-implement.
- **PVS (Principal Variation Search)**: Python function call overhead (~0.1–0.5 ms/call) exceeds node-saving benefit. Result: 30% win rate (down from 85%). Do NOT implement.
- **Proper TT node types** (exact/lower/upper bound): The "incorrect" all-exact TT provides faster cutoffs. Correct node types cause positions that previously returned immediately to continue searching — more nodes, fewer iterations. Result: 0% wins in first 2 games. The current "incorrect" TT is actually stronger. Do NOT change.
- **Futility pruning** (`remaining==1`): Previously unsound without quiescence. Quiescence is now in place, so futility may be implementable. Previously tested: 20–40% win rate without quiescence.
- **History malus** (quiet moves that fail low get `history -= entry_depth`): Causes ordering regression — the same quiet move can be good in some subtrees and bad in others; malus from one context penalizes it in unrelated contexts. Result: search depth drops from 6.6 to ~4 (completed depth 3), clearly worse. Do NOT re-implement.

### Mobile Web UI — `chess_mobile/`

A single self-contained HTML file playable in any mobile browser — no server, no internet, no installation.

**Files:**
```
chess_mobile/
├── build_html.py     ← assembler script; always edit this, never edit chess_mobile.html directly
├── utils.js          ← JS port of utils.py (Move, LimitedSizeDict, piece constants)
├── engine.js         ← JS port of bot2.py (ChessEngine class, full search + eval)
├── chess_mobile.html ← generated output (~67 KB); open directly in any browser
├── test_utils.js     ← Node.js unit tests for utils.js
└── test_engine.js    ← Node.js unit tests for engine.js
```

**Build:**
```powershell
python chess_mobile/build_html.py
```

**Run tests (requires Node.js):**
```powershell
node chess_mobile/test_utils.js
node chess_mobile/test_engine.js
```

**Architecture:**
- `build_html.py` reads `utils.js` + `engine.js` and inlines them into the HTML template as `<script id="utils-src">` / `<script id="engine-src">`.
- The bot runs in a **Web Worker** (blob URL built from the two inlined scripts + a handler stub), keeping the UI responsive during search.
- Game JS reads the two script tags' `.textContent` to construct the worker blob at runtime.

**Critical browser gotcha — IIFE wrapper:**
`utils.js` and `engine.js` both declare `const empty`, `const Move`, etc. at their top level. In browsers, all `<script>` tags share the same global lexical environment, so the second script's `const` declarations throw `SyntaxError: Identifier 'empty' has already been declared`. Fix: `build_html.py` wraps the engine-src content in an IIFE:
```js
(function() {
  /* engine.js content */
})();
```
Do NOT remove this wrapper. It is also harmless inside the worker blob (worker combines both scripts in one realm; the IIFE keeps engine's consts function-scoped).

**UI features:**
- Play as White or Black against the bot, or watch **Bot vs Bot** (engine drives both sides automatically).
- Time options: Fast (0.1 s) / Normal (1 s) / Slow (10 s) per move.
- Board flips to always show the human's side at the bottom.
- Legal move dots/rings on tap, last-move highlight, check indicator, result banner.

**engine.js exports (dual-environment pattern):**
```js
const _engineExports = { ChessEngine };
if (typeof module !== 'undefined' && module.exports) {
    module.exports = _engineExports;   // Node.js (tests, require())
} else {
    Object.assign(typeof globalThis !== 'undefined' ? globalThis : self, _engineExports);
}
```
The import block at the top of `engine.js` uses the same pattern to pull from `require('./utils.js')` in Node and from the global object in the browser/worker.

### GUI — `chessViewer.py`

`boardManager` wraps a matplotlib figure. Board coordinates: visual `(x,y)` maps to board `(bx,by)` based on `playWhite` orientation flag. Two modes selected at startup:
- **Mode 1** (bot-vs-bot): infinite loop with `plt.pause()` between moves
- **Mode 2** (single-player): click handler via `fig.canvas.mpl_connect`; two-click move (select piece → legal destinations shown in red → click destination); bot responds synchronously via `bot2.botMove()`

`TIME_LIMIT` is set from user input at startup (milliseconds → seconds) and controls both modes.
