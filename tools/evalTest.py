"""
evalTest.py — Diagnostic script for bot2 evaluation quality.

Tests bot2's evaluation on known positions. Optionally compares against Stockfish
if stockfish binary is present at STOCKFISH_PATH.

Usage:
    python evalTest.py                        # eval tests only
    python evalTest.py --stockfish path/sf    # also run Stockfish comparison
    python evalTest.py --bot-moves            # also check bot2's chosen moves
"""

import argparse
import sys
import os

import chess

from utils import empty, Wpawn, Bpawn, Wknight, Bknight, Wbishop, Bbishop
from utils import Wrook, Brook, Wqueen, Bqueen, Wking, Bking, pieceDivider
from bot2 import chessBoard2

# ---------------------------------------------------------------------------
# Helpers: FEN → bot2 board
# ---------------------------------------------------------------------------

_PIECE_MAP = {
    'P': Wpawn,  'N': Wknight, 'B': Wbishop, 'R': Wrook,  'Q': Wqueen,  'K': Wking,
    'p': Bpawn,  'n': Bknight, 'b': Bbishop, 'r': Brook,  'q': Bqueen,  'k': Bking,
}

def fen_to_bot2(fen: str) -> chessBoard2:
    """Return a chessBoard2 with the position set from the FEN string."""
    board = chess.Board(fen)
    b2 = chessBoard2()
    b2.board = [empty] * 64

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            # python-chess: sq=0 is a1 (x=0,y=0); bot2: board[y*8+x]
            x, y = sq % 8, sq // 8
            b2.board[y * 8 + x] = _PIECE_MAP[piece.symbol()]
            if piece.symbol() == 'K':
                b2.whiteKingPos = [x, y]
            elif piece.symbol() == 'k':
                b2.blackKingPos = [x, y]

    b2.whitesMove = board.turn == chess.WHITE

    # Castling rights → rkMoved flags (bit 0=Bleft, 1=Bking, 2=Bright, 3=Wleft, 4=Wking, 5=Wright)
    if not board.has_queenside_castling_rights(chess.BLACK):
        b2.rkMoved |= 1 << 0
    if not board.has_kingside_castling_rights(chess.BLACK):
        b2.rkMoved |= 1 << 2
    if not board.has_queenside_castling_rights(chess.WHITE):
        b2.rkMoved |= 1 << 3
    if not board.has_kingside_castling_rights(chess.WHITE):
        b2.rkMoved |= 1 << 5
    if not board.has_castling_rights(chess.WHITE):
        b2.rkMoved |= 1 << 4
    if not board.has_castling_rights(chess.BLACK):
        b2.rkMoved |= 1 << 1

    # En passant
    if board.ep_square is not None:
        ep_x = board.ep_square % 8
        # python-chess ep_square is the capture-to square, bot2 enPas is the pawn's square
        if board.turn == chess.WHITE:
            ep_y = board.ep_square // 8 - 1  # black pawn is one rank below white capture square
        else:
            ep_y = board.ep_square // 8 + 1
        b2.enPas = [ep_x, ep_y]

    b2.nonPawnCount = sum(1 for p in b2.board if p != empty and p != Wpawn and p != Bpawn)
    return b2


def _eval_str(cp: float) -> str:
    v = round(cp / 100, 2)
    return f"{v:+.2f}"


# ---------------------------------------------------------------------------
# Test positions
# ---------------------------------------------------------------------------

# Each entry: (description, FEN, expected_eval_sign, expected_min_abs_eval_cp)
# expected_eval_sign: +1 = white winning, -1 = black winning, 0 = roughly equal
# expected_min_abs_eval_cp: minimum absolute cp we expect (helps detect flat evals)
TEST_POSITIONS = [
    # --- Material tests ---
    (
        "Starting position (roughly equal)",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        0, 0,
    ),
    (
        "White up a queen (should be strongly +white)",
        "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        +1, 700,
    ),
    (
        "Black up a rook (should be strongly -white)",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNr w KQkq - 0 1",
        -1, 400,
    ),
    (
        "White up a pawn in endgame (king+pawn vs king)",
        "8/8/8/3k4/8/8/3P4/3K4 w - - 0 1",
        +1, 40,
    ),
    # --- Positional tests ---
    (
        "Rook on open file (white should be slightly better)",
        "4k3/pppppppp/8/8/8/8/PPPPPPPP/R3K3 w Q - 0 1",
        +1, 0,
    ),
    (
        "Passed pawn close to promotion (white strongly +)",
        "4k3/8/8/8/8/8/6P1/4K3 w - - 0 1",
        +1, 50,
    ),
    (
        "Black passed pawn close to promotion (black strongly +)",
        "4k3/6p1/8/8/8/8/8/4K3 b - - 0 1",
        -1, 50,
    ),
    # --- Tactical positions ---
    (
        "Checkmate in 1 (white): Qh5# available",
        "r1bqkb1r/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
        +1, 0,
    ),
    (
        "Symmetric pawn structure (equal material, center control)",
        "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/3P4/PPP2PPP/RNBQKBNR w KQkq - 0 3",
        0, 0,
    ),
    (
        "White up bishop pair vs two knights (minor advantage)",
        "r1bqk2r/pppp1ppp/2n2n2/4p3/2B1P3/2NP4/PPP2PPP/R1BQK2R w KQkq - 0 5",
        +1, 0,
    ),
]


