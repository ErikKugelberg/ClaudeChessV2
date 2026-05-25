# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

```powershell
# Automated benchmark: bot1 vs bot2, logs to logs/benchmark_<timestamp>.log
python botFighter.py
python botFighter.py --games 20 --time-limit 0.5

# GUI viewer: watch bots play or play against bot2 interactively
python botWatch.py
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

### GUI — `botWatch.py`

`boardManager` wraps a matplotlib figure. Board coordinates: visual `(x,y)` maps to board `(bx,by)` based on `playWhite` orientation flag. Two modes selected at startup:
- **Mode 1** (bot-vs-bot): infinite loop with `plt.pause()` between moves
- **Mode 2** (single-player): click handler via `fig.canvas.mpl_connect`; two-click move (select piece → legal destinations shown in red → click destination); bot responds synchronously via `bot2.botMove()`

`TIME_LIMIT` is set from user input at startup (milliseconds → seconds) and controls both modes.
