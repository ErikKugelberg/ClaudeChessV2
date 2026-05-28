# -*- coding: utf-8 -*-
"""
Compare bot2 move choices to Stockfish at depth 5.

Usage:
  python sfcompare.py           # run all preset positions
  python sfcompare.py --game    # play a full game bot2(white) vs Stockfish(black)
  python sfcompare.py --game2   # play a full game Stockfish(white) vs bot2(black)
"""
import sys
import time
import chess
import chess.engine

sys.path.insert(0, '.')
from bot2 import chessBoard2
from utils import *

STOCKFISH_PATH = './stockfish.exe'
SF_DEPTH = 5

PIECE_TO_FEN = {
    Wpawn: 'P', Wbishop: 'B', Wknight: 'N', Wrook: 'R', Wqueen: 'Q', Wking: 'K',
    Bpawn: 'p', Bbishop: 'b', Bknight: 'n', Brook: 'r', Bqueen: 'q', Bking: 'k',
}
PIECE_CHARS = {
    0: '.', 1: 'P', 2: 'B', 3: 'N', 4: 'R', 5: 'Q', 6: 'K',
    8: 'p', 9: 'b', 10: 'n', 11: 'r', 12: 'q', 13: 'k'
}


def board_to_fen(bot):
    rows = []
    for y in range(7, -1, -1):
        empty_count = 0
        row = ''
        for x in range(8):
            piece = bot.board[y*8 + x]
            if piece == 0:
                empty_count += 1
            else:
                if empty_count:
                    row += str(empty_count)
                    empty_count = 0
                row += PIECE_TO_FEN.get(piece, '?')
        if empty_count:
            row += str(empty_count)
        rows.append(row)

    side = 'w' if bot.whitesMove else 'b'

    castling = ''
    if not (bot.rkMoved & (1 << 4)):
        if not (bot.rkMoved & (1 << 5)):
            castling += 'K'
        if not (bot.rkMoved & (1 << 3)):
            castling += 'Q'
    if not (bot.rkMoved & (1 << 1)):
        if not (bot.rkMoved & (1 << 2)):
            castling += 'k'
        if not (bot.rkMoved & (1 << 0)):
            castling += 'q'
    if not castling:
        castling = '-'

    if bot.enPas[0] != -1:
        ep_file = chr(ord('a') + bot.enPas[0])
        # whitesMove: black just pushed, pawn at enPas[1], target one rank higher
        ep_rank = (bot.enPas[1] + 2) if bot.whitesMove else bot.enPas[1]
        ep = ep_file + str(ep_rank)
    else:
        ep = '-'

    return f"{'/'.join(rows)} {side} {castling} {ep} 0 1"


def move_to_uci(move):
    files = 'abcdefgh'
    return f"{files[move.getX1()]}{move.getY1()+1}{files[move.getX2()]}{move.getY2()+1}"


def apply_uci_to_bot(bot, uci):
    """Find and apply a UCI move to bot2. Returns the Move object or None."""
    x1 = ord(uci[0]) - ord('a')
    y1 = int(uci[1]) - 1
    x2 = ord(uci[2]) - ord('a')
    y2 = int(uci[3]) - 1
    for m in bot.getLegalMoves():
        if m.getX1() == x1 and m.getY1() == y1 and m.getX2() == x2 and m.getY2() == y2:
            bot.makeMove(m, frfr=True)
            return m
    return None


def setup_position(bot, move_seq):
    """Reset bot to start and replay move_seq (list of UCI strings)."""
    bot.setupPieces()
    for uci in move_seq:
        result = apply_uci_to_bot(bot, uci)
        if result is None:
            print(f"  ERROR: illegal move {uci}")
            return False
    return True


