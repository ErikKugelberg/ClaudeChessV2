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
- MVV-LVA capture ordering + history heuristic for quiet moves
- Killer move heuristic (2 killers per depth, reset each `botMove()`)
- TT hash-move ordering (3-tuple: depth, eval, best_move)
- Evaluation: passed pawns, rooks on open/semi-open files, isolated pawn penalty

**Reverted — do not re-implement without fixing the root cause:**
- **Quiescence search** (standalone): `getLegalMoves()` and `evaluatePosition()` are too expensive at every leaf; tested at qdepth 1–4, all produced 0% win rate. Now viable again with negamax — attempt using `_quiesce(alpha, beta)` with stand-pat.
- **Null move pruning**: The dual-branch minimax structure caused incorrect cutoffs (now moot since negamax refactor). Still risky — needs zugzwang guard (piece count > 4) and no consecutive null moves.

### GUI — `chessViewer.py`

`boardManager` wraps a matplotlib figure. Board coordinates: visual `(x,y)` maps to board `(bx,by)` based on `playWhite` orientation flag. Two modes selected at startup:
- **Mode 1** (bot-vs-bot): infinite loop with `plt.pause()` between moves
- **Mode 2** (single-player): click handler via `fig.canvas.mpl_connect`; two-click move (select piece → legal destinations shown in red → click destination); bot responds synchronously via `bot2.botMove()`

`TIME_LIMIT` is set from user input at startup (milliseconds → seconds) and controls both modes.
