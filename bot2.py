# -*- coding: utf-8 -*-
"""
Created on Sun Dec 10 22:00:27 2023

@author: kugel
"""
import numpy as np
import random
import time

from utils import *

class UndoRecord:
    __slots__ = ['changes', 'whitesMove', 'rkMoved', 'enPas', 'nonPawnCount']

    def __init__(self, whitesMove, rkMoved, enPas, nonPawnCount):
        self.changes = []          # list of (board_index, old_value)
        self.whitesMove = whitesMove
        self.rkMoved = rkMoved
        self.enPas = enPas[:]
        self.nonPawnCount = nonPawnCount


class chessBoard2:
    # Combinations of moves a knight can make
    knightMoves = [[-2,1], [-1,2], [1,2], [2,1], [2,-1], [1,-2], [-1,-2], [-2,-1]]

    # Piece Values for evaluating a position, same Indexing as above
    pValues = [0,100,300,300,500,900,0,0,100,300,300,500,900,0]
    kingInCheckValue = 50
    doublePawnValue = -50
    attackValue = 10         # The value of attacking a square, should be the same as in the queen weight board
    castelingValue = 100

    # Weight boards for the different pieces
    kingWBE       = [-10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                    10, 10, 10,-10,-10, 10, 10, 10,
                    20, 30, 20, 10, 10, 20, 30, 20,]

    kingWBL      = [ 0,  0,  0,  0,  0,  0,  0,  0,
                    50, 50, 50, 50, 50, 50, 50, 50,
                    40, 40, 40, 40, 40, 40, 40, 40,
                    30, 30, 30, 30, 30, 30, 30, 30,
                    20, 20, 20, 20, 20, 20, 20, 20,
                    10, 10, 10, 10, 10, 10, 10, 10,
                     0,  0,  0,  0,  0,  0,  0,  0,
                   -10,-10,-10,-10,-10,-10,-10,-10,]

    queenWBE    = [-10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                     0,  0,  0,  0,  0,  0,  0,  0,
                     0,  0,  0,  0,  0,  0,  0,  0,]
    queenWBE = [item*10 for item in queenWBE]

    rookWBE    =  [-10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                   -10,-10,-10,-10,-10,-10,-10,-10,
                     0,  0, 10, 10, 10, 10,  0,  0,
                    10, 10, 20, 20, 20, 20, 10, 10,]

    bishKnighWB = [ 0,  0,  0,  0,  0,  0,  0, 0,
                    0,  0,  0,  0,  0,  0,  0, 0,
                    0, 20, 20, 20, 20, 20, 20, 0,
                    0, 20, 20, 20, 20, 20, 20, 0,
                    0, 20, 20, 20, 20, 20, 20, 0,
                    0, 20, 20, 20, 20, 20, 20, 0,
                    0, 10, 10, 10, 10, 10, 10, 0,
                    0, 10, 10, 10, 10, 10, 10, 0,]

    pawnWBE      = [ 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0,10,10, 0, 0, 0,
                     0, 0, 0,20,20, 0, 0, 0,
                    20, 0,10,20,20,10, 0,20,
                    20,20,20, 0, 0,20,20,20,
                     0, 0, 0, 0, 0, 0, 0, 0,]

    pawnWBL      = [ 0,  0,  0,  0,  0,  0,  0,  0,
                    50, 50, 50, 50, 50, 50, 50, 50,
                    40, 40, 40, 40, 40, 40, 40, 40,
                    30, 30, 30, 30, 30, 30, 30, 30,
                    20, 20, 20, 20, 20, 20, 20, 20,
                    10, 10, 10, 10, 10, 10, 10, 10,
                     0,  0,  0,  0,  0,  0,  0,  0,
                     0,  0,  0,  0,  0,  0,  0,  0,]

    # Precomputed rank masks for passed-pawn detection
    _RANKS_AHEAD  = [sum(0xFF << (r * 8) for r in range(y + 1, 8)) for y in range(8)]
    _RANKS_BEHIND = [sum(0xFF << (r * 8) for r in range(0, y))     for y in range(8)]
    # Precomputed adjacent-file masks (files x-1, x, x+1) per file
    _FILES_AROUND = [
        sum(0x0101010101010101 << col for col in range(max(0, x - 1), min(8, x + 2)))
        for x in range(8)
    ]
    # Precomputed single-file masks
    _FILE_MASK = [0x0101010101010101 << x for x in range(8)]
    # Passed pawn rank bonus (index = white-perspective rank 0-7)
    _PASSED_BONUS = [0, 0, 0, 10, 20, 35, 60, 100]

    # --- Precomputed attack/ray tables built once at class-load time ---
    # For each square: bitboard of squares that piece type attacks (board-state-independent).
    # For sliding pieces: list of ray index-lists (each ray is a list of board indices in order
    # outward from the piece square, within board bounds — no bounds checking needed in eval loop).
    def _build_attack_tables():
        KN = [0]*64; KG = [0]*64; WP = [0]*64; BP = [0]*64
        kn_off = [(-2,1),(-1,2),(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1)]
        for sq in range(64):
            x, y = sq%8, sq//8
            kb = 0
            for dx, dy in kn_off:
                nx, ny = x+dx, y+dy
                if 0<=nx<=7 and 0<=ny<=7: kb |= 1<<(ny*8+nx)
            KN[sq] = kb
            gb = 0
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: continue
                    nx, ny = x+dx, y+dy
                    if 0<=nx<=7 and 0<=ny<=7: gb |= 1<<(ny*8+nx)
            KG[sq] = gb
            wp = 0
            if y < 7:
                if x > 0: wp |= 1<<((y+1)*8+x-1)
                if x < 7: wp |= 1<<((y+1)*8+x+1)
            WP[sq] = wp
            bp = 0
            if y > 0:
                if x > 0: bp |= 1<<((y-1)*8+x-1)
                if x < 7: bp |= 1<<((y-1)*8+x+1)
            BP[sq] = bp
        RK = [[] for _ in range(64)]; BS = [[] for _ in range(64)]; QN = [[] for _ in range(64)]
        for sq in range(64):
            x, y = sq%8, sq//8
            rr = []
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                ray = []; nx, ny = x+dx, y+dy
                while 0<=nx<=7 and 0<=ny<=7:
                    ray.append(ny*8+nx); nx+=dx; ny+=dy
                if ray: rr.append(ray)
            br = []
            for dx, dy in ((1,1),(1,-1),(-1,1),(-1,-1)):
                ray = []; nx, ny = x+dx, y+dy
                while 0<=nx<=7 and 0<=ny<=7:
                    ray.append(ny*8+nx); nx+=dx; ny+=dy
                if ray: br.append(ray)
            RK[sq] = rr; BS[sq] = br; QN[sq] = rr + br
        return KN, KG, WP, BP, RK, BS, QN
    (_KNIGHT_ATTACKS, _KING_ATTACKS, _WPAWN_ATTACKS, _BPAWN_ATTACKS,
     _ROOK_RAYS, _BISHOP_RAYS, _QUEEN_RAYS) = _build_attack_tables()
    del _build_attack_tables

    def __init__(self):
        self.board = []
        self.whitesMove = True              # True if it is whites move
        # King / Rook has moved Brook(left), Bking, Brook(right), Wrook (left), Wking, Wrook(right)
        self.rkMoved = 0b000000
        # Keeps tracks of en passant, x y coordinates of pawn
        self.enPas = [-1,-1]
        self.boardHistory = []         # stack of board hashes for the current game path
        self.boardHistoryCounts = {}   # hash → count; O(1) repetition lookup
        self.i = 0
        self.avgMoveTime = 0
        self.prunings = 0
        self._ttable = LimitedSizeDict(max_size=100_000)
        self.lookUps = 0
        self.avgPositionsEvaluated = 0
        self.whiteKingPos = [4, 0]
        self.blackKingPos = [4, 7]
        self.nonPawnCount = 0  # count of non-pawn pieces (including kings); used by null move guard
        self._history = [[0]*64 for _ in range(64)]
        self._killers = [[None, None] for _ in range(128)]

    # Return the current "score", positive means white is winning
    def evaluatePosition(self) -> float:
        WSum = 0
        BSum = 0
        Wattacks = 0
        Battacks = 0
        BmovesBoard = 0
        WmovesBoard = 0
        BkingCoord = (-1, -1)
        WkingCoord = (-1, -1)
        BPawnArray = 0
        WPawnArray = 0
        WbishopCount = 0
        BbishopCount = 0

        lateGame = (64 - self.board.count(0)) < 15
        board = self.board  # local ref avoids repeated attribute lookup

        # Pre-pass: build own-piece occupancy bitboards needed for mobility computation.
        # O(64) with minimal per-step cost; avoids per-piece rebuild inside the main loop.
        own_W_bb = 0
        own_B_bb = 0
        for sq in range(64):
            pc = board[sq]
            if 0 < pc < pieceDivider:
                own_W_bb |= 1 << sq
            elif pc > pieceDivider:
                own_B_bb |= 1 << sq

        # Main pass: PST scores + mobility via precomputed tables (no _getMoves calls).
        for sq in range(64):
            piece = board[sq]
            if piece == empty:
                continue
            x, y = sq % 8, sq // 8

            if piece > pieceDivider:  # ---- black piece ----
                BSum += self.pValues[piece]
                if piece == Bpawn:
                    BPawnArray |= 1 << sq
                    BSum += self.pawnWBL[sq] if lateGame else self.pawnWBE[sq]
                    # Push mobility
                    if y > 0 and board[sq - 8] == empty:
                        Battacks += 1
                        if y == 6 and board[sq - 16] == empty:
                            Battacks += 1
                    # Diagonal captures via precomputed attack table
                    atk = self._BPAWN_ATTACKS[sq]
                    BmovesBoard |= atk
                    Battacks += bin(atk & own_W_bb).count('1') * 2
                    if self.enPas[0] != -1 and self.enPas[1] == y:
                        ep_sq = (y - 1) * 8 + self.enPas[0]
                        if atk & (1 << ep_sq):
                            Battacks += 2
                elif piece == Bknight:
                    BSum += self.bishKnighWB[sq]
                    atk = self._KNIGHT_ATTACKS[sq]
                    BmovesBoard |= atk
                    reachable = atk & ~own_B_bb
                    Battacks += bin(reachable).count('1') + bin(reachable & own_W_bb).count('1')
                elif piece == Bbishop:
                    BSum += self.bishKnighWB[sq]
                    BbishopCount += 1
                    atk = cnt = 0
                    for ray in self._BISHOP_RAYS[sq]:
                        for idx in ray:
                            pc2 = board[idx]
                            if pc2 == empty:
                                atk |= 1 << idx; cnt += 1
                            else:
                                if pc2 < pieceDivider:  # white piece = enemy
                                    atk |= 1 << idx; cnt += 2
                                break
                    BmovesBoard |= atk; Battacks += cnt
                elif piece == Brook:
                    if not lateGame:
                        BSum += self.rookWBE[sq]
                    atk = cnt = 0
                    for ray in self._ROOK_RAYS[sq]:
                        for idx in ray:
                            pc2 = board[idx]
                            if pc2 == empty:
                                atk |= 1 << idx; cnt += 1
                            else:
                                if pc2 < pieceDivider:
                                    atk |= 1 << idx; cnt += 2
                                break
                    BmovesBoard |= atk; Battacks += cnt
                elif piece == Bqueen:
                    if not lateGame:
                        BSum += self.queenWBE[sq]
                    atk = cnt = 0
                    for ray in self._QUEEN_RAYS[sq]:
                        for idx in ray:
                            pc2 = board[idx]
                            if pc2 == empty:
                                atk |= 1 << idx; cnt += 1
                            else:
                                if pc2 < pieceDivider:
                                    atk |= 1 << idx; cnt += 2
                                break
                    BmovesBoard |= atk; Battacks += cnt
                elif piece == Bking:
                    BSum += self.kingWBL[sq] if lateGame else self.kingWBE[sq]
                    BkingCoord = (x, y)
                    atk = self._KING_ATTACKS[sq]
                    BmovesBoard |= atk
                    reachable = atk & ~own_B_bb
                    Battacks += bin(reachable).count('1') + bin(reachable & own_W_bb).count('1')

            else:  # ---- white piece ----
                WSum += self.pValues[piece]
                if piece == Wpawn:
                    WPawnArray |= 1 << sq
                    WSum += self.pawnWBL[(7-y)*8 + x] if lateGame else self.pawnWBE[(7-y)*8 + x]
                    # Push mobility
                    if y < 7 and board[sq + 8] == empty:
                        Wattacks += 1
                        if y == 1 and board[sq + 16] == empty:
                            Wattacks += 1
                    # Diagonal captures via precomputed attack table
                    atk = self._WPAWN_ATTACKS[sq]
                    WmovesBoard |= atk
                    Wattacks += bin(atk & own_B_bb).count('1') * 2
                    if self.enPas[0] != -1 and self.enPas[1] == y:
                        ep_sq = (y + 1) * 8 + self.enPas[0]
                        if atk & (1 << ep_sq):
                            Wattacks += 2
                elif piece == Wknight:
                    WSum += self.bishKnighWB[(7-y)*8 + x]
                    atk = self._KNIGHT_ATTACKS[sq]
                    WmovesBoard |= atk
                    reachable = atk & ~own_W_bb
                    Wattacks += bin(reachable).count('1') + bin(reachable & own_B_bb).count('1')
                elif piece == Wbishop:
                    WSum += self.bishKnighWB[(7-y)*8 + x]
                    WbishopCount += 1
                    atk = cnt = 0
                    for ray in self._BISHOP_RAYS[sq]:
                        for idx in ray:
                            pc2 = board[idx]
                            if pc2 == empty:
                                atk |= 1 << idx; cnt += 1
                            else:
                                if pc2 > pieceDivider:  # black piece = enemy
                                    atk |= 1 << idx; cnt += 2
                                break
                    WmovesBoard |= atk; Wattacks += cnt
                elif piece == Wrook:
                    if not lateGame:
                        WSum += self.rookWBE[(7-y)*8 + x]
                    atk = cnt = 0
                    for ray in self._ROOK_RAYS[sq]:
                        for idx in ray:
                            pc2 = board[idx]
                            if pc2 == empty:
                                atk |= 1 << idx; cnt += 1
                            else:
                                if pc2 > pieceDivider:
                                    atk |= 1 << idx; cnt += 2
                                break
                    WmovesBoard |= atk; Wattacks += cnt
                elif piece == Wqueen:
                    if not lateGame:
                        WSum += self.queenWBE[(7-y)*8 + x]
                    atk = cnt = 0
                    for ray in self._QUEEN_RAYS[sq]:
                        for idx in ray:
                            pc2 = board[idx]
                            if pc2 == empty:
                                atk |= 1 << idx; cnt += 1
                            else:
                                if pc2 > pieceDivider:
                                    atk |= 1 << idx; cnt += 2
                                break
                    WmovesBoard |= atk; Wattacks += cnt
                elif piece == Wking:
                    WSum += self.kingWBL[(7-y)*8 + x] if lateGame else self.kingWBE[(7-y)*8 + x]
                    WkingCoord = (x, y)
                    atk = self._KING_ATTACKS[sq]
                    WmovesBoard |= atk
                    reachable = atk & ~own_W_bb
                    Wattacks += bin(reachable).count('1') + bin(reachable & own_B_bb).count('1')
        
        
        if not (self.rkMoved & (1 << 1)):
            Bcnt = 0
            if not (self.rkMoved & (1 << 0)):
                Bcnt += 1
            if not (self.rkMoved & (1 << 2)):
                Bcnt += 1
            BSum += Bcnt*self.castelingValue
        if not (self.rkMoved & (1 << 4)):
            Wcnt = 0
            if not (self.rkMoved & (1 << 3)):
                Wcnt += 1
            if not (self.rkMoved & (1 << 5)):
                Wcnt += 1
            WSum += Wcnt*self.castelingValue

        WSum += Wattacks*self.attackValue
        BSum += Battacks*self.attackValue

        # Check for doubled pawns
        for i in range(8):
            Wmask = (0x0101010101010101 << i) & WPawnArray
            Bmask = (0x0101010101010101 << i) & BPawnArray
            Wdoubled = bin(Wmask).count('1')
            Bdoubled = bin(Bmask).count('1')
            if Wdoubled > 1:
                WSum += Wdoubled*self.doublePawnValue
            if Bdoubled > 1:
                BSum += Bdoubled*self.doublePawnValue

        # Passed pawn bonus, rook open-file bonus, and isolated pawn penalty
        for x in range(8):
            fa = self._FILES_AROUND[x]
            fm = self._FILE_MASK[x]
            adj = (self._FILE_MASK[x - 1] if x > 0 else 0) | (self._FILE_MASK[x + 1] if x < 7 else 0)
            w_no_pawn = not (WPawnArray & fm)
            b_no_pawn = not (BPawnArray & fm)

            # Isolated pawn penalty
            if (WPawnArray & fm) and not (WPawnArray & adj):
                WSum -= 20
            if (BPawnArray & fm) and not (BPawnArray & adj):
                BSum -= 20

            # Rook open/semi-open file bonus + 7th-rank bonus
            for y in range(8):
                piece = self.board[y * 8 + x]
                if piece == Wrook:
                    if w_no_pawn and b_no_pawn:
                        WSum += 50
                    elif w_no_pawn:
                        WSum += 25
                    if y == 6:  # 7th rank: cuts off enemy king, attacks pawns
                        WSum += 25
                elif piece == Brook:
                    if w_no_pawn and b_no_pawn:
                        BSum += 50
                    elif b_no_pawn:
                        BSum += 25
                    if y == 1:  # 7th rank for black (white's 2nd rank)
                        BSum += 25

            # Passed pawn bonus
            for y in range(2, 7):
                idx_bit = 1 << (x + y * 8)
                if (WPawnArray & idx_bit) and not (BPawnArray & (fa & self._RANKS_AHEAD[y])):
                    WSum += self._PASSED_BONUS[y]
                if (BPawnArray & idx_bit) and not (WPawnArray & (fa & self._RANKS_BEHIND[y])):
                    BSum += self._PASSED_BONUS[7 - y]

        # Bishop pair bonus: having both bishops is worth ~30 cp in open/semi-open positions
        if WbishopCount >= 2:
            WSum += 30
        if BbishopCount >= 2:
            BSum += 30

        # King safety: pawn shield (middlegame only — in endgame king should be active)
        if not lateGame:
            wx, wy = WkingCoord
            bx, by = BkingCoord
            for dx in (-1, 0, 1):
                sx = wx + dx
                if 0 <= sx < 8:
                    if wy + 1 < 8 and (WPawnArray & (1 << (sx + (wy + 1) * 8))):
                        WSum += 15  # pawn on the rank immediately ahead
                    elif wy + 2 < 8 and (WPawnArray & (1 << (sx + (wy + 2) * 8))):
                        WSum += 7   # pawn two ranks ahead (advanced but still offers cover)
                sx = bx + dx
                if 0 <= sx < 8:
                    if by - 1 >= 0 and (BPawnArray & (1 << (sx + (by - 1) * 8))):
                        BSum += 15
                    elif by - 2 >= 0 and (BPawnArray & (1 << (sx + (by - 2) * 8))):
                        BSum += 7

        if (BkingCoord[0] == -1) or (WkingCoord[0] == -1):
            print(self.board)
            while True:
                time.sleep(1)

        # Add check points
        if WmovesBoard & (1 << (BkingCoord[0] + BkingCoord[1]*8)):
            WSum += self.kingInCheckValue
        if BmovesBoard & (1 << (WkingCoord[0] + WkingCoord[1]*8)):
            BSum += self.kingInCheckValue

        evaluation = (WSum - BSum)

        # Tempo bonus: having the move is worth ~17 cp (calibrated from Stockfish at start pos)
        if self.whitesMove:
            evaluation += 17
        else:
            evaluation -= 17

        return evaluation

    # Let the bot make the best move
    def botMove(self, timeLimit=3, depthLimit=99):
        startTime = time.time()
        d = 2
        self.i = 0
        self.prunings = 0
        self.lookUps = 0
        self._history = [[0]*64 for _ in range(64)]
        self._killers = [[None, None] for _ in range(128)]
        self._ttable = LimitedSizeDict(max_size=100_000)  # clear per-move: cross-move entries contaminate different positions
        self._stop_search = False
        prevMove = None
        prevEval = -float('inf')

        moves = self.getLegalMoves()
        while True:
            # Clear TT before each depth: cross-iteration TT entries (odd-depth values returned
            # by even-depth searches and vice versa) cause wrong evaluations due to parity swings.
            # Move ordering is preserved via the sorted `moves` list from the previous iteration.
            self._ttable = LimitedSizeDict(max_size=100_000)
            move, self.evaluation, moves = self.findBestMove(
                depthLimit=d, timeLimit=timeLimit, startTime=startTime, moves=moves)
            d += 1
            if ((time.time() - startTime) > timeLimit):
                # Search was interrupted: always use the last COMPLETE depth result
                if self._stop_search and prevMove is not None:
                    self.evaluation = prevEval
                    move = prevMove
                break
            prevMove, prevEval = move, self.evaluation
            if d == depthLimit:
                break
        self.depth = d

        IIR = 10
        self.avgMoveTime *= (IIR-1)
        self.avgMoveTime += (time.time() - startTime)
        self.avgMoveTime /= IIR
        self.avgMoveTime = np.round(self.avgMoveTime, decimals=1)
        print(f"\033[31mBot2 | {'White' if self.whitesMove else 'Black'} | Positions: {self.i}  Prunings: {self.prunings}  Depth: {d}  LookUps: {self.lookUps}\033[0m")

        if move != None:
            self.makeMove(move, frfr=True)

        # Normalize to white-positive convention: negate when black just moved (whitesMove is now True)
        white_eval = self.evaluation if not self.whitesMove else -self.evaluation
        return move, self.depth, self.avgMoveTime, white_eval
            
    # Returns list of all possible moves a player can make
    def getLegalMoves(self) -> []:
        moves = []
        board = self.board
        white = self.whitesMove
        in_check = self._kingChecked(white)

        # Pre-compute absolutely-pinned squares via ray-tracing from the king.
        # A piece is pinned if it is the sole friendly piece between the king and
        # an enemy slider on that ray.  Pinned pieces and king moves still go
        # through _legalMove(); all other non-king pieces skip it entirely.
        pinned_set = set()
        if not in_check:
            kx = self.whiteKingPos[0] if white else self.blackKingPos[0]
            ky = self.whiteKingPos[1] if white else self.blackKingPos[1]
            rq = (Brook, Bqueen) if white else (Wrook, Wqueen)
            bq = (Bbishop, Bqueen) if white else (Wbishop, Wqueen)
            for (dx, dy), sliders in (((1,0), rq), ((-1,0), rq), ((0,1), rq), ((0,-1), rq),
                                       ((1,1), bq), ((1,-1), bq), ((-1,1), bq), ((-1,-1), bq)):
                nx, ny = kx+dx, ky+dy
                blocker = -1
                while 0 <= nx <= 7 and 0 <= ny <= 7:
                    sq2 = ny*8+nx
                    pc2 = board[sq2]
                    if pc2 != empty:
                        if white:
                            if 0 < pc2 < pieceDivider:   # own piece
                                if blocker == -1: blocker = sq2
                                else: break              # two own pieces — no pin
                            else:                        # enemy piece
                                if blocker != -1 and pc2 in sliders:
                                    pinned_set.add(blocker)
                                break
                        else:
                            if pc2 > pieceDivider:       # own piece
                                if blocker == -1: blocker = sq2
                                else: break
                            else:                        # enemy piece
                                if blocker != -1 and pc2 in sliders:
                                    pinned_set.add(blocker)
                                break
                    nx += dx; ny += dy

        ep_x = self.enPas[0]  # -1 when no en passant is available

        for sq in range(64):
            pc = board[sq]
            if white:
                if pc == empty or pc >= pieceDivider: continue
                is_king = (pc == Wking)
                is_pawn = (pc == Wpawn)
            else:
                if pc <= pieceDivider: continue
                is_king = (pc == Bking)
                is_pawn = (pc == Bpawn)

            tx, ty = sq % 8, sq // 8
            # must_check: king moves, any move while in check, and pinned pieces.
            # Safe pieces (not pinned, not king, not in check) cannot expose the king,
            # so their pseudo-legal moves are all legal — skip _legalMove entirely.
            must_check = in_check or is_king or (sq in pinned_set)

            bb, _ = self._getMoves(tx, ty, rokad=not in_check)
            while bb:
                bit = bb & -bb; bb ^= bit
                dest = bit.bit_length() - 1
                dx2, dy2 = dest % 8, dest // 8
                move = Move(tx, ty, dx2, dy2)

                dest_pc = board[dest]
                if dest_pc != empty:
                    move.setAttacking()

                # En passant: diagonal pawn move to an empty square.  Even when the
                # pawn is not pinned, en passant can expose a rank pin (both the moving
                # pawn and the captured pawn leave the same rank), so always check it.
                if must_check or (is_pawn and ep_x != -1 and dest_pc == empty and dx2 != tx):
                    if not self._legalMove(move):
                        continue
                moves.append(move)

        return moves

    # Set up the board to starting position
    def setupPieces(self):
        self.board = [
                    Wrook, Wknight, Wbishop, Wqueen, Wking, Wbishop, Wknight, Wrook,
                    Wpawn, Wpawn, Wpawn, Wpawn, Wpawn, Wpawn, Wpawn, Wpawn,
                    0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0,
                    Bpawn, Bpawn, Bpawn, Bpawn, Bpawn, Bpawn, Bpawn, Bpawn,
                    Brook, Bknight, Bbishop, Bqueen, Bking, Bbishop, Bknight, Brook,
                    ]
        self.whitesMove = True
        # King / Rook has moved Brook(left), Bking, Brook(right), Wrook (left), Wking, Wrook(right)
        self.rkMoved = 0b000000
        # Keeps tracks of en passant
        self.enPas = [-1,-1]
        self.boardHistory = []
        self.boardHistoryCounts = {}
        self.whiteKingPos = [4, 0]
        self.blackKingPos = [4, 7]
        self.nonPawnCount = sum(1 for p in self.board if p != empty and p != Wpawn and p != Bpawn)

    # Execute a move, OBS: this does not care if it is legal or not!
    def makeMove(self, move, frfr=False):
        piece = self.board[move.getX2() + move.getY2()*8]
        if (piece == Wking) or (piece == Bking):
            print("the king was taken wtf ", self.board[move.getX1() + move.getY1()*8])

        self._movePieces(move)
        
        piece = self.board[move.getX2() + move.getY2()*8]

        # Keep track of en passant opportunities
        if ((piece == Wpawn) or (piece == Bpawn)) and (np.abs(move.getY1()-move.getY2()) == 2):
            self.enPas = [move.getX2(), move.getY2()]
        else:
            self.enPas = [-1,-1]

        # Keep track of where a rokad has happened
        if (piece == Brook):
            if move.getX1() == 0:
                self.rkMoved |= 1 << 0
            else:
                self.rkMoved |= 1 << 2
        elif piece == Wrook:
            if move.getX1() == 0:
                self.rkMoved |= 1 << 3
            else:
                self.rkMoved |= 1 << 5
        elif piece == Wking:
            self.rkMoved |= 1 << 4
        elif piece == Bking:
            self.rkMoved |= 1 << 1
        self.whitesMove = not self.whitesMove

        _bh = self._toString(self.board)
        self.boardHistory.append(_bh)
        self.boardHistoryCounts[_bh] = self.boardHistoryCounts.get(_bh, 0) + 1
        if frfr:
            if self.boardHistoryCounts[_bh] > 2:
                return drawRep
            else:
                # Check for stalemate/win
                moves = self.getLegalMoves()
                if len(moves) == 0:
                    if not self._kingChecked(checkWhiteKing=self.whitesMove):
                        return staleMate
                    elif self.whitesMove:
                        print("Black wins!")
                        return blackWin
                    else:
                        print("White wins!")
                        return whiteWin
        return onGoing

    # Set position to a given chess position, if it is legal
    def setPosition(self, newBoard, whitesMove):
        oldBoard = self.board.copy()
        self.board = newBoard.copy()
        if self._kingChecked(not whitesMove):
            self.board = oldBoard.copy()
            print("Illegal position")
            return False
        self.whitesMove = whitesMove
        self.nonPawnCount = sum(1 for p in self.board if p != empty and p != Wpawn and p != Bpawn)
        return True

    # Set position to a given chess position, if it is legal
    def getPosition(self):
        return self.board.copy()

    # Returns the best move for a given position, the evaluation after this (negamax)
    def findBestMove(self, depthLimit=1, timeLimit=1, startTime=0, moves=[],
                     initial_alpha=-float('inf'), initial_beta=float('inf')):
        self._stop_search = False
        alpha = initial_alpha
        beta = initial_beta

        if len(moves) == 0:
            if self._kingChecked(checkWhiteKing=self.whitesMove):
                return None, alpha, []  # We lose (checkmate)
            else:
                return None, 0, []  # Stalemate

        scores = []
        best_move = None
        best_score = -float('inf')
        for move in moves:
            rec = self._saveState(move)
            self.makeMove(move)
            _cur = self._toString(self.board)
            if (self.boardHistoryCounts.get(_cur, 0) > 2):
                score = 0
                scores.append(score)
            else:
                score = -self._recFindBestEval(depthLimit, -beta, -alpha, timeLimit=timeLimit, startTime=startTime)
                if not self._stop_search:
                    scores.append(score)
            self._undoMove(rec)
            if self._stop_search:
                break
            # Track the best move via strict improvement only: moves evaluated later with a
            # tight alpha-beta window can fail-high and return exactly alpha (a lower bound),
            # not their true score. Using strict improvement avoids spurious ties with those.
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(score, alpha)
            if alpha >= beta:  # fail-high at root: stop (botMove will retry with wider window)
                break

        if len(scores) == 0:
            return moves[0], -float('inf'), moves  # timed out before any move was evaluated

        bestEval = best_score
        move = best_move

        # Pad unevaluated moves with -inf so they sort to the end but the full list is preserved
        padded = scores + [-float('inf')] * (len(moves) - len(scores))
        newMoves = sorted(zip(moves, padded), key=lambda x: x[1], reverse=True)
        newMoves = [m for m, _ in newMoves]

        return move, bestEval, newMoves

    # Returns the best eval of a certain move, given the following moves (negamax)
    def _recFindBestEval(self, depth, alpha, beta, timeLimit, startTime, allow_null=True, allow_lmr=True):
        if self._stop_search:
            return -float('inf')
        if (time.time() - startTime) > timeLimit:
            self._stop_search = True
            return -float('inf')

        entry_depth = depth

        # Transposition table lookup — key encodes full game state, not just pieces
        _bh = self._toString(self.board)
        ttKey = (_bh, self.whitesMove, self.rkMoved, self.enPas[0], self.enPas[1])
        tt_move = None
        if self._ttable.containsKey(ttKey):
            entry = self._ttable[ttKey]
            stored_depth, stored_eval = entry[0], entry[1]
            tt_move = entry[2] if len(entry) > 2 else None
            if stored_depth >= entry_depth:
                self.lookUps += 1
                return stored_eval

        if depth == 0:
            self.i += 1
            eval_val = self.evaluatePosition() if self.whitesMove else -self.evaluatePosition()
            self._ttable[ttKey] = (0, eval_val, None)
            return eval_val

        bestEval = -float('inf')
        remaining = depth - 1
        best_move = None

        # Null move pruning BEFORE getLegalMoves: when pruning, we skip the expensive getLegalMoves call.
        # require remaining > R so opponent gets at least 1 real ply.
        R = 2
        if (allow_null and remaining > R
                and not self._kingChecked(self.whitesMove)
                and self.nonPawnCount > 4):
            old_enPas = self.enPas[:]
            self.enPas = [-1, -1]
            self.whitesMove = not self.whitesMove
            null_score = -self._recFindBestEval(remaining - R, -beta, -beta + 1,
                                                 timeLimit=timeLimit, startTime=startTime,
                                                 allow_null=False)
            self.whitesMove = not self.whitesMove
            self.enPas = old_enPas
            if not self._stop_search and null_score >= beta:
                return beta

        moves = self.getLegalMoves()

        if len(moves) == 0:
            if self._kingChecked(checkWhiteKing=self.whitesMove):
                return bestEval  # checkmate: -inf from current player's perspective
            else:
                return 0  # stalemate

        if remaining != 0:
            moves = self._sortMoves(moves, self.whitesMove, entry_depth, tt_move)
        else:
            # Stand-pat at the capture-search frontier: the player can always choose NOT to capture.
            # This prevents forced bad captures (e.g. exd5 after 1.e4 d5) from distorting scores.
            stand_pat = self.evaluatePosition() if self.whitesMove else -self.evaluatePosition()
            self.i += 1
            if stand_pat >= beta:
                return stand_pat
            if stand_pat > alpha:
                alpha = stand_pat
            bestEval = max(bestEval, stand_pat)
            moves = [m for m in moves if m.getAttacking() == 1]
            # Filter losing captures at the search horizon: skip moves where we give away
            # a piece worth >3× the victim (e.g. Qxpawn, Rxpawn). These look good statically
            # because the opponent's recapture isn't evaluated at depth=0, but they're almost
            # always unsound. Victim==0 passes through (en passant, edge cases).
            moves = [m for m in moves
                     if self.pValues[self.board[m.getY2()*8 + m.getX2()]] == 0
                     or self.pValues[self.board[m.getY2()*8 + m.getX2()]] * 3
                        >= self.pValues[self.board[m.getY1()*8 + m.getX1()]]]
            if not moves:
                return bestEval  # no captures: stand-pat is the answer

        for move_idx, move in enumerate(moves):
            rec = self._saveState(move)
            self.makeMove(move)
            _cur = self._toString(self.board)
            if (self.boardHistoryCounts.get(_cur, 0) > 2):
                score = 0  # Draw by repetition — score this move as draw, keep searching
            else:
                # Late Move Reduction: try late quiet moves at reduced depth (no cascading).
                # _kingChecked is lazy: only called when all cheaper LMR conditions pass.
                if (allow_lmr and move_idx >= 5 and remaining >= 3
                        and move.getAttacking() == 0 and not self._stop_search
                        and not self._kingChecked(self.whitesMove)):
                    # LMR: probe at reduced depth with null window; re-search if it beats alpha.
                    # allow_null=False prevents null move firing inside already-reduced searches.
                    score = -self._recFindBestEval(remaining - 1, -alpha - 1, -alpha,
                                                    timeLimit=timeLimit, startTime=startTime,
                                                    allow_lmr=False, allow_null=False)
                    if not self._stop_search and score > alpha:
                        score = -self._recFindBestEval(remaining, -beta, -alpha,
                                                        timeLimit=timeLimit, startTime=startTime)
                else:
                    score = -self._recFindBestEval(remaining, -beta, -alpha, timeLimit=timeLimit, startTime=startTime)
            self._undoMove(rec)

            if self._stop_search:
                break  # don't use score from incomplete search

            if score > bestEval:
                bestEval = score
                best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                self.prunings += 1
                if move.getAttacking() == 0:
                    self._history[move.getX1() + move.getY1()*8][move.getX2() + move.getY2()*8] += entry_depth * entry_depth
                    if move != self._killers[entry_depth][0]:
                        self._killers[entry_depth][1] = self._killers[entry_depth][0]
                        self._killers[entry_depth][0] = move
                self._ttable[ttKey] = (entry_depth, bestEval, move)
                return bestEval

        if not self._stop_search:
            self._ttable[ttKey] = (entry_depth, bestEval, best_move)
        return bestEval

    # Moves the pieces, but doesn't update things like en Passant, board history and rokad logic
    def _movePieces(self, move):
        piece = self.board[move.getX1() + move.getY1()*8]
        captured = self.board[move.getX2() + move.getY2()*8]
        self.board[move.getX2() + move.getY2()*8] = piece
        self.board[move.getX1() + move.getY1()*8] = empty
        if captured != empty and captured != Wpawn and captured != Bpawn:
            self.nonPawnCount -= 1

        if piece == Wking:
            self.whiteKingPos = [move.getX2(), move.getY2()]
        elif piece == Bking:
            self.blackKingPos = [move.getX2(), move.getY2()]

        # Do a Rokad
        if piece == Wking:
            if (not self.rkMoved & (1 << 4)) and (move.getX2() == 2) and (self.board[0] == Wrook):
                self.board[0] = empty
                self.board[3] = Wrook
            elif (not self.rkMoved & (1 << 4)) and (move.getX2() == 6) and (self.board[7] == Wrook):
                self.board[7] = empty
                self.board[5] = Wrook
        elif piece == Bking:
            if (not self.rkMoved & (1 << 1)) and (move.getX2() == 2) and (self.board[7*8] == Brook):
                self.board[7*8] = empty
                self.board[59] = Brook
            elif (not self.rkMoved & (1 << 1)) and (move.getX2() == 6) and (self.board[7 + 7*8] == Brook):
                self.board[63] = empty
                self.board[61] = Brook

        # Check en Passant
        if (self.enPas[0] == move.getX2()):
            if ((piece == Bpawn) and (move.getY2() == self.enPas[1] - 1)) or ((piece == Wpawn) and (move.getY2() == self.enPas[1] + 1)):
                self.board[self.enPas[0] + self.enPas[1]*8] = empty
        
        # Check for queened pawns
        if (piece == Wpawn) and (move.getY2() == 7):
            self.board[move.getX2() + move.getY2()*8] = Wqueen
            self.nonPawnCount += 1
        elif (piece == Bpawn) and (move.getY2() == 0):
            self.board[move.getX2() + move.getY2()*8] = Bqueen
            self.nonPawnCount += 1

    # Capture the board squares that will change for the given move (call before _movePieces)
    def _saveState(self, move):
        rec = UndoRecord(self.whitesMove, self.rkMoved, self.enPas, self.nonPawnCount)
        x1, y1, x2, y2 = move.getX1(), move.getY1(), move.getX2(), move.getY2()
        piece = self.board[x1 + y1*8]
        rec.changes.append((x1 + y1*8, piece))
        rec.changes.append((x2 + y2*8, self.board[x2 + y2*8]))
        # Castling: rook squares that _movePieces will touch
        if piece == Wking and not (self.rkMoved & (1 << 4)):
            if x2 == 2:
                rec.changes += [(0, self.board[0]), (3, self.board[3])]
            elif x2 == 6:
                rec.changes += [(7, self.board[7]), (5, self.board[5])]
        elif piece == Bking and not (self.rkMoved & (1 << 1)):
            if x2 == 2:
                rec.changes += [(56, self.board[56]), (59, self.board[59])]
            elif x2 == 6:
                rec.changes += [(63, self.board[63]), (61, self.board[61])]
        # En passant: captured pawn square
        if self.enPas[0] == x2:
            if (piece == Bpawn and y2 == self.enPas[1] - 1) or \
               (piece == Wpawn and y2 == self.enPas[1] + 1):
                rec.changes.append((x2 + self.enPas[1]*8, self.board[x2 + self.enPas[1]*8]))
        return rec

    # Restore board state from an UndoRecord (after makeMove)
    def _undoMove(self, rec):
        for idx, val in rec.changes:
            self.board[idx] = val
            if val == Wking:
                self.whiteKingPos = [idx % 8, idx // 8]
            elif val == Bking:
                self.blackKingPos = [idx % 8, idx // 8]
        self.whitesMove = rec.whitesMove
        self.rkMoved = rec.rkMoved
        self.enPas = rec.enPas
        self.nonPawnCount = rec.nonPawnCount
        _bh = self.boardHistory.pop()
        cnt = self.boardHistoryCounts.get(_bh, 0) - 1
        if cnt <= 0:
            self.boardHistoryCounts.pop(_bh, None)
        else:
            self.boardHistoryCounts[_bh] = cnt

    # Check if a given move is legal
    def _legalMove(self, move) -> bool:
        rec = self._saveState(move)
        self._movePieces(move)
        legal = not self._kingChecked(self.whitesMove)
        for idx, val in rec.changes:
            self.board[idx] = val
            if val == Wking:
                self.whiteKingPos = [idx % 8, idx // 8]
            elif val == Bking:
                self.blackKingPos = [idx % 8, idx // 8]
        return legal

    # Checks if a king is checked (ray-tracing from king position, ~4x faster than generating all enemy moves)
    def _kingChecked(self, checkWhiteKing) -> bool:
        if checkWhiteKing:
            kx, ky = self.whiteKingPos
            e_rq = (Brook, Bqueen)
            e_bq = (Bbishop, Bqueen)
            e_knight = Bknight
            e_pawn   = Bpawn
            e_king   = Bking
            pawn_dy  = 1   # black pawns attack downward, so they sit above the white king
        else:
            kx, ky = self.blackKingPos
            e_rq = (Wrook, Wqueen)
            e_bq = (Wbishop, Wqueen)
            e_knight = Wknight
            e_pawn   = Wpawn
            e_king   = Wking
            pawn_dy  = -1  # white pawns attack upward, so they sit below the black king

        # Rook / queen — horizontal and vertical rays
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            x, y = kx+dx, ky+dy
            while 0 <= x <= 7 and 0 <= y <= 7:
                p = self.board[y*8+x]
                if p != empty:
                    if p == e_rq[0] or p == e_rq[1]:
                        return True
                    break
                x += dx; y += dy

        # Bishop / queen — diagonal rays
        for dx, dy in ((1,1),(1,-1),(-1,1),(-1,-1)):
            x, y = kx+dx, ky+dy
            while 0 <= x <= 7 and 0 <= y <= 7:
                p = self.board[y*8+x]
                if p != empty:
                    if p == e_bq[0] or p == e_bq[1]:
                        return True
                    break
                x += dx; y += dy

        # Knights
        for dx, dy in self.knightMoves:
            x, y = kx+dx, ky+dy
            if 0 <= x <= 7 and 0 <= y <= 7 and self.board[y*8+x] == e_knight:
                return True

        # Pawns (enemy pawns sit one rank in pawn_dy direction, on adjacent files)
        py = ky + pawn_dy
        if 0 <= py <= 7:
            for px in (kx-1, kx+1):
                if 0 <= px <= 7 and self.board[py*8+px] == e_pawn:
                    return True

        # Enemy king (adjacent squares)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                x, y = kx+dx, ky+dy
                if 0 <= x <= 7 and 0 <= y <= 7 and self.board[y*8+x] == e_king:
                    return True

        return False
   
    # Follow a defined path on the board, setting the movesBoard to 1 along it until it runs into a piece
    def _iterateMovesW(self,x,y,xt,yt, newBoard=0x0000000000000000, nrMoves=0):
        t = x + xt
        p = y + yt
        while (t != 8) and (p != 8) and (t != -1) and (p != -1):
            if self.board[p*8 + t] == empty:
                newBoard |= (1 << (p*8+t))
                nrMoves += 1
                t += xt
                p += yt
            elif pieceDivider < self.board[p*8 + t]:
                newBoard |= (1 << (p*8+t))
                nrMoves += 2
                t = 8
            else:
                t = 8
        return newBoard, nrMoves

    # Follow a defined path on the board, setting the movesBoard to 1 along it until it runs into a piece
    def _iterateMovesB(self,x,y,xt,yt, newBoard=0x0000000000000000, nrMoves=0):
        t = x + xt
        p = y + yt
        while (t != 8) and (p != 8) and (t != -1) and (p != -1):
            if self.board[p*8 + t] == empty:
                newBoard |= (1 << (p*8+t))
                nrMoves += 1
                t += xt
                p += yt
            elif pieceDivider > self.board[p*8 + t]:
                newBoard |= (1 << (p*8+t))
                nrMoves += 2
                t = 8
            else:
                t = 8
        return newBoard, nrMoves

    # Update movesBoard, which shows which squares the current piece can go to
    def _getMoves(self,x,y,rokad=False):
        newBoard = 0x0000000000000000
        nrMoves = 0
        piece = self.board[y*8 + x]
        if piece == Wpawn:
            if y < 7:
                if self.board[(y+1)*8+x] == empty:
                    newBoard |= (1 << ((y+1)*8+x))
                    nrMoves += 1
                    if y == 1:
                        if (self.board[(y+2)*8+x] == empty):
                            newBoard |= (1 << ((y+2)*8+x))
                            nrMoves += 1
                if x != 0:
                    if (self.board[(y+1)*8+(x-1)] > pieceDivider) or (self.enPas == [x-1,y]):
                        newBoard |= (1 << ((y+1)*8+(x-1)))
                        nrMoves += 2
                if x != 7:
                    if (self.board[(y+1)*8+(x+1)] > pieceDivider) or (self.enPas == [x+1,y]):
                        newBoard |= (1 << ((y+1)*8+(x+1)))
                        nrMoves += 2
        elif piece == Bpawn:
            if y > 0:
                if self.board[x + (y-1)*8] == empty:
                    newBoard |= (1 << ((y-1)*8+x))
                    nrMoves += 1
                    if y == 6:
                        if (self.board[(y-2)*8+x] == empty):
                            newBoard |= (1 << ((y-2)*8+x))
                            nrMoves += 1
                if x != 0:
                    if ((self.board[(y-1)*8+(x-1)] < pieceDivider) and (self.board[(y-1)*8+(x-1)] != empty)) or (self.enPas == [x-1,y]):
                        newBoard |= (1 << ((y-1)*8+(x-1)))
                        nrMoves += 2
                if x != 7:
                    if ((self.board[(y-1)*8+(x+1)] < pieceDivider) and (self.board[(y-1)*8+(x+1)] != empty)) or (self.enPas == [x+1,y]):
                        newBoard |= (1 << ((y-1)*8+(x+1)))
                        nrMoves += 2
        elif piece == Wrook:
            newBoard, nrMoves = self._iterateMovesW(x,y,1,0, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,-1,0, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,0,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,0,-1, newBoard, nrMoves)
        elif piece == Brook:
            newBoard, nrMoves = self._iterateMovesB(x,y,1,0, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,-1,0, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,0,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,0,-1, newBoard, nrMoves)
        elif piece == Wbishop:
            newBoard, nrMoves = self._iterateMovesW(x,y,1,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,1,-1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,-1,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,-1,-1, newBoard, nrMoves)
        elif piece == Bbishop:
            newBoard, nrMoves = self._iterateMovesB(x,y,1,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,1,-1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,-1,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,-1,-1, newBoard, nrMoves)
        elif piece == Wqueen:
            newBoard, nrMoves = self._iterateMovesW(x,y,1,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,1,-1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,-1,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,-1,-1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,1,0, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,-1,0, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,0,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesW(x,y,0,-1, newBoard, nrMoves)
        elif piece == Bqueen:
            newBoard, nrMoves = self._iterateMovesB(x,y,1,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,1,-1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,-1,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,-1,-1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,1,0, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,-1,0, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,0,1, newBoard, nrMoves)
            newBoard, nrMoves = self._iterateMovesB(x,y,0,-1, newBoard, nrMoves)
        elif piece == Wking:
            for t in range(3):
                for p in range(3):
                    xt = x -1 + t
                    yp = y -1 + p
                    if (0 <= xt <= 7) and (0 <= yp <= 7):
                        if (self.board[yp*8 + xt] > pieceDivider) or (self.board[yp*8 + xt] == empty): 
                            newBoard |= (1 << (yp*8+xt))
                            nrMoves += 1
            # Rokad logic
            if rokad and (not self.rkMoved & (1 << 4)):
                if (not self.rkMoved & (1 << 3)) and (self.board[1] == empty) and (self.board[2] == empty) and (self.board[3] == empty):
                        newBoard |= (1 << 2)
                        nrMoves += 1
                if (not self.rkMoved & (1 << 5)) and (self.board[5] == empty) and (self.board[6] == empty):
                        newBoard |= (1 << 6)
                        nrMoves += 1        
        elif piece == Bking:
            for t in range(3):
                for p in range(3):
                    xt = x -1 + t
                    yp = y -1 + p
                    if (0 <= xt <= 7) and (0 <= yp <= 7):
                        if (self.board[yp*8 + xt] < pieceDivider) or (self.board[yp*8 + xt] == empty):
                            newBoard |= (1 << (yp*8+xt))
                            nrMoves += 1
            # Rokad logic
            if rokad and (not self.rkMoved & (1 << 1)):
                if (not self.rkMoved & (1 << 0)) and (self.board[57] == empty) and (self.board[58] == empty) and (self.board[59] == empty):
                        newBoard |= (1 << 58)
                        nrMoves += 1
                if (not self.rkMoved & (1 << 2)) and (self.board[61] == empty)and (self.board[62] == empty):
                        newBoard |= (1 << 62)
                        nrMoves += 1
        elif piece == Wknight:
            for m in self.knightMoves:
                xt = x + m[0]
                yp = y + m[1]
                if (0 <= xt <= 7) and (0 <= yp <= 7):
                    nr = yp*8 + xt
                    if (self.board[nr] == empty):
                        newBoard |= (1 << nr)
                        nrMoves += 1
                    elif (self.board[nr] > pieceDivider):
                        newBoard |= (1 << nr)
                        nrMoves += 2
        elif piece == Bknight:
            for m in self.knightMoves:
                xt = x + m[0]
                yp = y + m[1]
                if (0 <= xt <= 7) and (0 <= yp <= 7):
                    nr = yp*8 + xt
                    if  (self.board[nr] == empty):
                        newBoard |= (1 << nr)
                        nrMoves += 1
                    elif (self.board[nr] < pieceDivider):
                        newBoard |= (1 << nr)
                        nrMoves += 2
        return newBoard, nrMoves

    # MVV-LVA score: captures scored by (10*victim_value - attacker_value), quiet moves score 0
    _MVV_LVA_VALUES = [0, 100, 300, 300, 500, 900, 20000, 0, 100, 300, 300, 500, 900, 20000]

    def _mvvLvaScore(self, move, depth=0, tt_move=None):
        if tt_move is not None and move == tt_move:
            return 2_000_000
        if move.getAttacking() == 1:
            victim = self.board[move.getX2() + move.getY2()*8]
            attacker = self.board[move.getX1() + move.getY1()*8]
            # En passant: destination square is empty; treat captured piece as a pawn
            victim_val = self._MVV_LVA_VALUES[victim] if victim != empty else self._MVV_LVA_VALUES[Wpawn]
            return 1_000_000 + 10 * victim_val - self._MVV_LVA_VALUES[attacker]
        if move == self._killers[depth][0]:
            return 900_000
        if move == self._killers[depth][1]:
            return 800_000
        return self._history[move.getX1() + move.getY1()*8][move.getX2() + move.getY2()*8]

    # Return a list of moves, sorted by TT move, MVV-LVA captures, killers, and history
    def _sortMoves(self, moves, whitesMove, depth=0, tt_move=None):
        moves.sort(key=lambda m: self._mvvLvaScore(m, depth, tt_move), reverse=True)
        return moves

    def _toString(self, board):
        return bytes(board)