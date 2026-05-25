"""
botFighter.py — Automated benchmark harness for comparing chessBoard1 vs chessBoard2.

Usage:
    python botFighter.py [--games N] [--time-limit T]

    --games      Number of games to play (default: 20, must be even for balanced colors)
    --time-limit Seconds allowed per move (default: 0.5)

Outputs a structured log to logs/benchmark_<timestamp>.log and prints a
summary table to stdout after all games complete.
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Optional, Tuple

from utils import (
    onGoing, drawRep, staleMate, blackWin, whiteWin,
    Move,
)
from bot1 import chessBoard1
from bot2 import chessBoard2

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_MOVES_PER_GAME = 250   # half-moves; game declared draw beyond this

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger(log_dir: str = "logs") -> Tuple[logging.Logger, str]:
    """Create a dual-target logger (file + stdout)."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"benchmark_{timestamp}.log")

    fmt = logging.Formatter("%(message)s")
    logger = logging.getLogger("benchmark")
    logger.setLevel(logging.DEBUG)
    # Avoid duplicate handlers when the module is reloaded
    logger.handlers.clear()

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger, log_path


# ---------------------------------------------------------------------------
# Move / eval formatting helpers
# ---------------------------------------------------------------------------

def _eval_str(evaluation: float) -> str:
    val = round(evaluation / 100, 2)
    return f"+{val:.2f}" if val >= 0 else f"{val:.2f}"


def _move_str(move: Move) -> str:
    cols = "abcdefgh"
    return (
        f"{cols[move.getX1()]}{move.getY1() + 1}"
        f"{cols[move.getX2()]}{move.getY2() + 1}"
    )


# ---------------------------------------------------------------------------
# Per-move logger
# ---------------------------------------------------------------------------

def log_move(
    log: logging.Logger,
    game_num: int,
    half_move: int,
    color: str,          # "W" or "B"
    bot_label: str,      # "bot1" or "bot2"
    move: Move,
    depth: int,
    nodes: int,
    prunings: int,
    elapsed: float,
    evaluation: float,
) -> None:
    log.info(
        f"[G{game_num:02d} M{half_move:03d} {color}/{bot_label}] "
        f"depth={depth} nodes={nodes} prunings={prunings} "
        f"time={elapsed:.2f}s eval={_eval_str(evaluation)} move={_move_str(move)}"
    )


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

def _result_label(result_code: int, white_label: str, black_label: str) -> str:
    """Translate internal result code to human-readable string."""
    if result_code == whiteWin:
        return f"{white_label.upper()} WINS (white)"
    if result_code == blackWin:
        return f"{black_label.upper()} WINS (black)"
    if result_code == staleMate:
        return "DRAW (stalemate)"
    if result_code == drawRep:
        return "DRAW (repetition)"
    return "DRAW (move limit)"


# ---------------------------------------------------------------------------
# Single-game runner
# ---------------------------------------------------------------------------

