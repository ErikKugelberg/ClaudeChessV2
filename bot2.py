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
        BmovesBoard = 0x0000000000000000
        WmovesBoard = 0x0000000000000000
        BkingCoord = [-1,-1]
        WkingCoord = [-1,-1]
        BPawnArray = 0x0000000000000000
        WPawnArray = 0x0000000000000000

        lateGame = (64 - self.board.count(0)) < 15
        for x in range(8):
            for y in range(8):
                piece = self.board[y*8 + x]
                if piece > pieceDivider:
                    if piece == Bpawn:
                        BPawnArray |= 1 << (x + y*8)
                        BSum += self.pawnWBL[y*8 + x] if lateGame else self.pawnWBE[y*8 + x]
                    elif piece == Bbishop or piece == Bknight:
                        BSum += self.bishKnighWB[y*8 + x]
                    elif piece == Brook and not lateGame:
                        BSum += self.rookWBE[y*8 + x]
                    elif piece == Bking:
                        BSum += self.kingWBL[y*8 + x] if lateGame else self.kingWBE[y*8 + x]
                        BkingCoord = [x, y]
                    elif piece == Bqueen and not lateGame:
                        BSum += self.queenWBE[y*8 + x]
                    BSum += self.pValues[piece]
                    movesBoard, cnt = self._getMoves(x, y)
                    BmovesBoard |= movesBoard
                    Battacks += cnt
                elif piece != 0:
                    if piece == Wpawn:
                        WPawnArray |= 1 << (x + y*8)
                        WSum += self.pawnWBL[(7-y)*8 + x] if lateGame else self.pawnWBE[(7-y)*8 + x]
                    elif piece == Wbishop or piece == Wknight:
                        WSum += self.bishKnighWB[(7-y)*8 + x]
                    elif piece == Wrook and not lateGame:
                        WSum += self.rookWBE[(7-y)*8 + x]
                    elif piece == Wking:
                        WSum += self.kingWBL[(7-y)*8 + x] if lateGame else self.kingWBE[(7-y)*8 + x]
                        WkingCoord = [x, y]
                    elif piece == Wqueen and not lateGame:
                        WSum += self.queenWBE[(7-y)*8 + x]
                    WSum += self.pValues[piece]
                    movesBoard, cnt = self._getMoves(x, y)
                    WmovesBoard |= movesBoard
                    Wattacks += cnt
        
        
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

            # Rook open/semi-open file bonus
            for y in range(8):
                piece = self.board[y * 8 + x]
                if piece == Wrook:
                    if w_no_pawn and b_no_pawn:
                        WSum += 50
                    elif w_no_pawn:
                        WSum += 25
                elif piece == Brook:
                    if w_no_pawn and b_no_pawn:
                        BSum += 50
                    elif b_no_pawn:
                        BSum += 25

            # Passed pawn bonus
            for y in range(2, 7):
                idx_bit = 1 << (x + y * 8)
                if (WPawnArray & idx_bit) and not (BPawnArray & (fa & self._RANKS_AHEAD[y])):
                    WSum += self._PASSED_BONUS[y]
                if (BPawnArray & idx_bit) and not (WPawnArray & (fa & self._RANKS_BEHIND[y])):
                    BSum += self._PASSED_BONUS[7 - y]

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

        # Based on what stockfish thinks at starting position:
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
        self._stop_search = False
        prevMove : Move
        prevEval = -float('inf')

        moves = self.getLegalMoves()
        while True:
            # Aspiration windows: narrow search window around previous result to prune more branches.
            # Only use when we have a stable eval (not mate, not first iteration).
            aw = 50
            if d >= 3 and prevEval != -float('inf') and abs(prevEval) < 5000:
                move, self.evaluation, moves = self.findBestMove(
                    depthLimit=d, timeLimit=timeLimit, startTime=startTime, moves=moves,
                    initial_alpha=prevEval - aw, initial_beta=prevEval + aw)
                # On fail-low or fail-high, retry with full window
                if not self._stop_search and (self.evaluation <= prevEval - aw or self.evaluation >= prevEval + aw):
                    move, self.evaluation, moves = self.findBestMove(
                        depthLimit=d, timeLimit=timeLimit, startTime=startTime, moves=moves)
            else:
                move, self.evaluation, moves = self.findBestMove(
                    depthLimit=d, timeLimit=timeLimit, startTime=startTime, moves=moves)
            d += 1
            if ((time.time() - startTime) > timeLimit):
                if prevEval > self.evaluation:  # timed out mid-search, use last complete result
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
        inCheck = self._kingChecked(self.whitesMove)
        if (self.whitesMove):
            for t in range(8):
                for p in range(8):
                    if (self.board[p*8 + t] < pieceDivider) and (self.board[p*8 + t] != empty):
                        bb, _ = self._getMoves(t, p, rokad=not inCheck)
                        while bb:
                            bit = bb & -bb; bb ^= bit
                            pos = bit.bit_length() - 1
                            x, y = pos % 8, pos // 8
                            move = Move(t, p, x, y)
                            if self._legalMove(move):
                                if self.board[x + y*8] != empty:
                                    move.setAttacking()
                                moves.append(move)
        else:
            for t in range(8):
                for p in range(8):
                    if self.board[p*8 + t] > pieceDivider:
                        bb, _ = self._getMoves(t, p, rokad=not inCheck)
                        while bb:
                            bit = bb & -bb; bb ^= bit
                            pos = bit.bit_length() - 1
                            x, y = pos % 8, pos // 8
                            move = Move(t, p, x, y)
                            if self._legalMove(move):
                                if self.board[x + y*8] != empty:
                                    move.setAttacking()
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
        for move in moves:
            rec = self._saveState(move)
            self.makeMove(move)
            _cur = self._toString(self.board)
            if (self.boardHistoryCounts.get(_cur, 0) > 2):
                scores.append(0)  # Draw by repetition
            else:
                score = -self._recFindBestEval(depthLimit, -beta, -alpha, timeLimit=timeLimit, startTime=startTime)
                if not self._stop_search:
                    scores.append(score)
            self._undoMove(rec)
            if self._stop_search:
                break
            alpha = max(scores[-1], alpha)
            if alpha >= beta:  # fail-high at root: stop (botMove will retry with wider window)
                break

        if len(scores) == 0:
            return moves[0], -float('inf'), moves  # timed out before any move was evaluated

        bestEval = max(scores)
        indices = [index for index, score in enumerate(scores) if score == bestEval]
        randomIndex = random.randint(0, len(indices)-1)
        move = moves[indices[randomIndex]]

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
            newMoves = [move for move in moves if move.getAttacking() == 1]
            if len(newMoves) != 0:
                moves = newMoves

        for move_idx, move in enumerate(moves):
            rec = self._saveState(move)
            self.makeMove(move)
            _cur = self._toString(self.board)
            if (self.boardHistoryCounts.get(_cur, 0) > 2):
                score = 0  # Draw by repetition — score this move as draw, keep searching
            else:
                # Late Move Reduction: try late quiet moves at reduced depth (no cascading).
                # Skip LMR if the move gives check — check-giving moves can be critical.
                gives_check = self._kingChecked(self.whitesMove)
                if (allow_lmr and not gives_check and move_idx >= 3 and remaining >= 2
                        and move.getAttacking() == 0 and not self._stop_search):
                    score = -self._recFindBestEval(remaining - 1, -alpha - 1, -alpha,
                                                    timeLimit=timeLimit, startTime=startTime,
                                                    allow_lmr=False)
                    # If LMR didn't fail low, re-search at full depth
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
        victim = self.board[move.getX2() + move.getY2()*8]
        if victim != empty:
            attacker = self.board[move.getX1() + move.getY1()*8]
            return 1_000_000 + 10 * self._MVV_LVA_VALUES[victim] - self._MVV_LVA_VALUES[attacker]
        if move == self._killers[depth][0]:
            return 900_000
        if move == self._killers[depth][1]:
            return 800_000
        return self._history[move.getX1() + move.getY1()*8][move.getX2() + move.getY2()*8]

    # Return a list of moves, sorted by TT move, MVV-LVA captures, killers, and history
    def _sortMoves(self, moves, whitesMove, depth=0, tt_move=None):
        moves.sort(key=lambda m: self._mvvLvaScore(m, depth, tt_move), reverse=True)
        return moves

    # Compress chess board to string for map 1200, 
    def _toString(self, board):
        code = 0x0000000000000000000000000000000000000000000000000000000000000000
        for i, p in enumerate(board):
            code |= p << i*4
        return code