def get_bot2_move(bot, depth):
    """Get bot2's best move at given depth without applying it to the board."""
    bot._stop_search = False
    bot.i = 0
    bot.prunings = 0
    bot._history = [[0]*64 for _ in range(64)]
    bot._killers = [[None, None] for _ in range(128)]
    bot._ttable = LimitedSizeDict(max_size=100_000)  # clear TT to avoid cross-position pollution
    start = time.time()
    moves = bot.getLegalMoves()
    best_move, best_eval = None, -float('inf')
    for d in range(2, depth + 1):
        best_move, best_eval, moves = bot.findBestMove(
            depthLimit=d, timeLimit=9999, startTime=start, moves=moves)
    # Normalize to white-positive convention
    white_eval = best_eval if bot.whitesMove else -best_eval
    return best_move, white_eval, bot.i


def score_all_moves(bot, depth):
    """Score every legal move at the given depth and return sorted list of (uci, score)."""
    bot._stop_search = False
    bot._history = [[0]*64 for _ in range(64)]
    bot._killers = [[None, None] for _ in range(128)]
    start = time.time()
    moves = bot.getLegalMoves()
    results = []
    alpha = -float('inf')
    beta = float('inf')
    for move in moves:
        rec = bot._saveState(move)
        bot.makeMove(move)
        score = -bot._recFindBestEval(depth, -beta, -alpha,
                                       timeLimit=9999, startTime=start)
        bot._undoMove(rec)
        white_score = score if bot.whitesMove else -score
        results.append((move_to_uci(move), white_score))
    results.sort(key=lambda x: -x[1])
    return results


def trace_botmove(bot, time_limit=0.5):
    """Simulate botMove (full window, per-iteration TT clear), printing per-depth result.
    Does NOT apply the move. Use to diagnose why botMove picks a certain move."""
    bot._stop_search = False
    bot.i = 0
    bot.prunings = 0
    bot._history = [[0]*64 for _ in range(64)]
    bot._killers = [[None, None] for _ in range(128)]
    bot._ttable = LimitedSizeDict(max_size=100_000)

    start = time.time()
    d = 2
    prevMove = None
    prevEval = -float('inf')
    moves = bot.getLegalMoves()

    print(f"\n  --- trace_botmove (time_limit={time_limit}s, "
          f"{'White' if bot.whitesMove else 'Black'} to move) ---")

    while True:
        bot._ttable = LimitedSizeDict(max_size=100_000)
        move, evaluation, moves = bot.findBestMove(
            depthLimit=d, timeLimit=time_limit, startTime=start, moves=moves)
        interrupted = bot._stop_search

        white_eval = evaluation if bot.whitesMove else -evaluation
        uci = move_to_uci(move) if move else 'none'
        elapsed = time.time() - start
        status = 'INTERRUPTED' if interrupted else 'complete'
        print(f"    d={d:2d}: {uci}  eval={white_eval/100:+.2f}  t={elapsed:.3f}s  [{status}]")

        d += 1
        if (time.time() - start) > time_limit:
            if interrupted and prevMove is not None:
                final_uci = move_to_uci(prevMove)
                final_eval = prevEval if bot.whitesMove else -prevEval
                print(f"  --> Final (last complete depth): {final_uci}  eval={final_eval/100:+.2f}")
            else:
                final_uci = uci
                final_eval = white_eval
                print(f"  --> Final (interrupted, no fallback): {final_uci}  eval={final_eval/100:+.2f}")
            break
        prevMove, prevEval = move, evaluation
        if d > 20:
            final_uci = uci
            final_eval = white_eval
            print(f"  --> Final (depth limit reached): {final_uci}  eval={final_eval/100:+.2f}")
            break

    return prevMove


def sf_analyse(sf, fen, depth):
    """Return (best_uci, score_cp_white_positive) from Stockfish."""
    board = chess.Board(fen)
    info = sf.analyse(board, chess.engine.Limit(depth=depth))
    pv = info.get('pv', [])
    best = str(pv[0]) if pv else None
    score = info.get('score')
    if score:
        cp = score.white().score(mate_score=100000)
    else:
        cp = None
    return best, cp


def sf_eval_move(sf, fen, uci, depth):
    """Evaluate a specific move using Stockfish: apply the move and return the resulting eval."""
    board = chess.Board(fen)
    board.push(chess.Move.from_uci(uci))
    info = sf.analyse(board, chess.engine.Limit(depth=depth))
    score = info.get('score')
    if score:
        cp = score.white().score(mate_score=100000)
    else:
        cp = None
    return cp