def run_game(
    game_num: int,
    bot1: chessBoard1,
    bot2: chessBoard2,
    bot1_plays_white: bool,
    time_limit: float,
    log: logging.Logger,
) -> Tuple[int, int, int, List[int], List[int], List[int], List[int]]:
    """
    Play one complete game.

    Returns
    -------
    (result_code, total_half_moves,
     bot1_depths, bot2_depths, bot1_nodes, bot2_nodes)
    where result_code is one of: whiteWin, blackWin, staleMate, drawRep, or -1 (move limit).
    """
    bot1.setupPieces()
    bot2.setupPieces()

    white_bot   = bot1  if bot1_plays_white else bot2
    black_bot   = bot2  if bot1_plays_white else bot1
    white_label = "bot1" if bot1_plays_white else "bot2"
    black_label = "bot2" if bot1_plays_white else "bot1"

    log.info(f"\n--- GAME {game_num:02d}: {white_label}=WHITE  {black_label}=BLACK ---")

    bot1_depths: List[int] = []
    bot2_depths: List[int] = []
    bot1_nodes:  List[int] = []
    bot2_nodes:  List[int] = []

    half_move = 0
    result_code = -1   # -1 = move-limit draw

    while half_move < MAX_MOVES_PER_GAME:
        # ------------------------------------------------------------------
        # White's move
        # ------------------------------------------------------------------
        t0 = time.time()
        move, depth, avg_t, evaluation = white_bot.botMove(
            depthLimit=99, timeLimit=time_limit
        )
        elapsed = time.time() - t0

        # Accumulate depth/node stats for the bot that just moved
        if white_label == "bot1":
            bot1_depths.append(depth)
            bot1_nodes.append(white_bot.i)
        else:
            bot2_depths.append(depth)
            bot2_nodes.append(white_bot.i)

        half_move += 1

        if move is None:
            # White is checkmated or stalemated (getLegalMoves returned empty)
            if white_bot._kingChecked(white_bot.whitesMove):
                result_code = blackWin
            else:
                result_code = staleMate
            log.info(
                f"[G{game_num:02d} M{half_move:03d} W/{white_label}] "
                f"No legal moves -> {_result_label(result_code, white_label, black_label)}"
            )
            break

        log_move(log, game_num, half_move, "W", white_label,
                 move, depth, white_bot.i, white_bot.prunings, elapsed, evaluation)

        # Apply white's move to the black bot's board state
        gs = black_bot.makeMove(move, frfr=True)
        if gs in (staleMate, drawRep, blackWin, whiteWin):
            result_code = gs
            log.info(
                f"[G{game_num:02d}] After W move: "
                f"{_result_label(result_code, white_label, black_label)}"
            )
            break

        # ------------------------------------------------------------------
        # Black's move
        # ------------------------------------------------------------------
        t0 = time.time()
        move, depth, avg_t, evaluation = black_bot.botMove(
            depthLimit=99, timeLimit=time_limit
        )
        elapsed = time.time() - t0

        if black_label == "bot1":
            bot1_depths.append(depth)
            bot1_nodes.append(black_bot.i)
        else:
            bot2_depths.append(depth)
            bot2_nodes.append(black_bot.i)

        half_move += 1

        if move is None:
            if black_bot._kingChecked(black_bot.whitesMove):
                result_code = whiteWin
            else:
                result_code = staleMate
            log.info(
                f"[G{game_num:02d} M{half_move:03d} B/{black_label}] "
                f"No legal moves -> {_result_label(result_code, white_label, black_label)}"
            )
            break

        log_move(log, game_num, half_move, "B", black_label,
                 move, depth, black_bot.i, black_bot.prunings, elapsed, evaluation)

        # Apply black's move to the white bot's board state
        gs = white_bot.makeMove(move, frfr=True)
        if gs in (staleMate, drawRep, blackWin, whiteWin):
            result_code = gs
            log.info(
                f"[G{game_num:02d}] After B move: "
                f"{_result_label(result_code, white_label, black_label)}"
            )
            break

        # Sanity check: both bots must agree on the position
        if white_bot.getPosition() != black_bot.getPosition():
            log.warning(
                f"[G{game_num:02d}] POSITION MISMATCH after half-move {half_move} — "
                "state desync! Aborting game as draw."
            )
            result_code = -1
            break

    if result_code == -1:
        log.info(f"[G{game_num:02d}] Move limit ({MAX_MOVES_PER_GAME}) reached -> DRAW")

    # Compute the game winner from the perspective of bot1/bot2 (not color)
    result_str = _result_label(result_code, white_label, black_label)
    avg_d_white = round(
        sum(bot1_depths if bot1_plays_white else bot2_depths) /
        max(1, len(bot1_depths if bot1_plays_white else bot2_depths)), 1
    )
    avg_d_black = round(
        sum(bot2_depths if bot1_plays_white else bot1_depths) /
        max(1, len(bot2_depths if bot1_plays_white else bot1_depths)), 1
    )
    log.info(
        f"=== GAME {game_num:02d} RESULT: {result_str} | "
        f"half_moves={half_move} | "
        f"W({white_label}) avg_depth={avg_d_white} | "
        f"B({black_label}) avg_depth={avg_d_black} ==="
    )

    return (
        result_code,
        half_move,
        bot1_depths, bot2_depths,
        bot1_nodes,  bot2_nodes,
        white_label, black_label,
    )


# ---------------------------------------------------------------------------
# Session runner
# ---------------------------------------------------------------------------

