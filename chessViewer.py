import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

from utils import *
from bot1 import *
from bot2 import *

TIME_LIMIT = 1  # seconds per move


class boardManager:
    Wpawn_img   = mpimg.imread('white-pawn.png')
    Wbishop_img = mpimg.imread('white-bishop.png')
    Wknight_img = mpimg.imread('white-knight.png')
    Wrook_img   = mpimg.imread('white-rook.png')
    Wqueen_img  = mpimg.imread('white-queen.png')
    Wking_img   = mpimg.imread('white-king.png')
    Bpawn_img   = mpimg.imread('black-pawn.png')
    Bbishop_img = mpimg.imread('black-bishop.png')
    Bknight_img = mpimg.imread('black-knight.png')
    Brook_img   = mpimg.imread('black-rook.png')
    Bqueen_img  = mpimg.imread('black-queen.png')
    Bking_img   = mpimg.imread('black-king.png')

    black_color  = (150/255, 75/255, 0)
    white_color  = (245/255, 245/255, 220/255)
    red_color    = (255/255, 192/255, 203/255)
    yellow_color = (255/255, 170/255, 51/255)

    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.yellowSquare = [-1, -1]
        self.movesBoard = 0
        self.board = [0] * 64
        self.playWhite = True       # board orientation
        self.avgMoveTime = 0
        self.bot1Depth = 0
        self.bot2Depth = 0
        self.bot1Evaluation = 0
        self.bot2Evaluation = 0
        self.bot1Wins = 0
        self.bot2Wins = 0
        self.draws = 0
        self.gameNum = 0
        self.whiteLabel = "bot1"
        self.blackLabel = "bot2"
        # Single-player state
        self._sp_bot = None
        self._sp_user_white = True
        self._selected = None       # (bx, by) of piece selected by user
        self._bot_thinking = False
        self._game_over = False

    def draw(self, block=True, delay=0):
        self.ax.clear()
        for t in range(8):
            for p in range(8):
                # Visual position depends on board orientation
                x = t if self.playWhite else 7 - t
                y = p if self.playWhite else 7 - p

                if self.movesBoard & (1 << (8*p + t)):
                    color = self.red_color
                elif [t, p] == self.yellowSquare:
                    color = self.yellow_color
                elif (x + y) % 2 == 0:
                    color = self.black_color
                else:
                    color = self.white_color
                self.ax.add_patch(plt.Rectangle((x, y), 1, 1, edgecolor=color, facecolor=color, zorder=0))
                if self.board[p*8 + t] != empty:
                    self._drawPiece(x, y, self.board[p*8 + t])

        if self._sp_bot is not None:
            plt.text(8.1, 7.0, "Your Wins: " + str(self.bot1Wins),                                  fontsize=10, color='blue')
            plt.text(8.1, 6.0, "Draws:     " + str(self.draws),                                     fontsize=10, color='black')
            plt.text(8.1, 5.0, "Bot Wins:  " + str(self.bot2Wins),                                  fontsize=10, color='red')
            plt.text(8.1, 3.5, "Bot Eval:  " + str(np.round(self.bot2Evaluation/100, decimals=1)),  fontsize=10, color='red')
            plt.text(8.1, 3.0, "Bot Depth: " + str(self.bot2Depth),                                 fontsize=10, color='red')
            plt.text(8.1, 2.5, "Time:      " + str(self.avgMoveTime),                               fontsize=10, color='red')
        else:
            plt.text(8.1, 7.5, f"Game {self.gameNum}",                                              fontsize=10, color='black')
            plt.text(8.1, 7.1, f"White: {self.whiteLabel}",                                         fontsize=9,  color='black')
            plt.text(8.1, 6.8, f"Black: {self.blackLabel}",                                         fontsize=9,  color='black')
            plt.text(8.1, 6.2, f"Bot1 Wins:  {self.bot1Wins}",                                      fontsize=10, color='blue')
            plt.text(8.1, 5.7, f"Bot1 Eval:  {np.round(self.bot1Evaluation/100, decimals=1)}",      fontsize=10, color='blue')
            plt.text(8.1, 5.2, f"Bot1 Depth: {self.bot1Depth}",                                     fontsize=10, color='blue')
            plt.text(8.1, 4.4, f"Bot2 Wins:  {self.bot2Wins}",                                      fontsize=10, color='red')
            plt.text(8.1, 3.9, f"Bot2 Eval:  {np.round(self.bot2Evaluation/100, decimals=1)}",      fontsize=10, color='red')
            plt.text(8.1, 3.4, f"Bot2 Depth: {self.bot2Depth}",                                     fontsize=10, color='red')
            plt.text(8.1, 2.5, f"Draws:      {self.draws}",                                         fontsize=10, color='black')
            plt.text(8.1, 2.0, f"Time:       {self.avgMoveTime}",                                   fontsize=10, color='black')

        self.ax.add_patch(plt.Rectangle((0, 0), 8, 8, fill=False, edgecolor='black', linewidth=2, zorder=5))
        self.ax.set_xlim(0, 11)
        self.ax.set_ylim(0, 8)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        self.ax.set_aspect('equal', 'box')
        plt.show(block=block)
        if delay:
            plt.pause(delay)

    def setPosition(self, newBoard, yellowSquare=[-1, -1]):
        self.board = newBoard.copy()
        self.yellowSquare = yellowSquare

    def _drawPiece(self, x, y, piece):
        img_map = {
            Wpawn: self.Wpawn_img, Wbishop: self.Wbishop_img, Wknight: self.Wknight_img,
            Wrook: self.Wrook_img, Wqueen:  self.Wqueen_img,  Wking:   self.Wking_img,
            Bpawn: self.Bpawn_img, Bbishop: self.Bbishop_img, Bknight: self.Bknight_img,
            Brook: self.Brook_img, Bqueen:  self.Bqueen_img,  Bking:   self.Bking_img,
        }
        if piece in img_map:
            self.ax.imshow(img_map[piece], extent=(x, x+1, y, y+1), alpha=1, zorder=1)

    # -------------------------------------------------------------------------
    # Single-player click handling
    # -------------------------------------------------------------------------

    def setup_single_player(self, bot, user_is_white):
        self._sp_bot = bot
        self._sp_user_white = user_is_white
        self.playWhite = user_is_white
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

    def _on_click(self, event):
        if self._bot_thinking or self._game_over:
            return
        if event.xdata is None or event.ydata is None:
            return

        # Convert visual click to board coordinates
        cx, cy = int(event.xdata), int(event.ydata)
        if not (0 <= cx < 8 and 0 <= cy < 8):
            return
        bx = cx if self._sp_user_white else 7 - cx
        by = cy if self._sp_user_white else 7 - cy

        # Ignore clicks when it's the bot's turn
        if self._sp_bot.whitesMove != self._sp_user_white:
            return

        piece = self._sp_bot.board[by*8 + bx]

        if self._selected is None:
            # First click: select one of the user's pieces
            is_users = (self._sp_user_white and 0 < piece < pieceDivider) or \
                       (not self._sp_user_white and piece > pieceDivider)
            if is_users:
                self._selected = (bx, by)
                legal = self._sp_bot.getLegalMoves()
                self.movesBoard = 0
                for m in legal:
                    if m.getX1() == bx and m.getY1() == by:
                        self.movesBoard |= 1 << (m.getX2() + m.getY2()*8)
                self.setPosition(self._sp_bot.getPosition(), [bx, by])
                self.draw(block=False)
        else:
            sx, sy = self._selected
            self._selected = None

            if self.movesBoard & (1 << (bx + by*8)):
                # Valid destination — execute user's move
                move = Move(sx, sy, bx, by)
                gameState = self._sp_bot.makeMove(move, frfr=True)
                self.movesBoard = 0
                self.setPosition(self._sp_bot.getPosition(), [bx, by])
                self.draw(block=False, delay=0.1)

                if gameState in (staleMate, drawRep, blackWin, whiteWin):
                    self._sp_end_game(gameState)
                    return

                # Bot responds
                self._bot_thinking = True
                bot_move, depth, elapsed, evaluation = self._sp_bot.botMove(depthLimit=99, timeLimit=TIME_LIMIT)
                self._bot_thinking = False
                self.bot2Depth = depth
                self.bot2Evaluation = evaluation
                self.avgMoveTime = elapsed

                if bot_move is None:
                    result = blackWin if self._sp_user_white else whiteWin
                    self._sp_end_game(result)
                    return

                self.setPosition(self._sp_bot.getPosition(), [bot_move.getX2(), bot_move.getY2()])
                self.draw(block=False, delay=0.1)

                # Check if user now has no legal moves
                user_moves = self._sp_bot.getLegalMoves()
                if len(user_moves) == 0:
                    in_check = self._sp_bot._kingChecked(self._sp_user_white)
                    result = (whiteWin if not self._sp_user_white else blackWin) if in_check else staleMate
                    self._sp_end_game(result)
            else:
                # Clicked elsewhere — deselect
                self.movesBoard = 0
                self.setPosition(self._sp_bot.getPosition())
                self.draw(block=False)

    def _sp_end_game(self, gameState):
        self._game_over = True
        if gameState == whiteWin:
            if self._sp_user_white:
                print("You win! (white wins)")
                self.bot1Wins += 1
            else:
                print("Bot wins! (white wins)")
                self.bot2Wins += 1
        elif gameState == blackWin:
            if not self._sp_user_white:
                print("You win! (black wins)")
                self.bot1Wins += 1
            else:
                print("Bot wins! (black wins)")
                self.bot2Wins += 1
        elif gameState == staleMate:
            print("Draw by stalemate!")
            self.draws += 1
        elif gameState == drawRep:
            print("Draw by repetition!")
            self.draws += 1

        self.draw(block=False, delay=5)

        # Start a new game automatically
        self._sp_bot.setupPieces()
        self._game_over = False
        self.movesBoard = 0
        self._selected = None
        self.setPosition(self._sp_bot.getPosition())
        self.draw(block=False)

        # If user plays black, bot makes the opening move
        if not self._sp_user_white:
            self._sp_bot_move_first()

    def _sp_bot_move_first(self):
        self._bot_thinking = True
        bot_move, depth, elapsed, evaluation = self._sp_bot.botMove(depthLimit=99, timeLimit=TIME_LIMIT)
        self._bot_thinking = False
        self.bot2Depth = depth
        self.bot2Evaluation = evaluation
        self.avgMoveTime = elapsed
        if bot_move is not None:
            self.setPosition(self._sp_bot.getPosition(), [bot_move.getX2(), bot_move.getY2()])
        self.draw(block=False)