def print_board(bot):
    for y in range(7, -1, -1):
        row = f"  {y+1} "
        for x in range(8):
            row += PIECE_CHARS.get(bot.board[y*8+x], '?') + ' '
        print(row)
    print("    a b c d e f g h")


def compare_position(sf, bot, move_seq, description):
    if not setup_position(bot, move_seq):
        return

    print(f"\n{'='*62}")
    print(f"  {description}")
    print(f"  To move: {'White' if bot.whitesMove else 'Black'}")
    print(f"{'='*62}")
    print_board(bot)
    fen = board_to_fen(bot)
    print(f"  FEN: {fen}")

    # Bot2 analysis
    b2_move, b2_eval_cp, b2_nodes = get_bot2_move(bot, SF_DEPTH)
    b2_uci = move_to_uci(b2_move) if b2_move else 'none'

    # Stockfish analysis
    sf_move, sf_eval_cp = sf_analyse(sf, fen, SF_DEPTH)

    # Format evals as pawn units
    def fmt(cp): return f"{cp/100:+.2f}" if cp is not None else "N/A"

    agree = (sf_move == b2_uci)

    print(f"\n  Bot2 (depth {SF_DEPTH}, {b2_nodes} nodes): {b2_uci:6s}  eval {fmt(b2_eval_cp)}")
    print(f"  Stockfish (depth {SF_DEPTH})         : {sf_move or 'none':6s}  eval {fmt(sf_eval_cp)}")
    print(f"  Agreement: {'YES [OK]' if agree else 'NO  [!!]'}")

    if not agree and sf_move and b2_move:
        sf_sees_b2  = sf_eval_move(sf, fen, b2_uci, SF_DEPTH)
        sf_sees_sf  = sf_eval_move(sf, fen, sf_move, SF_DEPTH)
        loss = None
        if sf_sees_sf is not None and sf_sees_b2 is not None:
            # from current side's perspective
            mult = 1 if bot.whitesMove else -1
            loss = mult * (sf_sees_sf - sf_sees_b2)
        print(f"  Stockfish eval of bot2 move : {fmt(sf_sees_b2)}")
        print(f"  Stockfish eval of SF move   : {fmt(sf_sees_sf)}")
        if loss is not None:
            marker = "  <-- BLUNDER" if loss > 150 else ("  <-- mistake" if loss > 50 else "")
            print(f"  Quality loss for bot2       : {loss/100:+.2f} pawns{marker}")

    return {
        'desc': description,
        'fen': fen,
        'b2': b2_uci,
        'sf': sf_move,
        'b2_eval': b2_eval_cp,
        'sf_eval': sf_eval_cp,
        'agree': agree,
    }


