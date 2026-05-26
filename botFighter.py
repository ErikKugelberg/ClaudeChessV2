"""
botFighter.py — Automated benchmark harness for comparing chessBoard1 vs chessBoard2.

Usage:
    python botFighter.py [--games N] [--time-limit T] [--workers W]

    --games      Number of games to play (default: 20, must be even for balanced colors)
    --time-limit Seconds allowed per move (default: 0.5)
    --workers    Parallel worker processes (default: cpu_count; use 1 for sequential mode)

In parallel mode, per-move logs are buffered and written to the log file in game order
after all games finish. Progress is reported as "[N/total games done]" on stdout.
In sequential mode (--workers 1), per-move logs stream to stdout in real time.
"""

import argparse
import io
import logging
import math
import multiprocessing
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from utils import (
    onGoing, drawRep, staleMate, blackWin, whiteWin,
    Move,
)
from bot1 import chessBoard1
from bot2 import chessBoard2

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_MOVES_PER_GAME = 250

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger(log_dir: str = "logs") -> Tuple[logging.Logger, str]:
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"benchmark_{timestamp}.log")

    fmt = logging.Formatter("%(message)s")
    logger = logging.getLogger("benchmark")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger, log_path


# ---------------------------------------------------------------------------
# Formatting helpers
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


def _result_label(result_code: int, white_label: str, black_label: str) -> str:
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
# Single-game runner (used by both sequential and parallel paths)
# ---------------------------------------------------------------------------