def run_session(n_games: int, time_limit: float) -> None:
    """Run a full benchmark session of n_games games."""
    log, log_path = setup_logger()
    log.info(
        f"=== Benchmark started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==="
    )
    log.info(f"Games: {n_games}  |  Time limit per move: {time_limit}s  |  Log: {log_path}")
    log.info(f"Max half-moves per game: {MAX_MOVES_PER_GAME}")
    log.info("")

    bot1 = chessBoard1()
    bot2 = chessBoard2()

    # Session accumulators
    bot1_wins  = 0
    bot2_wins  = 0
    draws      = 0

    # Color-split win counters
    bot1_wins_as_white = 0
    bot1_wins_as_black = 0
    bot2_wins_as_white = 0
    bot2_wins_as_black = 0

    all_bot1_depths: List[int] = []
    all_bot2_depths: List[int] = []
    all_bot1_nodes:  List[int] = []
    all_bot2_nodes:  List[int] = []
    all_game_lengths: List[int] = []

    game_results = []   # list of (result_code, white_label, black_label)

    for game_num in range(1, n_games + 1):
        bot1_plays_white = (game_num % 2 == 1)

        (
            result_code,
            half_moves,
            b1_depths, b2_depths,
            b1_nodes,  b2_nodes,
            white_label, black_label,
        ) = run_game(
            game_num=game_num,
            bot1=bot1,
            bot2=bot2,
            bot1_plays_white=bot1_plays_white,
            time_limit=time_limit,
            log=log,
        )

        all_bot1_depths.extend(b1_depths)
        all_bot2_depths.extend(b2_depths)
        all_bot1_nodes.extend(b1_nodes)
        all_bot2_nodes.extend(b2_nodes)
        all_game_lengths.append(half_moves)
        game_results.append((result_code, white_label, black_label))

        # Tally wins
        if result_code == whiteWin:
            if white_label == "bot1":
                bot1_wins += 1
                bot1_wins_as_white += 1
            else:
                bot2_wins += 1
                bot2_wins_as_white += 1
        elif result_code == blackWin:
            if black_label == "bot1":
                bot1_wins += 1
                bot1_wins_as_black += 1
            else:
                bot2_wins += 1
                bot2_wins_as_black += 1
        else:
            draws += 1

    # ------------------------------------------------------------------
    # Session summary
    # ------------------------------------------------------------------
    total = bot1_wins + bot2_wins + draws
    b1_pct = 100 * bot1_wins / total if total else 0
    b2_pct = 100 * bot2_wins / total if total else 0
    d_pct  = 100 * draws      / total if total else 0

    b1_avg_d = round(sum(all_bot1_depths) / max(1, len(all_bot1_depths)), 2)
    b2_avg_d = round(sum(all_bot2_depths) / max(1, len(all_bot2_depths)), 2)
    b1_avg_n = int(sum(all_bot1_nodes)    / max(1, len(all_bot1_nodes)))
    b2_avg_n = int(sum(all_bot2_nodes)    / max(1, len(all_bot2_nodes)))
    avg_game_len = round(sum(all_game_lengths) / max(1, len(all_game_lengths)), 1)

    log.info("")
    log.info("=" * 70)
    log.info("SESSION SUMMARY")
    log.info("=" * 70)
    log.info(f"  Total games played : {total}")
    log.info(f"  Bot1 wins          : {bot1_wins:3d}  ({b1_pct:.1f}%)")
    log.info(f"  Bot2 wins          : {bot2_wins:3d}  ({b2_pct:.1f}%)")
    log.info(f"  Draws              : {draws:3d}  ({d_pct:.1f}%)")
    log.info("")
    log.info("  Color breakdown:")
    log.info(f"    Bot1 wins as White: {bot1_wins_as_white}")
    log.info(f"    Bot1 wins as Black: {bot1_wins_as_black}")
    log.info(f"    Bot2 wins as White: {bot2_wins_as_white}")
    log.info(f"    Bot2 wins as Black: {bot2_wins_as_black}")
    log.info("")
    log.info("  Search statistics (averaged over all moves in session):")
    log.info(f"    Bot1 avg search depth   : {b1_avg_d}")
    log.info(f"    Bot2 avg search depth   : {b2_avg_d}")
    log.info(f"    Bot1 avg nodes/move     : {b1_avg_n}")
    log.info(f"    Bot2 avg nodes/move     : {b2_avg_n}")
    log.info(f"    Avg game length (half-moves): {avg_game_len}")
    log.info("=" * 70)

    # Determine winner
    if bot1_wins > bot2_wins:
        log.info("  VERDICT: Bot1 is stronger in this sample.")
    elif bot2_wins > bot1_wins:
        log.info("  VERDICT: Bot2 is stronger in this sample.")
    else:
        log.info("  VERDICT: Tied — inconclusive with this sample size.")

    # Margin-of-error note (approx 95% CI width for a proportion)
    import math
    p = bot1_wins / total if total else 0.5
    moe = 1.96 * math.sqrt(p * (1 - p) / max(1, total)) * 100
    log.info(f"  95% CI margin of error on win%: ±{moe:.1f} pp  (n={total})")
    log.info("=" * 70)
    log.info(f"\nFull move log written to: {log_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a benchmark match between chessBoard1 (bot1) and chessBoard2 (bot2)."
    )
    parser.add_argument(
        "--games", type=int, default=20,
        help="Number of games to play (default: 20). Use an even number for balanced colors."
    )
    parser.add_argument(
        "--time-limit", type=float, default=0.5,
        help="Seconds allowed per move (default: 0.5)."
    )
    args = parser.parse_args()

    if args.games % 2 != 0:
        print(
            f"WARNING: --games={args.games} is odd. "
            "Bot1 will play one extra game as White. Consider an even number."
        )

    run_session(n_games=args.games, time_limit=args.time_limit)


if __name__ == "__main__":
    main()