def run_game(sf, bot2_is_white=True, max_moves=60):
    """Play a full game: bot2 vs Stockfish, printing move comparisons."""
    print(f"\n{'#'*62}")
    bot_side = 'WHITE' if bot2_is_white else 'BLACK'
    print(f"  GAME: bot2={bot_side} vs Stockfish={'BLACK' if bot2_is_white else 'WHITE'}")
    print(f"{'#'*62}")

    bot = chessBoard2()
    bot.setupPieces()
    chess_board = chess.Board()
    move_num = 0
    disagreements = []

    while move_num < max_moves * 2:
        if chess_board.is_game_over():
            break

        bot2_to_move = (bot.whitesMove == bot2_is_white)
        move_num += 1
        side_str = 'W' if bot.whitesMove else 'B'
        move_label = f"M{move_num:03d} {side_str}"

        fen = board_to_fen(bot)

        if bot2_to_move:
            # Bot2 picks the move
            b2_move, b2_eval_cp, b2_nodes = get_bot2_move(bot, SF_DEPTH)
            if b2_move is None:
                print(f"  [{move_label}] Bot2 has no legal moves")
                break
            b2_uci = move_to_uci(b2_move)

            # Stockfish recommendation at same position
            sf_move, sf_eval_cp = sf_analyse(sf, fen, SF_DEPTH)

            agree = (sf_move == b2_uci)
            quality_loss = None
            if not agree and sf_move:
                sf_sees_b2 = sf_eval_move(sf, fen, b2_uci, SF_DEPTH)
                sf_sees_sf = sf_eval_move(sf, fen, sf_move, SF_DEPTH)
                if sf_sees_sf is not None and sf_sees_b2 is not None:
                    mult = 1 if bot.whitesMove else -1
                    quality_loss = mult * (sf_sees_sf - sf_sees_b2)

            marker = ''
            if quality_loss is not None and quality_loss > 150:
                marker = '  *** BLUNDER'
            elif quality_loss is not None and quality_loss > 50:
                marker = '  * mistake'

            def fmt(cp): return f"{cp/100:+.2f}" if cp is not None else "N/A"
            agree_str = 'OK' if agree else '!!'
            print(f"  [{move_label}] Bot2: {b2_uci}  SF: {sf_move or 'none'}  {agree_str}"
                  f"  loss={fmt(quality_loss)}{marker}")

            if not agree and quality_loss is not None and quality_loss > 50:
                disagreements.append({
                    'move': move_label, 'b2': b2_uci, 'sf': sf_move,
                    'loss': quality_loss, 'fen': fen
                })

            # Apply bot2's chosen move
            apply_uci_to_bot(bot, b2_uci)
            chess_board.push(chess.Move.from_uci(b2_uci))
        else:
            # Stockfish picks the move
            info = sf.play(chess_board, chess.engine.Limit(depth=SF_DEPTH))
            sf_uci = str(info.move)
            print(f"  [{move_label}] SF plays: {sf_uci}")
            apply_uci_to_bot(bot, sf_uci)
            chess_board.push(info.move)

    result = chess_board.result() if chess_board.is_game_over() else '*'
    print(f"\n  Game result: {result}")

    if disagreements:
        print(f"\n  Top bot2 mistakes (quality loss > 0.5 pawns):")
        for d in sorted(disagreements, key=lambda x: -x['loss'])[:5]:
            print(f"    {d['move']}: bot2={d['b2']} SF={d['sf']}  loss={d['loss']/100:+.2f}")
            print(f"      FEN: {d['fen']}")


# Preset positions: (description, move sequence from start)
POSITIONS = [
    ("Starting position",
     []),
    ("After 1.e4 e5",
     ["e2e4", "e7e5"]),
    ("After 1.e4 e5 2.Nf3 Nc6 3.Bc4 (Italian)",
     ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]),
    ("Fried liver: ...Nxf7?? (white to punish)",
     ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5", "e4d5", "f6d5"]),
    ("Fork opportunity: Nc6 attacks queen after Bc5",
     ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "b2b4"]),
    ("Queen's gambit after 2...d5 3.Nc3 (white to find best)",
     ["d2d4", "d7d5", "c2c4", "d5c4", "b1c3"]),
    ("Back-rank mate threat",
     ["e2e4", "e7e5", "d2d4", "e5d4", "c2c3", "d4c3", "b1c3", "d7d6",
      "f1c4", "g8f6", "g1f3", "f8e7", "e1g1", "e8g8", "f1e1", "c8g4"]),
    ("Endgame: rook vs 2 pawns",
     ["e2e4", "e7e5", "d2d4", "e5d4", "d1d4", "b8c6", "d4e3", "g8f6",
      "e3e5", "f6e4", "e5d5", "d7d6", "b1c3", "e4c3", "b2c3", "c8e6",
      "d5e6", "f7e6", "f1b5", "a7a6", "b5c6", "b7c6", "g1e2", "d8d7",
      "e1g1", "e8c8", "c1g5", "f8e7", "g5e7", "d8e7"]),
]


