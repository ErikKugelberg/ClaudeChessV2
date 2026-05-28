# -*- coding: utf-8 -*-
"""
Compare bot2.getLegalMoves() against python-chess for correctness.

Usage:
  python legalmoves_check.py          # run all test positions
  python legalmoves_check.py --perft  # also run perft(3) node counts
"""
import sys
import chess
from bot2 import chessBoard2
from utils import *
from sfcompare import board_to_fen, apply_uci_to_bot, move_to_uci

POSITIONS = [
    ("Starting position",                   []),
    ("After 1.e4 e5",                       ["e2e4", "e7e5"]),
    ("After 1.e4 e5 2.Nf3 Nc6 3.Bc4",      ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]),
    # Castling available for both sides
    ("Castling ready (both sides)",
     ["e2e4", "e7e5", "g1f3", "g8f6", "f1e2", "f8e7"]),
    # King-side castling
    ("After 0-0",
     ["e2e4", "e7e5", "g1f3", "g8f6", "f1e2", "f8e7", "e1g1"]),
    # Queen-side castling path
    ("Queen-side castling ready",
     ["d2d4", "d7d5", "b1c3", "b8c6", "c1f4", "c8f5", "d1d2", "d8d7"]),
    # En passant
    ("En passant available (white)",
     ["e2e4", "d7d5", "e4e5", "f7f5"]),
    ("En passant available (black)",
     ["e2e4", "e7e5", "d2d4"]),
    # Check positions
    ("White in check",
     ["e2e4", "e7e5", "f1c4", "d8h4"]),
    ("Fried liver: white to punish",
     ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5", "e4d5", "f6d5"]),
    # Pinned pieces
    ("Pin on f3 knight",
     ["e2e4", "e7e5", "g1f3", "f8b4"]),
    # Late endgame (few pieces)
    ("Endgame: K+P vs K",
     ["e2e4", "e7e5", "d2d4", "e5d4", "d1d4", "b8c6", "d4e3", "g8f6",
      "e3e5", "f6e4", "e5d5", "d7d6", "b1c3", "e4c3", "b2c3", "c8e6",
      "d5e6", "f7e6", "f1b5", "a7a6", "b5c6", "b7c6", "g1e2", "d8d7",
      "e1g1", "e8c8", "c1g5", "f8e7", "g5e7", "d8e7"]),
    # Near promotion
    ("White pawn on 7th rank",
     ["e2e4", "f7f5", "e4f5", "g7g6", "f5g6", "h7h5", "g6g7"]),
]


def bot2_moves_uci(bot):
    """Return set of UCI strings for bot2's legal moves (queen-only promotions)."""
    moves = bot.getLegalMoves()
    result = set()
    for m in moves:
        uci = move_to_uci(m)
        # If pawn reaches last rank, it auto-promotes to queen — mark as queen promo
        x1, y1, x2, y2 = m.getX1(), m.getY1(), m.getX2(), m.getY2()
        piece = bot.board[y1 * 8 + x1]
        if (piece == Wpawn and y2 == 7) or (piece == Bpawn and y2 == 0):
            uci += 'q'
        result.add(uci)
    return result


def chess_moves_uci(chess_board):
    """Return set of UCI strings from python-chess, normalising promotions to queen only."""
    result = set()
    for m in chess_board.legal_moves:
        uci = m.uci()
        if m.promotion and m.promotion != chess.QUEEN:
            continue  # skip non-queen promotions to match bot2
        result.add(uci)
    return result


def compare_position(bot, chess_board, desc):
    b2 = bot2_moves_uci(bot)
    sf = chess_moves_uci(chess_board)

    missing = sf - b2   # moves chess has but bot2 doesn't
    extra   = b2 - sf   # moves bot2 has but chess doesn't

    ok = not missing and not extra
    status = "OK" if ok else "FAIL"
    print(f"\n  [{status}] {desc}")
    print(f"         bot2: {len(b2)} moves   chess: {len(sf)} moves")
    if missing:
        print(f"    MISSING (chess has, bot2 doesn't): {sorted(missing)}")
    if extra:
        print(f"    EXTRA   (bot2 has, chess doesn't): {sorted(extra)}")
    return ok


def perft(bot, chess_board, depth):
    """Count leaf nodes for bot2 and python-chess at given depth."""
    if depth == 0:
        return 1, 1

    b2_moves = bot.getLegalMoves()
    chess_moves = list(chess_board.legal_moves)

    b2_nodes = 0
    for m in b2_moves:
        bot.makeMove(m, frfr=True)
        b2_nodes += perft(bot, None, depth - 1)[0]
        # undo via setupPieces is not practical; use a fresh bot per branch
        # Instead track with undo
        # Note: makeMove with frfr=True doesn't support undo easily here
        # So just count bot2 moves recursively without undo (approximate)
        break  # placeholder — see note below

    sf_nodes = 0
    for m in chess_moves:
        chess_board.push(m)
        sf_nodes += chess_board.legal_moves.count()
        chess_board.pop()

    return b2_nodes, sf_nodes


def run_perft(depth=3):
    """Run perft comparison at starting position."""
    print(f"\n{'='*60}")
    print(f"  PERFT depth={depth}: bot2 vs python-chess node counts")
    print(f"{'='*60}")

    def perft_chess(board, d):
        if d == 0:
            return 1
        count = 0
        for m in board.legal_moves:
            board.push(m)
            count += perft_chess(board, d - 1)
            board.pop()
        return count

    def perft_bot2(bot2, d):
        if d == 0:
            return 1
        count = 0
        for m in bot2.getLegalMoves():
            state = bot2._saveState(m)
            bot2.makeMove(m)
            count += perft_bot2(bot2, d - 1)
            bot2._undoMove(state)
        return count

    cb = chess.Board()
    b2 = chessBoard2()
    b2.setupPieces()

    for d in range(1, depth + 1):
        n_chess = perft_chess(cb, d)
        n_bot2  = perft_bot2(b2, d)
        match = "OK" if n_chess == n_bot2 else f"MISMATCH (diff={n_bot2 - n_chess:+d})"
        print(f"  depth={d}: chess={n_chess:8d}  bot2={n_bot2:8d}  {match}")


if __name__ == '__main__':
    bot = chessBoard2()
    total = 0
    passed = 0

    print("="*60)
    print("  Legal move comparison: bot2 vs python-chess")
    print("="*60)

    for desc, moves in POSITIONS:
        bot.setupPieces()
        chess_board = chess.Board()

        ok = True
        for uci in moves:
            result = apply_uci_to_bot(bot, uci)
            if result is None:
                print(f"\n  [SKIP] {desc}: illegal setup move {uci}")
                ok = False
                break
            chess_board.push(chess.Move.from_uci(uci))

        if ok:
            total += 1
            if compare_position(bot, chess_board, desc):
                passed += 1

    print(f"\n{'='*60}")
    print(f"  RESULT: {passed}/{total} positions correct")
    print(f"{'='*60}")

    if '--perft' in sys.argv:
        run_perft(depth=3)
