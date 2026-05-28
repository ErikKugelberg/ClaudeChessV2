# -*- coding: utf-8 -*-
"""
Generate a PDF report for the ClaudeChessV2 project.
Usage: python generate_report.py
Output: ClaudeChessV2_Report.pdf
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import textwrap

# ── Colour palette ──────────────────────────────────────────────────────────
BG       = '#1a1a2e'
ACCENT   = '#e94560'
GOLD     = '#f5a623'
TEAL     = '#0f3460'
LT       = '#eaeaea'
GREY     = '#555577'
GREEN    = '#4caf50'
RED      = '#f44336'
BLUE     = '#2196f3'
PURPLE   = '#9c27b0'

# ── Helpers ──────────────────────────────────────────────────────────────────
def new_fig(bg=BG):
    fig = plt.figure(figsize=(11, 8.5), facecolor=bg)
    return fig

def title_text(ax, text, y=0.92, size=28, color=ACCENT):
    ax.text(0.5, y, text, transform=ax.transAxes,
            ha='center', va='top', fontsize=size, color=color,
            fontweight='bold', fontfamily='monospace')

def body_text(ax, text, x=0.08, y=0.82, size=11, color=LT, wrap=90):
    lines = []
    for para in text.split('\n'):
        if para.strip() == '':
            lines.append('')
        else:
            lines.extend(textwrap.wrap(para, wrap))
    ax.text(x, y, '\n'.join(lines), transform=ax.transAxes,
            ha='left', va='top', fontsize=size, color=color,
            fontfamily='monospace', linespacing=1.6)

def section_label(ax, text, x=0.08, y=0.88, size=14, color=GOLD):
    ax.text(x, y, text, transform=ax.transAxes,
            ha='left', va='top', fontsize=size, color=color,
            fontweight='bold', fontfamily='monospace')

def hline(ax, y=0.87, color=ACCENT, lw=1.5):
    ax.plot([0, 1], [y, y], color=color, linewidth=lw,
            transform=ax.transAxes, clip_on=False)

def hide_axes(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis('off')


# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — TITLE
# ════════════════════════════════════════════════════════════════════════════
def page_title(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    # Background rectangles
    ax.add_patch(patches.Rectangle((0, 0.55), 1, 0.45, color=TEAL, zorder=0))
    ax.add_patch(patches.Rectangle((0, 0),    1, 0.55, color=BG,   zorder=0))

    # Chessboard mini-graphic
    sq = 0.042
    ox, oy = 0.38, 0.60
    for r in range(8):
        for c in range(8):
            col = '#eeeed2' if (r+c) % 2 == 0 else '#769656'
            ax.add_patch(patches.Rectangle((ox+c*sq, oy+r*sq), sq, sq,
                                           color=col, zorder=1))
    ax.add_patch(patches.Rectangle((ox-0.002, oy-0.002),
                                   8*sq+0.004, 8*sq+0.004,
                                   fill=False, edgecolor=GOLD, lw=2, zorder=2))

    ax.text(0.5, 0.94, 'ClaudeChessV2', ha='center', va='top',
            fontsize=40, color=GOLD, fontweight='bold', fontfamily='monospace',
            transform=ax.transAxes)
    ax.text(0.5, 0.87, 'A Python Chess Engine — Development Report',
            ha='center', va='top', fontsize=16, color=LT,
            fontfamily='monospace', transform=ax.transAxes)

    ax.text(0.5, 0.52, 'Contents', ha='center', va='top',
            fontsize=18, color=GOLD, fontweight='bold',
            fontfamily='monospace', transform=ax.transAxes)

    toc = [
        '1.  Project Overview & Architecture',
        '2.  Board Representation',
        '3.  Move Generation & Legal-Move Checking',
        '4.  Negamax Alpha-Beta Search',
        '5.  Iterative Deepening',
        '6.  Move Ordering (MVV-LVA, Killers, TT Hash Move)',
        '7.  Transposition Table',
        '8.  Null Move Pruning',
        '9.  Late Move Reductions (LMR)',
        '10. Stand-Pat Capture Filter (Horizon Effect)',
        '11. Evaluation Function',
        '12. Optimisation Journey & Win-Rate Progression',
        '13. What Was Tried & Reverted',
        '14. Current State & Next Steps',
    ]
    for i, line in enumerate(toc):
        ax.text(0.24, 0.45 - i*0.029, line, ha='left', va='top',
                fontsize=11, color=LT, fontfamily='monospace',
                transform=ax.transAxes)

    ax.text(0.5, 0.03, 'Erik Kugelberg  •  2026',
            ha='center', va='bottom', fontsize=10, color=GREY,
            fontfamily='monospace', transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — PROJECT OVERVIEW & ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════
def page_overview(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '1. Project Overview & Architecture')
    hline(ax, 0.87)

    body_text(ax, """\
ClaudeChessV2 is a two-bot Python chess engine where bot2 is iteratively
improved against a frozen baseline (bot1).  Both bots expose the same
public interface so the benchmark harness (botFighter.py) can pit them
against each other automatically.\
""", y=0.85, size=11)

    # Architecture box diagram
    boxes = [
        (0.05, 0.62, 0.20, 0.12, 'utils.py', 'Move · LimitedSizeDict\npiece constants', TEAL),
        (0.32, 0.62, 0.20, 0.12, 'bot1.py', 'Frozen baseline\nboard.copy() undo', GREY),
        (0.58, 0.62, 0.20, 0.12, 'bot2.py', 'Active engine\nincremental undo', ACCENT),
        (0.32, 0.42, 0.20, 0.12, 'botFighter.py', 'Benchmark harness\n10 games / 0.5 s', TEAL),
        (0.58, 0.42, 0.20, 0.12, 'chessViewer.py', 'GUI (matplotlib)\nplay vs bot2', TEAL),
        (0.05, 0.42, 0.20, 0.12, 'sfcompare.py', 'Stockfish debug\nscore_all_moves()', PURPLE),
    ]
    for bx, by, bw, bh, title, sub, color in boxes:
        ax.add_patch(FancyBboxPatch((bx, by), bw, bh,
                     boxstyle='round,pad=0.01', facecolor=color,
                     edgecolor=GOLD, linewidth=1.5, transform=ax.transAxes))
        ax.text(bx+bw/2, by+bh*0.65, title, ha='center', va='center',
                fontsize=11, color=LT, fontweight='bold',
                fontfamily='monospace', transform=ax.transAxes)
        ax.text(bx+bw/2, by+bh*0.25, sub, ha='center', va='center',
                fontsize=8.5, color='#cccccc', fontfamily='monospace',
                transform=ax.transAxes)

    # Arrows
    arrowprops = dict(arrowstyle='->', color=GOLD, lw=1.5)
    def arrow(ax, x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=arrowprops)

    arrow(ax, 0.25, 0.68, 0.32, 0.68)   # utils → bot1
    arrow(ax, 0.25, 0.68, 0.58, 0.68)   # utils → bot2
    arrow(ax, 0.42, 0.62, 0.42, 0.54)   # bot1 → botFighter
    arrow(ax, 0.68, 0.62, 0.68, 0.54)   # bot2 → chessViewer
    arrow(ax, 0.58, 0.48, 0.52, 0.48)   # botFighter → bot2
    arrow(ax, 0.25, 0.48, 0.32, 0.48)   # sfcompare → botFighter

    body_text(ax, """\