if __name__ == '__main__':
    args = sys.argv[1:]
    bot = chessBoard2()

    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as sf:
        if '--game' in args:
            run_game(sf, bot2_is_white=True)
        elif '--game2' in args:
            run_game(sf, bot2_is_white=False)
        elif '--scores' in args:
            # Print per-move scores at depth 2 and 3, then show black's best reply to e4 vs e3
            bot.setupPieces()
            print("\n=== Starting position: scores at depth 2 (fresh TT) ===")
            bot._ttable = LimitedSizeDict(max_size=100_000)
            scores2 = score_all_moves(bot, depth=2)
            for uci, s in scores2[:8]:
                print(f"  {uci}: {s/100:+.2f}")

            print("\n=== Starting position: scores at depth 3 (fresh TT) ===")
            bot._ttable = LimitedSizeDict(max_size=100_000)
            scores3 = score_all_moves(bot, depth=3)
            for uci, s in scores3[:8]:
                print(f"  {uci}: {s/100:+.2f}")

            print("\n=== Starting position: scores at depth 4 (fresh TT) ===")
            bot._ttable = LimitedSizeDict(max_size=100_000)
            scores4 = score_all_moves(bot, depth=4)
            for uci, s in scores4[:8]:
                print(f"  {uci}: {s/100:+.2f}")

            # After e2e4: show black's best replies and white's best w2 for each
            for w1_uci in ['e2e4', 'e2e3']:
                bot.setupPieces()
                bot._ttable = LimitedSizeDict(max_size=100_000)
                print(f"\n=== After {w1_uci}: black's depth-1 replies (white responds optimally) ===")
                apply_uci_to_bot(bot, w1_uci)
                # Score all black moves at depth 1 (black plays, white responds, evaluate)
                black_scores = score_all_moves(bot, depth=1)
                print(f"  Black's best replies (from BLACK's perspective, higher=better for black):")
                for uci, s in black_scores[:6]:  # s is from white's perspective
                    print(f"    black: {uci}  white_eval={s/100:+.2f}")
                # For black's best reply, show white's best w2
                if black_scores:
                    best_black = black_scores[0][0]  # worst for white = best for black
                    # actually lowest white eval = best for black
                    black_scores_wb = sorted(black_scores, key=lambda x: x[1])  # ascending = worst for white first
                    print(f"\n  Black plays: {black_scores_wb[0][0]} (worst for white at {black_scores_wb[0][1]/100:+.2f})")
                    apply_uci_to_bot(bot, black_scores_wb[0][0])
                    white_w2_scores = score_all_moves(bot, depth=0)
                    print(f"  White's best w2 replies (depth 0 eval):")
                    for uci, s in white_w2_scores[:5]:
                        print(f"    white: {uci}  eval={s/100:+.2f}")
        elif '--trace' in args:
            # Trace botMove per-depth decisions for the starting position (and a few others)
            trace_positions = [
                ("Starting position", []),
                ("After 1.e4 e5", ["e2e4", "e7e5"]),
                ("Italian opening (white to move)", ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]),
            ]
            for desc, seq in trace_positions:
                bot.setupPieces()
                for uci in seq:
                    apply_uci_to_bot(bot, uci)
                print(f"\n{'='*60}")
                print(f"  {desc}  ({'White' if bot.whitesMove else 'Black'} to move)")
                print(f"{'='*60}")
                fen = board_to_fen(bot)
                sf_move, sf_eval = sf_analyse(sf, fen, SF_DEPTH)
                print(f"  Stockfish (depth {SF_DEPTH}): {sf_move}  eval={sf_eval/100:+.2f}")
                trace_botmove(bot, time_limit=0.5)
        else:
            results = []
            for desc, seq in POSITIONS:
                r = compare_position(sf, bot, seq, desc)
                if r:
                    results.append(r)

            # Summary
            agree_count = sum(1 for r in results if r['agree'])
            print(f"\n{'='*62}")
            print(f"  SUMMARY: {agree_count}/{len(results)} positions agree with Stockfish")
            disagree = [r for r in results if not r['agree']]
            if disagree:
                print(f"  Disagreements:")
                for r in disagree:
                    print(f"    {r['desc'][:45]}: bot2={r['b2']}  SF={r['sf']}")
            print(f"{'='*62}")