def run_game(
    game_num: int,
    bot1: chessBoard1,
    bot2: chessBoard2,
    bot1_plays_white: bool,
    time_limit: float,
) -> tuple:
    """
    Play one complete game. Returns a tuple:
        (game_num, result_code, half_moves,
         bot1_depths, bot2_depths, bot1_nodes, bot2_nodes,
         white_label, black_label,
         bot1_blunders, bot2_blunders,
         log_lines)

    log_lines is a List[str] of per-move log messages for this game.
    """
    bot1.setupPieces()
    bot2.setupPieces()

    white_bot   = bot1  if bot1_plays_white else bot2
    black_bot   = bot2  if bot1_plays_white else bot1
    white_label = "bot1" if bot1_plays_white else "bot2"
    black_label = "bot2" if bot1_plays_white else "bot1"

    lines: List[str] = [
        f"\n--- GAME {game_num:02d}: {white_label}=WHITE  {black_label}=BLACK ---"
    ]

    bot1_depths: List[int] = []
    bot2_depths: List[int] = []
    bot1_nodes:  List[int] = []
    bot2_nodes:  List[int] = []

    half_move    = 0
    result_code  = -1
    BLUNDER_CP   = 150
    last_w_eval: Optional[float] = None
    last_b_eval: Optional[float] = None
    white_blunders = 0
    black_blunders = 0

    while half_move < MAX_MOVES_PER_GAME:
        # ------------------------------------------------------------------
        # White's move
        # ------------------------------------------------------------------
        t0 = time.time()
        move, depth, _avg_t, evaluation = white_bot.botMove(
            depthLimit=99, timeLimit=time_limit
        )
        elapsed = time.time() - t0

        if white_label == "bot1":
            bot1_depths.append(depth); bot1_nodes.append(white_bot.i)
        else:
            bot2_depths.append(depth); bot2_nodes.append(white_bot.i)
        half_move += 1

        if move is None:
            result_code = (blackWin if white_bot._kingChecked(white_bot.whitesMove)
                           else staleMate)
            lines.append(
                f"[G{game_num:02d} M{half_move:03d} W/{white_label}] "
                f"No legal moves -> {_result_label(result_code, white_label, black_label)}"
            )
            break

        w_blunder = None
        if last_w_eval is not None:
            delta = evaluation - last_w_eval
            if delta < -BLUNDER_CP:
                w_blunder = round(delta / 100, 2)
                white_blunders += 1
        last_w_eval = evaluation

        blunder_str = f" BLUNDER(d={w_blunder:+.2f})" if w_blunder is not None else ""
        lines.append(
            f"[G{game_num:02d} M{half_move:03d} W/{white_label}] "
            f"depth={depth} nodes={white_bot.i} prunings={white_bot.prunings} "
            f"time={elapsed:.2f}s eval={_eval_str(evaluation)} move={_move_str(move)}{blunder_str}"
        )

        gs = black_bot.makeMove(move, frfr=True)
        if gs in (staleMate, drawRep, blackWin, whiteWin):
            result_code = gs
            lines.append(
                f"[G{game_num:02d}] After W move: "
                f"{_result_label(result_code, white_label, black_label)}"
            )
            break

        # ------------------------------------------------------------------
        # Black's move
        # ------------------------------------------------------------------
        t0 = time.time()
        move, depth, _avg_t, evaluation = black_bot.botMove(
            depthLimit=99, timeLimit=time_limit
        )
        elapsed = time.time() - t0

        if black_label == "bot1":
            bot1_depths.append(depth); bot1_nodes.append(black_bot.i)
        else:
            bot2_depths.append(depth); bot2_nodes.append(black_bot.i)
        half_move += 1

        if move is None:
            result_code = (whiteWin if black_bot._kingChecked(black_bot.whitesMove)
                           else staleMate)
            lines.append(
                f"[G{game_num:02d} M{half_move:03d} B/{black_label}] "
                f"No legal moves -> {_result_label(result_code, white_label, black_label)}"
            )
            break

        b_blunder = None
        if last_b_eval is not None:
            delta = evaluation - last_b_eval
            if delta > BLUNDER_CP:
                b_blunder = round(delta / 100, 2)
                black_blunders += 1
        last_b_eval = evaluation

        blunder_str = f" BLUNDER(d={b_blunder:+.2f})" if b_blunder is not None else ""
        lines.append(
            f"[G{game_num:02d} M{half_move:03d} B/{black_label}] "
            f"depth={depth} nodes={black_bot.i} prunings={black_bot.prunings} "
            f"time={elapsed:.2f}s eval={_eval_str(evaluation)} move={_move_str(move)}{blunder_str}"
        )

        gs = white_bot.makeMove(move, frfr=True)
        if gs in (staleMate, drawRep, blackWin, whiteWin):
            result_code = gs
            lines.append(
                f"[G{game_num:02d}] After B move: "
                f"{_result_label(result_code, white_label, black_label)}"
            )
            break

        if white_bot.getPosition() != black_bot.getPosition():
            lines.append(
                f"[G{game_num:02d}] POSITION MISMATCH after half-move {half_move} — "
                "state desync! Aborting game as draw."
            )
            result_code = -1
            break

    if result_code == -1:
        lines.append(
            f"[G{game_num:02d}] Move limit ({MAX_MOVES_PER_GAME}) reached -> DRAW"
        )

    result_str   = _result_label(result_code, white_label, black_label)
    depths_white = bot1_depths if bot1_plays_white else bot2_depths
    depths_black = bot2_depths if bot1_plays_white else bot1_depths
    avg_d_w = round(sum(depths_white) / max(1, len(depths_white)), 1)
    avg_d_b = round(sum(depths_black) / max(1, len(depths_black)), 1)
    bot1_blunders = white_blunders if bot1_plays_white else black_blunders
    bot2_blunders = black_blunders if bot1_plays_white else white_blunders

    lines.append(
        f"=== GAME {game_num:02d} RESULT: {result_str} | "
        f"half_moves={half_move} | "
        f"W({white_label}) avg_depth={avg_d_w} blunders={white_blunders} | "
        f"B({black_label}) avg_depth={avg_d_b} blunders={black_blunders} ==="
    )

    return (
        game_num,
        result_code,
        half_move,
        bot1_depths, bot2_depths,
        bot1_nodes,  bot2_nodes,
        white_label, black_label,
        bot1_blunders, bot2_blunders,
        lines,
    )


# ---------------------------------------------------------------------------
# Top-level worker for multiprocessing (must be defined at module level)
# ---------------------------------------------------------------------------

def _run_game_worker(args: tuple) -> tuple:
    """Spawn-safe worker: creates its own bot instances and suppresses bot prints."""
    game_num, bot1_plays_white, time_limit = args
    # Suppress the per-move console prints from botMove() to avoid interleaved output
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        b1 = chessBoard1()
        b2 = chessBoard2()
        return run_game(game_num, b1, b2, bot1_plays_white, time_limit)
    finally:
        sys.stdout = old_stdout


# ---------------------------------------------------------------------------
# Session runner
# ---------------------------------------------------------------------------