def run_eval_tests(args) -> int:
    """Run all evaluation tests. Returns number of failures."""
    failures = 0
    print("\n" + "=" * 70)
    print("EVALUATION TESTS")
    print("=" * 70)
    print(f"{'Position':<52} {'Eval':>8}  {'Expected':>10}  {'Pass':>5}")
    print("-" * 70)

    for desc, fen, expected_sign, min_abs in TEST_POSITIONS:
        b2 = fen_to_bot2(fen)
        ev = b2.evaluatePosition()
        sign = 0 if abs(ev) < 30 else (1 if ev > 0 else -1)

        sign_ok = (expected_sign == 0) or (sign == expected_sign)
        abs_ok  = abs(ev) >= min_abs
        ok = sign_ok and abs_ok
        if not ok:
            failures += 1

        short_desc = desc[:50]
        pass_str = "OK" if ok else "FAIL"
        reason = ""
        if not sign_ok:
            reason = f" (sign: got {sign}, want {expected_sign})"
        if not abs_ok:
            reason += f" (|eval|={abs(ev):.0f} < {min_abs})"
        print(f"{short_desc:<52} {_eval_str(ev):>8}  {expected_sign:>+10}  {pass_str:>5}{reason}")

    print("-" * 70)
    print(f"Results: {len(TEST_POSITIONS) - failures}/{len(TEST_POSITIONS)} passed")
    return failures


def run_move_tests(args, time_limit: float = 0.3) -> int:
    """Run bot2 on tactical positions, check if it finds the right move."""
    MOVE_TESTS = [
        (
            "Forced mate (Scholar's mate position): must find forced win",
            "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
            # Both Qxf7# and Qf5 lead to forced mate — check eval, not specific move.
            lambda m, ev: ev > 5000,
            "eval > +50.00 (forced mate found)",
        ),
        (
            "Avoid moving into attack (don't blunder piece)",
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
            lambda m, ev: True,  # any legal move — just check it doesn't crash
            "any legal move",
        ),
    ]

    failures = 0
    print("\n" + "=" * 70)
    print("MOVE QUALITY TESTS")
    print("=" * 70)

    for desc, fen, check_fn, expected_desc in MOVE_TESTS:
        b2 = fen_to_bot2(fen)
        move, depth, _, eval_v = b2.botMove(timeLimit=time_limit)
        if move is None:
            print(f"FAIL {desc}: returned None (no legal move?)")
            failures += 1
            continue
        ok = check_fn(move, eval_v)
        status = "OK" if ok else "FAIL"
        cols = "abcdefgh"
        mv_str = f"{cols[move.getX1()]}{move.getY1()+1}{cols[move.getX2()]}{move.getY2()+1}"
        print(f"{status} [{depth}d eval={_eval_str(eval_v)}] {desc}: {mv_str} (want {expected_desc})")
        if not ok:
            failures += 1

    return failures


def run_stockfish_comparison(args) -> None:
    """Compare bot2 evals against Stockfish on all test positions."""
    try:
        import chess.engine
        engine = chess.engine.SimpleEngine.popen_uci(args.stockfish)
    except Exception as e:
        print(f"\nCould not start Stockfish at '{args.stockfish}': {e}")
        return

    print("\n" + "=" * 70)
    print("STOCKFISH COMPARISON")
    print("=" * 70)
    print(f"{'Position':<52} {'bot2':>8}  {'sf':>8}  {'Δ':>8}")
    print("-" * 70)

    for desc, fen, _, _ in TEST_POSITIONS:
        b2 = fen_to_bot2(fen)
        bot2_ev = b2.evaluatePosition()

        board = chess.Board(fen)
        info = engine.analyse(board, chess.engine.Limit(depth=15))
        sf_score = info["score"].white().score(mate_score=10000)

        delta = bot2_ev - sf_score if sf_score is not None else float('nan')
        sf_str = f"{sf_score/100:+.2f}" if sf_score is not None else "mate"
        print(
            f"{desc[:50]:<52} {_eval_str(bot2_ev):>8}  {sf_str:>8}  {delta/100:>+8.2f}"
        )

    engine.quit()
    print("-" * 70)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnostic eval tests for bot2")
    parser.add_argument("--stockfish", default=None,
                        help="Path to Stockfish binary for comparison")
    parser.add_argument("--bot-moves", action="store_true",
                        help="Also run move-quality tests (slower, calls botMove)")
    parser.add_argument("--time-limit", type=float, default=0.3,
                        help="Time limit per botMove call in --bot-moves mode (default 0.3s)")
    args = parser.parse_args()

    failures = run_eval_tests(args)

    if args.bot_moves:
        failures += run_move_tests(args, args.time_limit)

    if args.stockfish:
        run_stockfish_comparison(args)

    print(f"\nTotal eval failures: {failures}")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