Key design decisions:
  • Both bots share the same interface: setupPieces(), makeMove(), botMove(),
    getLegalMoves(), getPosition(), _kingChecked()
  • bot1 is NEVER modified — it is the immutable baseline for all win-rate tests
  • After each bot2 move, botFighter syncs bot1 via makeMove(move, frfr=True)
    and asserts both bots see the same position
  • Benchmark protocol: 10 games, 0.5 s per move, --workers 1 (sequential)\
""", y=0.38, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — BOARD REPRESENTATION
# ════════════════════════════════════════════════════════════════════════════
def page_board(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '2. Board Representation')
    hline(ax, 0.87)

    body_text(ax, """\
The board is a flat Python list of 64 integers, indexed as board[y*8 + x].
Origin (index 0) is the bottom-left corner — White's a1 square.\
""", y=0.85, size=11)

    # Draw the board
    piece_syms = {
        1:'♙', 2:'♘', 3:'♗', 4:'♖', 5:'♛', 6:'♔',
        8:'♟', 9:'♞', 10:'♝', 11:'♜', 12:'♛', 13:'♚', 0:''
    }
    starting = [
        4,2,3,5,6,3,2,4,   # y=0: white pieces
        1,1,1,1,1,1,1,1,   # y=1: white pawns
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        8,8,8,8,8,8,8,8,   # y=6: black pawns
        11,9,10,12,13,10,9,11, # y=7: black pieces
    ]
    sq = 0.058
    ox, oy = 0.04, 0.18
    for y in range(8):
        for x in range(8):
            light = (x + y) % 2 == 0
            bg_sq = '#eeeed2' if light else '#769656'
            ax.add_patch(patches.Rectangle(
                (ox + x*sq, oy + y*sq), sq, sq,
                color=bg_sq, transform=ax.transAxes, zorder=1))
            idx = y*8 + x
            piece = starting[idx]
            sym = piece_syms.get(piece, '')
            if sym:
                col = 'white' if piece <= 6 else '#1a1a2e'
                ax.text(ox + x*sq + sq/2, oy + y*sq + sq/2, sym,
                        ha='center', va='center', fontsize=14,
                        color=col, fontweight='bold',
                        transform=ax.transAxes, zorder=2)
            # index label
            ax.text(ox + x*sq + 0.003, oy + y*sq + 0.003, str(idx),
                    ha='left', va='bottom', fontsize=5.5,
                    color='#888888', transform=ax.transAxes, zorder=3)
    # rank/file labels
    files = 'abcdefgh'
    for x in range(8):
        ax.text(ox + x*sq + sq/2, oy - 0.022, files[x],
                ha='center', va='top', fontsize=9, color=LT,
                transform=ax.transAxes)
    for y in range(8):
        ax.text(ox - 0.018, oy + y*sq + sq/2, str(y+1),
                ha='right', va='center', fontsize=9, color=LT,
                transform=ax.transAxes)
    ax.add_patch(patches.Rectangle((ox-0.003, oy-0.003),
                                   8*sq+0.006, 8*sq+0.006,
                                   fill=False, edgecolor=GOLD, lw=2,
                                   transform=ax.transAxes, zorder=4))

    # Piece constants table
    rows = [
        ('empty', '0', '—'),
        ('Wpawn', '1', '100 cp'),
        ('Wknight','2','300 cp'),
        ('Wbishop','3','300 cp'),
        ('Wrook',  '4','500 cp'),
        ('Wqueen', '5','900 cp'),
        ('Wking',  '6','—'),
        ('pieceDivider','7','—'),
        ('Bpawn',  '8','100 cp'),
        ('Bknight','9','300 cp'),
        ('Bbishop','10','300 cp'),
        ('Brook',  '11','500 cp'),
        ('Bqueen', '12','900 cp'),
        ('Bking',  '13','—'),
    ]
    tx = 0.57
    ax.text(tx, 0.83, 'Piece Constants', ha='left', fontsize=13,
            color=GOLD, fontweight='bold', fontfamily='monospace',
            transform=ax.transAxes)
    hdrs = ['Name', 'Value', 'Material']
    for i, h in enumerate(hdrs):
        ax.text(tx + i*0.13, 0.79, h, ha='left', fontsize=10,
                color=ACCENT, fontweight='bold', fontfamily='monospace',
                transform=ax.transAxes)
    for j, (name, val, mat) in enumerate(rows):
        yy = 0.755 - j*0.035
        clr = '#aaddff' if int(val) <= 6 else '#ffaaaa' if int(val) != 7 else GREY
        for i, cell in enumerate([name, val, mat]):
            ax.text(tx + i*0.13, yy, cell, ha='left', fontsize=9,
                    color=clr, fontfamily='monospace', transform=ax.transAxes)

    body_text(ax, """\
Key insight: piece > pieceDivider (7) means BLACK.
Bitboards (Python integers) are used for move generation
and evaluation — each bit represents one board square.\
""", x=0.57, y=0.25, size=10)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — MOVE GENERATION
# ════════════════════════════════════════════════════════════════════════════
def page_movegen(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '3. Move Generation & Legal-Move Checking')
    hline(ax, 0.87)

    body_text(ax, """\
getLegalMoves() is the most-called function in the engine — hit ~35× per
alpha-beta node during getLegalMoves inside _legalMove checks.\
""", y=0.855, size=11)

    # Flow diagram
    steps = [
        (0.12, 0.70, '_getMoves(x,y)', 'Builds a bitboard of candidate\ndestinations for each piece'),
        (0.12, 0.555,'bit extraction', 'while bb: bit=bb&-bb; bb^=bit\nO(targets) not O(64)'),
        (0.12, 0.41, '_legalMove()', 'Applies move, checks _kingChecked,\nundoes move  (fast incremental undo)'),
        (0.12, 0.265,'legal moves list', 'Sets move.isAttacking flag\nif destination is occupied'),
    ]
    for bx, by, title, desc in steps:
        ax.add_patch(FancyBboxPatch((bx, by), 0.34, 0.10,
                     boxstyle='round,pad=0.01', facecolor=TEAL,
                     edgecolor=ACCENT, linewidth=1.5, transform=ax.transAxes))
        ax.text(bx+0.17, by+0.072, title, ha='center', va='center',
                fontsize=11, color=GOLD, fontweight='bold',
                fontfamily='monospace', transform=ax.transAxes)
        ax.text(bx+0.17, by+0.028, desc, ha='center', va='center',
                fontsize=9, color=LT, fontfamily='monospace',
                transform=ax.transAxes)

    # Arrows between steps
    for y_from, y_to in [(0.70, 0.655), (0.555, 0.51), (0.41, 0.365)]:
        ax.annotate('', xy=(0.29, y_to), xytext=(0.29, y_from),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.5))

    # _kingChecked box
    ax.add_patch(FancyBboxPatch((0.60, 0.42), 0.34, 0.28,
                 boxstyle='round,pad=0.01', facecolor='#1e1e3e',
                 edgecolor=GREEN, linewidth=1.5, transform=ax.transAxes))
    ax.text(0.77, 0.685, '_kingChecked() — Ray Tracing', ha='center',
            fontsize=11, color=GREEN, fontweight='bold',
            fontfamily='monospace', transform=ax.transAxes)
    rays = [
        '• 4 rook rays  (↑↓←→)  — rook / queen threats',
        '• 4 bishop rays (↗↘↙↖) — bishop / queen threats',
        '• 8 knight jumps       — knight threats',
        '• 2 pawn squares       — pawn diagonal attacks',
        '• 8 king squares       — adjacent king',
    ]
    for i, r in enumerate(rays):
        ax.text(0.62, 0.645 - i*0.038, r, ha='left', fontsize=9,
                color=LT, fontfamily='monospace', transform=ax.transAxes)

    ax.text(0.77, 0.435, '~4× faster than scanning all enemy pieces',
            ha='center', fontsize=9, color=GREY,
            fontfamily='monospace', transform=ax.transAxes)

    body_text(ax, """\
Move struct: 16-bit int packing x1,y1,x2,y2,isAttacking via bit-shifts.
Comparison (==) uses __eq__ on the packed int — killers work correctly.\
""", y=0.23, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 5 — NEGAMAX ALPHA-BETA
# ════════════════════════════════════════════════════════════════════════════
def page_negamax(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '4. Negamax Alpha-Beta Search')
    hline(ax, 0.87)

    # Tree diagram — simplified 3-ply example
    # Nodes: (x, y, label, val, pruned)
    node_r = 0.030
    nodes = {
        'root':  (0.50, 0.76, 'root', None,  False),
        'A':     (0.22, 0.60, 'A',    None,  False),
        'B':     (0.78, 0.60, 'B',    None,  True),
        'A1':    (0.10, 0.44, 'A1',   '+1.2',False),
        'A2':    (0.22, 0.44, 'A2',   '+0.8',False),
        'A3':    (0.34, 0.44, 'A3',   '+2.0',False),
        'B1':    (0.70, 0.44, 'B1',   '?',   True),
        'B2':    (0.86, 0.44, 'B2',   '?',   True),
    }
    edges = [
        ('root','A'), ('root','B'),
        ('A','A1'), ('A','A2'), ('A','A3'),
        ('B','B1'), ('B','B2'),
    ]
    def nc(k): return (nodes[k][0], nodes[k][1])

    for k1, k2 in edges:
        x1,y1 = nc(k1); x2,y2 = nc(k2)
        pruned = nodes[k2][4]
        col = GREY if pruned else GOLD
        style = '--' if pruned else '-'
        ax.annotate('', xy=(x2, y2+node_r), xytext=(x1, y1-node_r),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle='->', color=col,
                                   lw=1.5, linestyle=style))

    for k, (nx, ny, label, val, pruned) in nodes.items():
        col = GREY if pruned else (ACCENT if k=='root' else (TEAL if not pruned else GREY))
        ring = GREY if pruned else GOLD
        circle = plt.Circle((nx, ny), node_r, color=col,
                             transform=ax.transAxes, zorder=3)
        ax.add_patch(circle)
        ring_c = plt.Circle((nx, ny), node_r+0.005, fill=False,
                             edgecolor=ring, lw=1.5,
                             transform=ax.transAxes, zorder=4)
        ax.add_patch(ring_c)
        ax.text(nx, ny+0.001, label, ha='center', va='center',
                fontsize=9, color=LT, fontweight='bold',
                fontfamily='monospace', transform=ax.transAxes, zorder=5)
        if val:
            ax.text(nx, ny-node_r-0.022, val, ha='center', va='top',
                    fontsize=8.5, color=GREEN if not pruned else GREY,
                    fontfamily='monospace', transform=ax.transAxes)

    # Prune bracket
    ax.add_patch(patches.Rectangle((0.62, 0.36), 0.32, 0.30,
                 fill=False, edgecolor=RED, lw=2, linestyle='--',
                 transform=ax.transAxes))
    ax.text(0.78, 0.34, 'β-cutoff: pruned (never evaluated)',
            ha='center', fontsize=9, color=RED,
            fontfamily='monospace', transform=ax.transAxes)

    # Alpha-beta labels
    ax.text(0.50, 0.80, 'α=−∞  β=+∞', ha='center', fontsize=9,
            color=GREY, fontfamily='monospace', transform=ax.transAxes)
    ax.text(0.22, 0.64, 'α=−∞  β=+∞', ha='center', fontsize=9,
            color=GREY, fontfamily='monospace', transform=ax.transAxes)
    ax.text(0.78, 0.64, 'α=1.2  β=+∞', ha='center', fontsize=9,
            color=RED, fontfamily='monospace', transform=ax.transAxes)

    body_text(ax, """\
Negamax convention: score is always from the CURRENT player's perspective.
Recursive call passes (-β, -α) and negates the returned score.  This
means a single search function handles both colours correctly.\
""", y=0.30, size=10.5)

    body_text(ax, """\
Alpha-beta pruning: when a move is found that exceeds β (the opponent's
best already guaranteed), further siblings are skipped — the opponent
would never allow this branch.  In a perfectly ordered tree, alpha-beta
reduces nodes from O(b^d) to O(b^(d/2)), effectively doubling the
searchable depth for the same budget.\
""", y=0.21, size=10.5)

    body_text(ax, """\
Timeout sentinel: when time expires, _stop_search=True is set and every
ancestor returns -inf.  The caller discards the incomplete result and
keeps the last COMPLETE depth's move.  This prevents -inf being negated
to +inf and corrupting the best-move selection.\
""", y=0.11, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 6 — ITERATIVE DEEPENING
# ════════════════════════════════════════════════════════════════════════════
def page_id(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '5. Iterative Deepening (IDA*)')
    hline(ax, 0.87)

    body_text(ax, """\
Instead of searching to a fixed depth, bot2 repeatedly searches to
increasing depths (d=2, 3, 4, …) until the time limit is hit.
The last complete depth's result is used as the final move.\
""", y=0.85, size=11)

    # Timeline graphic
    ax.add_patch(patches.FancyArrowPatch(
        (0.08, 0.65), (0.92, 0.65),
        transform=ax.transAxes,
        arrowstyle='->', color=LT, linewidth=2))
    ax.text(0.92, 0.67, 'Time →', ha='left', fontsize=10,
            color=LT, fontfamily='monospace', transform=ax.transAxes)

    depths  = [2, 3, 4, 5, 6, 7]
    x_start = [0.09, 0.14, 0.22, 0.37, 0.55, 0.68]
    x_end   = [0.13, 0.21, 0.36, 0.54, 0.67, 0.91]
    colors  = [TEAL]*5 + [GREY]
    labels  = [f'd={d}' for d in depths]
    labels[-1] = 'd=7\n(incomplete)'

    for xs, xe, col, lbl in zip(x_start, x_end, colors, labels):
        ax.add_patch(patches.Rectangle(
            (xs, 0.59), xe-xs, 0.09,
            facecolor=col, edgecolor=GOLD, lw=1, transform=ax.transAxes))
        ax.text((xs+xe)/2, 0.635, lbl, ha='center', va='center',
                fontsize=9, color=LT, fontfamily='monospace',
                transform=ax.transAxes)

    ax.plot([0.88, 0.88], [0.55, 0.73], color=RED, lw=2,
            linestyle='--', transform=ax.transAxes, clip_on=False)
    ax.text(0.88, 0.74, 'time\nlimit', ha='center', fontsize=9,
            color=RED, fontfamily='monospace', transform=ax.transAxes)

    ax.annotate('', xy=(0.67, 0.55), xytext=(0.67, 0.59),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=2))
    ax.text(0.67, 0.52, 'Best move\n(d=6 result)', ha='center',
            fontsize=9.5, color=GREEN, fontfamily='monospace',
            transform=ax.transAxes)

    body_text(ax, """\
Why iterative deepening beats a single fixed depth:
  • The time budget is used optimally — you always have an answer ready
  • Move ordering from depth d improves the search at depth d+1, so
    early depths pay for themselves by pruning deeper ones more
  • TT is cleared at each depth to avoid parity contamination (odd-depth
    evals vs even-depth evals differ by ~86 cp due to the tempo bonus;
    stale entries from d=5 returned at d=6 cause wrong move choices)
  • Move ordering is preserved across depths via the sorted moves list
    from the previous iteration, so depth-d+1 searches the best move first\
""", y=0.46, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 7 — MOVE ORDERING
# ════════════════════════════════════════════════════════════════════════════
def page_ordering(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '6. Move Ordering')
    hline(ax, 0.87)

    # Priority pyramid / table
    prio = [
        (2_000_000, 'TT Hash Move',    GOLD,   'Best move from TT at same or higher depth'),
        (1_000_000, 'MVV-LVA Captures',ACCENT, '1M + 10×victim_val − attacker_val'),
        (  900_000, 'Killer #1',       GREEN,  'Quiet move that caused β-cutoff at this depth'),
        (  800_000, 'Killer #2',       GREEN,  'Second killer move at this depth'),
        (      '*', 'History Heuristic',BLUE,  'Quiet moves: score += depth² on each β-cutoff'),
    ]
    hdrs = ['Priority', 'Category', 'Score / Rule']
    ys = [0.81, 0.77, 0.73, 0.69, 0.65, 0.61]
    xs = [0.07, 0.23, 0.42]
    for i, (h, x) in enumerate(zip(hdrs, xs)):
        ax.text(x, ys[0], h, ha='left', fontsize=11, color=ACCENT,
                fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
    ax.plot([0.05, 0.95], [ys[1]-0.005, ys[1]-0.005], color=ACCENT,
            lw=1, transform=ax.transAxes, clip_on=False)
    for i, (score, cat, col, desc) in enumerate(prio):
        y = ys[i+1]
        ax.text(xs[0], y, str(score), ha='left', fontsize=10,
                color=col, fontfamily='monospace', transform=ax.transAxes)
        ax.text(xs[1], y, cat, ha='left', fontsize=10,
                color=col, fontweight='bold', fontfamily='monospace',
                transform=ax.transAxes)
        ax.text(xs[2], y, desc, ha='left', fontsize=9.5,
                color=LT, fontfamily='monospace', transform=ax.transAxes)

    body_text(ax, """\
MVV-LVA (Most Valuable Victim — Least Valuable Attacker):
  Captures are sorted so high-value victims captured by low-value pieces
  come first.  This ensures winning exchanges are explored before losing
  ones, dramatically improving early β-cutoffs.

  Example:  Qxp → score = 1M + 10×100 − 900 = 1,000,100
            NxQ → score = 1M + 10×900 − 300 = 1,008,700  ← searched 1st\
""", y=0.54, size=10.5)

    body_text(ax, """\
Killer Move Heuristic:
  When a quiet move causes a β-cutoff at depth D, it is stored as a
  "killer" for that depth.  On sibling nodes (same depth, different
  position), killers are tried before other quiet moves.  Two killers are
  stored per depth level (128-slot array, reset each botMove() call).
  Killers increased avg search depth from 6.78 → 7.4.\
""", y=0.36, size=10.5)

    body_text(ax, """\
TT Hash Move:
  If the transposition table has an entry for the current position (even
  at a lower depth), the stored best move is tried first with priority
  2,000,000.  This is the single highest-impact ordering improvement.\
""", y=0.20, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 8 — TRANSPOSITION TABLE
# ════════════════════════════════════════════════════════════════════════════
def page_tt(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '7. Transposition Table')
    hline(ax, 0.87)

    body_text(ax, """\
Many positions are reachable via different move orders (transpositions).
Without caching, the same position is evaluated multiple times.
The TT stores evaluation results so repeated positions are instant lookups.\
""", y=0.855, size=11)

    # Key diagram
    ax.add_patch(FancyBboxPatch((0.06, 0.62), 0.88, 0.14,
                 boxstyle='round,pad=0.01', facecolor=TEAL,
                 edgecolor=GOLD, lw=1.5, transform=ax.transAxes))
    ax.text(0.5, 0.72, 'TT Key  =  (board_hash, whitesMove, rkMoved, enPas_x, enPas_y)',
            ha='center', fontsize=11, color=GOLD, fontweight='bold',
            fontfamily='monospace', transform=ax.transAxes)
    ax.text(0.5, 0.665, 'Encodes full game state — castling rights & en passant prevent stale hits',
            ha='center', fontsize=10, color=LT,
            fontfamily='monospace', transform=ax.transAxes)

    ax.add_patch(FancyBboxPatch((0.06, 0.46), 0.88, 0.10,
                 boxstyle='round,pad=0.01', facecolor=TEAL,
                 edgecolor=ACCENT, lw=1.5, transform=ax.transAxes))
    ax.text(0.5, 0.52, 'TT Value  =  (depth, eval, best_move)',
            ha='center', fontsize=11, color=ACCENT, fontweight='bold',
            fontfamily='monospace', transform=ax.transAxes)
    ax.text(0.5, 0.477, '3-tuple stores the best move for ordering even on partial (depth) hits',
            ha='center', fontsize=10, color=LT,
            fontfamily='monospace', transform=ax.transAxes)

    body_text(ax, """\
Lookup logic:
  if stored_depth >= entry_depth → return stored_eval immediately (full hit)
  else → extract best_move for ordering, continue searching (partial hit)

Implementation: LimitedSizeDict (FIFO eviction at 100,000 entries).
  Capacity was tuned so the TT fills in ~0.5 s without excessive memory.

Critical gotcha — clear TT per iteration, not just per move:
  With iterative deepening, a d=5 entry (odd depth, eval ≈ +0.87) can be
  returned inside a d=6 search (even depth).  Because the tempo bonus flips
  sign each ply, odd/even evals differ by ~86 cp.  Using a d=5 entry at d=6
  produces wrong scores and wrong move choices (e.g. h2h4 instead of e2e4).
  Fix: self._ttable = LimitedSizeDict(...) at the start of each IDA* loop.\
""", y=0.42, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 9 — NULL MOVE PRUNING
# ════════════════════════════════════════════════════════════════════════════
def page_null(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '8. Null Move Pruning')
    hline(ax, 0.87)

    body_text(ax, """\
Null move pruning: if the current player can achieve a β-cutoff even after
SKIPPING their turn entirely, the position is so good that a real move will
also beat β — so the branch is pruned without searching any real moves.\
""", y=0.855, size=11)

    # Flow diagram
    steps_data = [
        (0.10, 0.67, 0.36, 0.10, 'Guard conditions',
         '  remaining > R=2  (≥ 3 plies left)\n  Not in check\n  nonPawnCount > 4  (avoid zugzwang)',
         TEAL, GOLD),
        (0.58, 0.67, 0.36, 0.10, 'Null-move search',
         '  Flip side-to-move\n  Search at depth − 1 − R  (shallow)\n  No consecutive null moves (allow_null=False)',
         TEAL, ACCENT),
        (0.10, 0.50, 0.36, 0.10, 'Prune if null ≥ β',
         '  Return β immediately\n  Skip getLegalMoves entirely\n  → saved nodes increase search depth',
         TEAL, GREEN),
        (0.58, 0.50, 0.36, 0.10, 'Otherwise continue',
         '  Un-flip side-to-move\n  Fall through to normal move loop\n  Normal getLegalMoves + search',
         TEAL, BLUE),
    ]
    for bx, by, bw, bh, title, desc, bg, ec in steps_data:
        ax.add_patch(FancyBboxPatch((bx, by), bw, bh,
                     boxstyle='round,pad=0.01', facecolor=bg,
                     edgecolor=ec, lw=1.5, transform=ax.transAxes))
        ax.text(bx+bw/2, by+bh*0.78, title, ha='center', fontsize=10.5,
                color=ec, fontweight='bold', fontfamily='monospace',
                transform=ax.transAxes)
        ax.text(bx+bw/2, by+bh*0.35, desc, ha='center', fontsize=8.5,
                color=LT, fontfamily='monospace', transform=ax.transAxes)

    arrow = dict(arrowstyle='->', color=GOLD, lw=1.5)
    ax.annotate('', xy=(0.58, 0.72), xytext=(0.46, 0.72),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=arrow)
    ax.annotate('', xy=(0.28, 0.50), xytext=(0.28, 0.67),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5))
    ax.annotate('', xy=(0.76, 0.50), xytext=(0.76, 0.67),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color=BLUE, lw=1.5))

    body_text(ax, """\
Critical placement: null move probe BEFORE getLegalMoves().
  If placed after, every node pays for two getLegalMoves() calls (one
  in the null search branch, one in the normal search). Placing it first
  means pruned nodes skip getLegalMoves entirely — the whole point.

Zugzwang guard: in king-and-pawn endgames, passing can be strictly worse
  than moving.  The nonPawnCount > 4 guard avoids null pruning in these
  positions.  nonPawnCount is tracked incrementally (decremented on
  capture, incremented on pawn promotion) to avoid an O(64) loop per node.\
""", y=0.45, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 10 — LMR
# ════════════════════════════════════════════════════════════════════════════
def page_lmr(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '9. Late Move Reductions (LMR)')
    hline(ax, 0.87)

    body_text(ax, """\
With good move ordering, the first few moves at each node are usually the
best.  Moves tried later (high index) are likely weaker and can be searched
at reduced depth.  If the reduced search beats alpha anyway, a full re-search
is done to confirm.\
""", y=0.855, size=11)

    # Move list diagram with reduction markers
    ax.add_patch(FancyBboxPatch((0.06, 0.60), 0.88, 0.18,
                 boxstyle='round,pad=0.01', facecolor='#111133',
                 edgecolor=GREY, lw=1, transform=ax.transAxes))
    moves_shown = [
        (0,  'TT best move',  GOLD,   'full depth'),
        (1,  'killer #1',     GREEN,  'full depth'),
        (2,  'NxQ (capture)', ACCENT, 'full depth'),
        (3,  'Bxf6 (cap)',    ACCENT, 'full depth'),
        (4,  'Nf3 (quiet)',   LT,     'full depth'),
        (5,  'a3 (quiet)',    GREY,   'REDUCED -1 ply'),
        (6,  'h3 (quiet)',    GREY,   'REDUCED -1 ply'),
        (7,  'g4 (quiet)',    GREY,   'REDUCED -1 ply'),
    ]
    for i, (idx, name, col, note) in enumerate(moves_shown):
        y = 0.755 - i*0.018
        ax.text(0.10, y, f'move[{idx}]', ha='left', fontsize=8.5,
                color=col, fontfamily='monospace', transform=ax.transAxes)
        ax.text(0.22, y, name, ha='left', fontsize=8.5,
                color=col, fontfamily='monospace', transform=ax.transAxes)
        ax.text(0.65, y, note, ha='left', fontsize=8.5,
                color=col, fontfamily='monospace', transform=ax.transAxes)

    ax.plot([0.07, 0.93], [0.704, 0.704], color=ACCENT,
            lw=1, linestyle='--', transform=ax.transAxes, clip_on=False)
    ax.text(0.50, 0.696, '← LMR threshold: move_idx ≥ 5, remaining ≥ 3, quiet, not in check →',
            ha='center', fontsize=8.5, color=ACCENT,
            fontfamily='monospace', transform=ax.transAxes)

    body_text(ax, """\
LMR parameters (tuned through benchmarking):
  move_idx ≥ 5       — first 5 moves always searched at full depth
  remaining ≥ 3      — don't reduce near the horizon (tactical positions)
  quiet move only    — captures are never reduced (too tactically important)
  not in check       — check positions need accurate eval, never reduce
  allow_null=False   — prevents null move firing inside a reduced search;
                       cascading LMR+null at depth 4+ was cutting valid lines
                       and caused a drop from 50% → 30% win rate

LMR re-search logic:
  score = probe(remaining-1, −α−1, −α)   # reduced null-window search
  if score > α: score = search(remaining, −β, −α)  # full re-search\
""", y=0.57, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 11 — STAND-PAT / HORIZON EFFECT
# ════════════════════════════════════════════════════════════════════════════
def page_horizon(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '10. Horizon Effect & Stand-Pat Capture Filter')
    hline(ax, 0.87)

    body_text(ax, """\
The horizon effect: a fixed-depth search cannot see what happens the move
after its frontier.  A queen sacrifice (Qxf7) can look great at depth 4
because the recapture (Kxf7) falls beyond the horizon and is invisible.\
""", y=0.855, size=11)

    # Diagram: horizon
    ax.add_patch(FancyArrowPatch(
        (0.06, 0.67), (0.94, 0.67),
        transform=ax.transAxes,
        arrowstyle='->', color=LT, linewidth=1.5))
    depths_labels = ['d=4', 'd=3', 'd=2', 'd=1', 'd=0', 'horizon', 'reply']
    xs_d = [0.10, 0.22, 0.34, 0.46, 0.58, 0.70, 0.86]
    for x, lbl in zip(xs_d, depths_labels):
        is_beyond = x >= 0.70
        col = RED if is_beyond else LT
        ax.text(x, 0.71, lbl, ha='center', fontsize=9.5,
                color=col, fontfamily='monospace', transform=ax.transAxes)
        ax.add_patch(patches.Circle((x, 0.665), 0.012,
                     color=GREY if is_beyond else TEAL,
                     transform=ax.transAxes, zorder=3))
    ax.plot([0.71, 0.71], [0.59, 0.75], color=RED, lw=2,
            linestyle='--', transform=ax.transAxes, clip_on=False)
    ax.text(0.71, 0.59, 'Qxf7 ← "looks great" (+1.5)',
            ha='center', fontsize=9, color=GOLD,
            fontfamily='monospace', transform=ax.transAxes)
    ax.text(0.86, 0.59, 'Kxf7 invisible (−8.0)',
            ha='center', fontsize=9, color=RED,
            fontfamily='monospace', transform=ax.transAxes)

    body_text(ax, """\
Bot2 mitigation: stand-pat + capture filter at remaining=0.

Stand-pat:  At the search horizon (remaining==0), the current player
  can always choose NOT to capture.  The static eval is computed first.
  If eval ≥ β, return immediately (stand-pat β-cutoff).
  Otherwise, alpha = max(alpha, eval) — guarantees we don't evaluate a
  forced bad capture as the baseline.

Capture filter:  After stand-pat, only captures where
    victim_value × 3  ≥  attacker_value
  are searched.  This filters Qxpawn (900 > 100×3) and Rxpawn
  (500 > 300) at the horizon, while allowing NxP, BxP (300=300×1 ≥ 300).

Result: speculative sacrifices that are tactically unsound are suppressed
  without requiring a full recursive quiescence search (which would need
  getLegalMoves + evaluatePosition at every quiescence node — too expensive
  in Python, tested at qdepth 1–4, all produced 0% win rate).\
""", y=0.54, size=10.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 12 — EVALUATION FUNCTION
# ════════════════════════════════════════════════════════════════════════════
def page_eval(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '11. Evaluation Function')
    hline(ax, 0.87)

    components = [
        ('Material',         'Wpawn=100  Wknight=Wbishop=300  Wrook=500  Wqueen=900',   GOLD),
        ('Piece-Square',     'PST per piece type: early-game king hides, late-game\n'
                             '  king centralises; pawns prefer centre; knights/bishops\n'
                             '  prefer board interior; rooks prefer open ranks',          BLUE),
        ('Mobility',         '10 cp per attacked square (_getMoves cnt per piece)\n'
                             '  Encourages active, well-placed pieces',                   GREEN),
        ('Castling rights',  '+100 cp per castling option still available\n'
                             '  Incentivises keeping kingside safety options open',        ACCENT),
        ('King in check',    '+50 cp bonus if own moves attack enemy king\n'
                             '  Detected via WmovesBoard / BmovesBoard bitboards',        RED),
        ('Doubled pawns',    '−50 cp per additional pawn on same file\n'
                             '  Structural weakness, hard to defend',                     GREY),
        ('Isolated pawns',   '−20 cp per pawn with no friendly pawns on adj files\n'
                             '  Cannot be defended by other pawns',                       GREY),
        ('Passed pawns',     '+10/20/35/60/100 cp by rank (ranks 3-7)\n'
                             '  Pawns with no opposing pawns ahead are promotion threats', GREEN),
        ('Rook open file',   '+50 cp fully open file, +25 cp semi-open\n'
                             '  Rooks are maximally active on open files',                ACCENT),
        ('Tempo bonus',      '+17 cp for the side to move\n'
                             '  Calibrated from Stockfish at the starting position',       GOLD),
    ]

    y = 0.83
    for name, desc, col in components:
        ax.text(0.07, y, f'▸ {name}', ha='left', fontsize=10.5,
                color=col, fontweight='bold', fontfamily='monospace',
                transform=ax.transAxes)
        ax.text(0.26, y, desc, ha='left', fontsize=9,
                color=LT, fontfamily='monospace', transform=ax.transAxes)
        y -= 0.073

    body_text(ax, """\
evaluatePosition() returns a WHITE-POSITIVE absolute score.
The caller negates when it is Black's turn (negamax convention).
_getMoves() is called for every piece to count mobility — this is the
dominant cost (~70% of eval time) but is load-bearing; removing it
caused a 10-20% win-rate drop by blinding the engine to mobility.\
""", y=0.055, size=9.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 13 — OPTIMISATION JOURNEY
# ════════════════════════════════════════════════════════════════════════════
def page_journey(pdf):
    fig = new_fig()
    ax_main = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax_main)

    title_text(ax_main, '12. Optimisation Journey & Win-Rate Progression')
    hline(ax_main, 0.87)

    # Bar chart of win rates
    ax = fig.add_axes([0.08, 0.28, 0.88, 0.56])
    ax.set_facecolor('#111122')

    milestones = [
        ('Baseline\n(bot1 vs bot1)',     50,  GREY),
        ('Incremental undo\n(UndoRecord)',42,  TEAL),
        ('Ray-trace\n_kingChecked',      60,  BLUE),
        ('Bit extraction\ngetLegalMoves',62,  BLUE),
        ('Killer moves',                 65,  GREEN),
        ('TT hash-move\nordering',       70,  GREEN),
        ('Eval improvements\n(PP,rooks,iso)',72, GOLD),
        ('LMR tuning\n(idx≥5,rem≥3)',   75,  GOLD),
        ('Remove aspiration\n+clear TT', 85,  ACCENT),
        ('Horizon filter\nstand-pat',    90,  ACCENT),
        ('findBestMove\nstrict-improve', 70,  RED),
    ]
    names  = [m[0] for m in milestones]
    rates  = [m[1] for m in milestones]
    colors = [m[2] for m in milestones]

    xs = np.arange(len(names))
    bars = ax.bar(xs, rates, color=colors, edgecolor='#333355', width=0.7)
    ax.axhline(50, color=GREY, lw=1, linestyle='--', alpha=0.5)
    ax.set_xlim(-0.5, len(names)-0.5)
    ax.set_ylim(0, 110)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, fontsize=7, color=LT, fontfamily='monospace',
                       rotation=15, ha='right')
    ax.set_ylabel('Win rate vs bot1 (%)', color=LT, fontsize=10,
                  fontfamily='monospace')
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0%','25%','50%','75%','100%'],
                       color=LT, fontsize=9, fontfamily='monospace')
    ax.tick_params(colors=LT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GREY)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.5,
                f'{rate}%', ha='center', fontsize=8, color=LT,
                fontfamily='monospace')

    ax_main.text(0.5, 0.22,
        'Note: last bar (strict-improve fix) is stable at ~70% ± 19 pp CI (10-game sample).\n'
        'The 90% peak was a 10-game sample in optimal conditions; all are within each other\'s CI.',
        ha='center', fontsize=9, color=GREY,
        fontfamily='monospace', transform=ax_main.transAxes)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 14 — WHAT WAS TRIED & REVERTED
# ════════════════════════════════════════════════════════════════════════════
def page_reverted(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '13. What Was Tried & Reverted')
    hline(ax, 0.87)

    items = [
        ('Quiescence Search\n(3 attempts)',
         'getLegalMoves() + evaluatePosition() called at every quiescence\n'
         'node starves the main search of time.  Tested at qdepth 1-4;\n'
         'all produced 0% win rate.  Needs faster eval to be viable.',
         RED, '✗'),
        ('Aspiration Windows',
         '±50 cp window always fails: ~86 cp parity oscillation between\n'
         'odd/even depths causes fail-high on every attempt → 2× work.\n'
         'Worse: the failed narrow search contaminates the TT with cutoff\n'
         'values; the full retry uses them as exact, causing wrong moves.',
         RED, '✗'),
        ('Proper TT Node Types\n(exact/lower/upper)',
         'Correct types cause more nodes (tight bounds → continue searching\n'
         'instead of returning).  The "incorrect" TT (all entries as exact)\n'
         'provides aggressive cutoffs that are NET BENEFICIAL in Python.\n'
         'Result: 0% wins in first 2 games with proper node types.',
         RED, '✗'),
        ('PVS (Principal\nVariation Search)',
         'Each recursive call costs ~0.1–0.5 ms in Python.  PVS doubles\n'
         'calls for moves 1+.  Overhead exceeds node savings.\n'
         'Result: 30% win rate (down from 85% baseline).',
         RED, '✗'),
        ('Futility Pruning\n(remaining=1)',
         'Unsound without quiescence search: static eval at depth-1 is not\n'
         'a reliable lower bound when captures are still available.\n'
         'Two variants tested (with/without stand-pat): both caused 20-40%\n'
         'win rate regression.',
         RED, '✗'),
        ('boardLookupMap\n(eval cache)',
         'Cache key omitted whitesMove & en passant → stale hits.\n'
         'TT already handles this correctly; boardLookupMap was entirely\n'
         'redundant and buggy. Removed cleanly.',
         GREY, '✗'),
    ]
    y = 0.82
    for name, desc, col, icon in items:
        ax.text(0.04, y, icon, ha='left', fontsize=14, color=col,
                fontfamily='monospace', transform=ax.transAxes)
        ax.text(0.085, y, name, ha='left', fontsize=10, color=col,
                fontweight='bold', fontfamily='monospace',
                transform=ax.transAxes)
        ax.text(0.26, y-0.005, desc, ha='left', fontsize=8.5,
                color=LT, fontfamily='monospace', transform=ax.transAxes)
        y -= 0.125

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 15 — CURRENT STATE & NEXT STEPS
# ════════════════════════════════════════════════════════════════════════════
def page_next(pdf):
    fig = new_fig()
    ax  = fig.add_axes([0, 0, 1, 1])
    hide_axes(ax)

    title_text(ax, '14. Current State & Next Steps')
    hline(ax, 0.87)

    # Performance box
    ax.add_patch(FancyBboxPatch((0.05, 0.70), 0.88, 0.14,
                 boxstyle='round,pad=0.01', facecolor=TEAL,
                 edgecolor=GOLD, lw=1.5, transform=ax.transAxes))
    stats = [
        ('Win rate vs bot1', '~70%  (±19 pp, n=10, sequential, 0.5 s/move)'),
        ('Avg search depth',  'bot2: 6–8 ply   bot1: 4–5 ply'),
        ('Nodes/move',        'bot2: ~2,000     bot1: ~240,000  (UndoRecord vs copy)'),
        ('Blunders/game',     'bot2 ≈ bot1 (~7 per game) — tactical horizon still visible'),
    ]
    for i, (label, val) in enumerate(stats):
        y = 0.80 - i * 0.028
        ax.text(0.09, y, label + ':', ha='left', fontsize=10,
                color=GOLD, fontweight='bold', fontfamily='monospace',
                transform=ax.transAxes)
        ax.text(0.35, y, val, ha='left', fontsize=10,
                color=LT, fontfamily='monospace', transform=ax.transAxes)

    body_text(ax, 'Next steps — ordered by expected impact:', y=0.665,
              size=12, color=ACCENT)

    next_items = [
        ('★★★★★', 'Speed up evaluatePosition()',
         'Replace _getMoves()-based mobility counting with precomputed\n'
         '  bitboard attack tables (lookup per piece type × square).\n'
         '  This reduces eval from O(pieces × moves) to O(pieces) and\n'
         '  is the prerequisite for viable quiescence search.'),
        ('★★★★★', 'Full Quiescence Search',
         'Once eval is fast enough, add recursive _quiesce(α, β) with\n'
         '  stand-pat — search all captures until a "quiet" position is\n'
         '  reached before returning static eval.  Eliminates the horizon\n'
         '  effect and will dramatically reduce blunder rate.'),
        ('★★★☆☆', 'Evaluation improvements',
         'Bishop pair (+30 cp), king safety (penalise open files near\n'
         '  king, pawn shield), connected rooks.  Low risk, moderate gain.'),
        ('★★☆☆☆', 'History heuristic improvements',
         'History gravity (decay older entries), counter-move heuristic\n'
         '  (store refutations indexed by the previous move).'),
    ]
    y = 0.60
    for stars, title, desc in next_items:
        ax.text(0.05, y, stars, ha='left', fontsize=10,
                color=GOLD, fontfamily='monospace', transform=ax.transAxes)
        ax.text(0.22, y, title, ha='left', fontsize=10.5,
                color=ACCENT, fontweight='bold', fontfamily='monospace',
                transform=ax.transAxes)
        ax.text(0.22, y - 0.038, desc, ha='left', fontsize=8.5,
                color=LT, fontfamily='monospace', transform=ax.transAxes)
        y -= 0.12

    ax.text(0.5, 0.02,
            'ClaudeChessV2  •  Erik Kugelberg  •  2026  •  github.com/ErikKugelberg/ClaudeChessV2',
            ha='center', fontsize=8, color=GREY,
            fontfamily='monospace', transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    out = 'ClaudeChessV2_Report.pdf'
    with PdfPages(out) as pdf:
        page_title(pdf)
        page_overview(pdf)
        page_board(pdf)
        page_movegen(pdf)
        page_negamax(pdf)
        page_id(pdf)
        page_ordering(pdf)
        page_tt(pdf)
        page_null(pdf)
        page_lmr(pdf)
        page_horizon(pdf)
        page_eval(pdf)
        page_journey(pdf)
        page_reverted(pdf)
        page_next(pdf)
        d = pdf.infodict()
        d['Title']   = 'ClaudeChessV2 Development Report'
        d['Author']  = 'Erik Kugelberg'
        d['Subject'] = 'Python Chess Engine — Iterative Deepening, Alpha-Beta, Move Ordering'

    print(f'Report written to {out}')