def run_session(n_games: int, time_limit: float, n_workers: Optional[int] = None) -> None:
    log, log_path = setup_logger()
    log.info(
        f"=== Benchmark started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==="
    )
    log.info(f"Games: {n_games}  |  Time limit per move: {time_limit}s  |  Log: {log_path}")
    log.info(f"Max half-moves per game: {MAX_MOVES_PER_GAME}")
    log.info("")

    if n_workers is None:
        n_workers = min(n_games, os.cpu_count() or 1)
    n_workers = max(1, n_workers)

    args_list = [
        (game_num, game_num % 2 == 1, time_limit)
        for game_num in range(1, n_games + 1)
    ]

    # Session accumulators
    bot1_wins = bot2_wins = draws = 0
    bot1_wins_as_white = bot1_wins_as_black = 0
    bot2_wins_as_white = bot2_wins_as_black = 0
    all_bot1_depths: List[int] = []
    all_bot2_depths: List[int] = []
    all_bot1_nodes:  List[int] = []
    all_bot2_nodes:  List[int] = []
    all_game_lengths: List[int] = []
    total_bot1_blunders = 0
    total_bot2_blunders = 0

    collected: Dict[int, tuple] = {}
    games_done = 0

    if n_workers == 1:
        # Sequential: stream per-move logs in real time
        b1 = chessBoard1()
        b2 = chessBoard2()
        for game_num, bot1_plays_white, tl in args_list:
            result = run_game(game_num, b1, b2, bot1_plays_white, tl)
            for line in result[-1]:
                log.info(line)
            collected[game_num] = result
            games_done += 1
            print(f"[{games_done}/{n_games} games done]", flush=True)
    else:
        # Parallel: buffer per-game logs; write them in order after all games finish
        log.info(f"Running up to {n_workers} games in parallel...")
        with multiprocessing.Pool(processes=n_workers) as pool:
            for result in pool.imap_unordered(_run_game_worker, args_list):
                collected[result[0]] = result
                games_done += 1
                print(f"[{games_done}/{n_games} games done]", flush=True)

        # Write per-game logs to file in game-number order
        for game_num in range(1, n_games + 1):
            for line in collected[game_num][-1]:
                log.info(line)

    # ------------------------------------------------------------------
    # Tally results
    # ------------------------------------------------------------------
    for game_num in range(1, n_games + 1):
        (_, result_code, half_moves,
         b1_depths, b2_depths,
         b1_nodes,  b2_nodes,
         white_label, black_label,
         b1_blunders, b2_blunders,
         _lines) = collected[game_num]

        all_bot1_depths.extend(b1_depths)
        all_bot2_depths.extend(b2_depths)
        all_bot1_nodes.extend(b1_nodes)
        all_bot2_nodes.extend(b2_nodes)
        all_game_lengths.append(half_moves)
        total_bot1_blunders += b1_blunders
        total_bot2_blunders += b2_blunders

        if result_code == whiteWin:
            if white_label == "bot1":
                bot1_wins += 1; bot1_wins_as_white += 1
            else:
                bot2_wins += 1; bot2_wins_as_white += 1
        elif result_code == blackWin:
            if black_label == "bot1":
                bot1_wins += 1; bot1_wins_as_black += 1
            else:
                bot2_wins += 1; bot2_wins_as_black += 1
        else:
            draws += 1

    # ------------------------------------------------------------------
    # Session summary
    # ------------------------------------------------------------------
    total  = bot1_wins + bot2_wins + draws
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
    log.info("")
    log.info("  Blunders (eval drop >150cp vs same side 2 half-moves ago):")
    log.info(f"    Bot1 total blunders     : {total_bot1_blunders}")
    log.info(f"    Bot2 total blunders     : {total_bot2_blunders}")
    log.info(f"    Avg game length (half-moves): {avg_game_len}")
    log.info("=" * 70)

    if bot1_wins > bot2_wins:
        log.info("  VERDICT: Bot1 is stronger in this sample.")
    elif bot2_wins > bot1_wins:
        log.info("  VERDICT: Bot2 is stronger in this sample.")
    else:
        log.info("  VERDICT: Tied — inconclusive with this sample size.")

    p   = bot1_wins / total if total else 0.5
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
    parser.add_argument(
        "--workers", type=int, default=None,
        help="Parallel worker processes (default: cpu_count). Use 1 for sequential mode."
    )
    args = parser.parse_args()

    if args.games % 2 != 0:
        print(
            f"WARNING: --games={args.games} is odd. "
            "Bot1 will play one extra game as White. Consider an even number."
        )

    run_session(n_games=args.games, time_limit=args.time_limit, n_workers=args.workers)


if __name__ == "__main__":
    main()