# ---------------------------------------------------------------------------
# Mode selection
# ---------------------------------------------------------------------------

print("=== chessViewer ===")
print("  1) Bot1 vs Bot2  (watch)")
print("  2) Play vs Bot2  (interactive)")
mode = input("Select mode [1/2]: ").strip()

ms_input = input("Computing time per move in ms [default 1000]: ").strip()
try:
    TIME_LIMIT = int(ms_input) / 1000 if ms_input else 1.0
except ValueError:
    TIME_LIMIT = 1.0
print(f"Time limit set to {TIME_LIMIT * 1000:.0f} ms per move.")

bot1 = chessBoard1()
bot2 = chessBoard2()
BM = boardManager()

if mode == "2":
    print()
    print("  1) Play as White (you go first)")
    print("  2) Play as Black (bot goes first)")
    color = input("Select color [1/2]: ").strip()
    user_is_white = (color != "2")

    bot2.setupPieces()
    BM.setup_single_player(bot2, user_is_white)
    BM.setPosition(bot2.getPosition())
    BM.draw(block=False)

    if not user_is_white:
        BM._sp_bot_move_first()

    plt.show(block=True)  # hand control to the GUI event loop

else:
    # Bot1 vs Bot2 — infinite loop
    game_num = 0
    while True:
        game_num += 1
        BM.gameNum = game_num

        bot1_plays_white = (game_num % 2 == 1)
        white_bot = bot1 if bot1_plays_white else bot2
        black_bot = bot2 if bot1_plays_white else bot1
        BM.whiteLabel = "bot1" if bot1_plays_white else "bot2"
        BM.blackLabel = "bot2" if bot1_plays_white else "bot1"

        bot1.setupPieces()
        bot2.setupPieces()

        BM.setPosition(white_bot.getPosition())
        BM.draw(block=False, delay=1)

        nrMoves = 0
        gameState = onGoing
        while True:
            move, depth, elapsed, evaluation = white_bot.botMove(depthLimit=99, timeLimit=TIME_LIMIT)
            BM.avgMoveTime = elapsed
            if bot1_plays_white:
                BM.bot1Depth = depth; BM.bot1Evaluation = evaluation
            else:
                BM.bot2Depth = depth; BM.bot2Evaluation = evaluation
            if move is None:
                BM.bot2Wins += 1 if bot1_plays_white else 0
                BM.bot1Wins += 1 if not bot1_plays_white else 0
                break
            BM.setPosition(white_bot.getPosition(), [move.getX2(), move.getY2()])
            BM.draw(block=False, delay=0.1)

            gameState = black_bot.makeMove(move, frfr=True)
            if gameState in (staleMate, drawRep):
                BM.draws += 1
                break

            move, depth, elapsed, evaluation = black_bot.botMove(depthLimit=99, timeLimit=TIME_LIMIT)
            BM.avgMoveTime = elapsed
            if bot1_plays_white:
                BM.bot2Depth = depth; BM.bot2Evaluation = evaluation
            else:
                BM.bot1Depth = depth; BM.bot1Evaluation = evaluation
            if move is None:
                BM.bot1Wins += 1 if bot1_plays_white else 0
                BM.bot2Wins += 1 if not bot1_plays_white else 0
                break
            BM.setPosition(black_bot.getPosition(), [move.getX2(), move.getY2()])
            BM.draw(block=False, delay=0.1)

            nrMoves += 2
            gameState = white_bot.makeMove(move, frfr=True)

            if white_bot.getPosition() != black_bot.getPosition():
                print(f"[G{game_num:02d}] Position mismatch after move {nrMoves}!")

            if gameState in (staleMate, drawRep) or nrMoves >= 200:
                BM.draws += 1
                break

        BM.draw(block=False, delay=5)
