"""
Visual diagram: how precomputed attack tables replace _getMoves() in evaluatePosition().
Saves attack_table_diagram.png.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import numpy as np

LIGHT = '#F0D9B5'
DARK  = '#B58863'
HL    = '#F6F669'   # yellow highlight
ATK   = '#CC3232'   # red = attacked square
OWN   = '#2255AA'   # blue = own piece
PIECE = '#1A1A1A'
GRAY  = '#CCCCCC'

def draw_board(ax, highlights=None, piece_sq=None, piece_char='N',
               attack_squares=None, labels=None, title='', annotate_sq=None):
    """Draw an 8×8 chess board with optional highlights."""
    ax.set_xlim(0, 8); ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=9, pad=4)
    for y in range(8):
        for x in range(8):
            color = LIGHT if (x + y) % 2 == 0 else DARK
            sq = y * 8 + x
            if highlights and sq in highlights:
                color = highlights[sq]
            rect = patches.Rectangle((x, y), 1, 1, fc=color, ec='none')
            ax.add_patch(rect)
    # Thin grid
    for i in range(9):
        ax.axhline(i, color='#555', lw=0.3)
        ax.axvline(i, color='#555', lw=0.3)
    # File/rank labels
    for i in range(8):
        ax.text(i + 0.5, -0.35, 'abcdefgh'[i], ha='center', va='top', fontsize=6, color='#666')
        ax.text(-0.3, i + 0.5, str(i + 1), ha='right', va='center', fontsize=6, color='#666')
    if piece_sq is not None:
        px, py = piece_sq % 8, piece_sq // 8
        ax.text(px + 0.5, py + 0.5, piece_char, ha='center', va='center',
                fontsize=18, color=OWN, fontweight='bold', zorder=5)
    if attack_squares:
        for sq in attack_squares:
            ax.text(sq % 8 + 0.5, sq // 8 + 0.5, '×', ha='center', va='center',
                    fontsize=14, color=ATK, fontweight='bold', zorder=5)
    if labels:
        for sq, txt in labels.items():
            ax.text(sq % 8 + 0.5, sq // 8 + 0.08, txt, ha='center', va='bottom',
                    fontsize=5, color='#333')
    if annotate_sq is not None:
        ax.add_patch(patches.Rectangle((annotate_sq%8, annotate_sq//8), 1, 1,
                     fc='none', ec='#FF8800', lw=2.5, zorder=6))

# ── Knight attack squares from e4 (sq=28) ──────────────────────────
KNIGHT_SQ = 28  # e4
kx, ky = 4, 3
kn_offs = [(-2,1),(-1,2),(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1)]
kn_valid = []
kn_invalid = []
for dx, dy in kn_offs:
    nx, ny = kx+dx, ky+dy
    if 0<=nx<=7 and 0<=ny<=7:
        kn_valid.append(ny*8+nx)
    else:
        kn_invalid.append((kx+dx, ky+dy))

# Precomputed bitboard for e4 knight
KNIGHT_BB = 0
for sq in kn_valid:
    KNIGHT_BB |= 1 << sq

# Rook e4 ray indices (simplified: one rank, one file)
ROOK_SQ = 28  # e4
rx, ry = 4, 3
rook_rays = {
    'East  [→]': [ry*8 + (rx+i) for i in range(1, 8-rx)],
    'West  [←]': [ry*8 + (rx-i) for i in range(1, rx+1)],
    'North [↑]': [(ry+i)*8 + rx for i in range(1, 8-ry)],
    'South [↓]': [(ry-i)*8 + rx for i in range(1, ry+1)],
}

# Blockers on east ray for demo: piece on g4 (sq=30)
BLOCKER_SQ = 30  # g4, own piece — rook can't pass

fig = plt.figure(figsize=(14, 9.5))
fig.patch.set_facecolor('#FAFAFA')

# ── Title ──────────────────────────────────────────────────────────
fig.text(0.5, 0.97, 'Precomputed Attack Tables — How evaluatePosition() was optimised',
         ha='center', va='top', fontsize=13, fontweight='bold', color='#222')

# ─────────────────────────────────────────────────────────────────────
# ROW 1: Knight — Before vs After
# ─────────────────────────────────────────────────────────────────────
ax1a = fig.add_axes([0.03, 0.55, 0.19, 0.35])   # board: before
ax1b = fig.add_axes([0.26, 0.55, 0.19, 0.35])   # board: after
ax1c = fig.add_axes([0.50, 0.55, 0.46, 0.35])   # explanation panel

# --- Board A: Before (show offset computation attempt) ---
hl_before = {}
for sq in kn_valid:
    hl_before[sq] = HL
for sq in kn_valid:
    hl_before[sq] = ATK + '55'   # translucent red
hl_before[KNIGHT_SQ] = '#AADAFF'

draw_board(ax1a, highlights=hl_before, piece_sq=KNIGHT_SQ, piece_char='♞',
           attack_squares=kn_valid,
           title='BEFORE: _getMoves(x=4, y=3)\n8 offset checks + bounds + board lookup')

# Draw offset arrows (crude — matplotlib axes)
for dx, dy in kn_offs:
    nx, ny = kx+dx, ky+dy
    if 0<=nx<=7 and 0<=ny<=7:
        ax1a.annotate('', xy=(nx+0.5, ny+0.5), xytext=(kx+0.5, ky+0.5),
                      arrowprops=dict(arrowstyle='->', color=ATK, lw=1.2, shrinkA=8, shrinkB=8))
    else:
        # Clip arrow to boundary
        nx_c = max(0, min(7.9, nx+0.5))
        ny_c = max(0, min(7.9, ny+0.5))
        ax1a.annotate('', xy=(nx_c, ny_c), xytext=(kx+0.5, ky+0.5),
                      arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.0,
                                      shrinkA=8, shrinkB=2,
                                      connectionstyle='arc3,rad=0'))
        ax1a.text(nx_c, ny_c, '✗', ha='center', va='center', fontsize=8, color=GRAY)

# --- Board B: After (precomputed table) ---
hl_after = {sq: '#FF888888' for sq in kn_valid}
hl_after[KNIGHT_SQ] = '#AADAFF'
draw_board(ax1b, highlights=hl_after, piece_sq=KNIGHT_SQ, piece_char='♞',
           attack_squares=kn_valid,
           title='AFTER: _KNIGHT_ATTACKS[28] (one lookup)\n→ bitboard with all 8 targets precomputed')

# Thick arrow from piece to each attack square (already in table)
for sq in kn_valid:
    ax1b.annotate('', xy=(sq%8+0.5, sq//8+0.5), xytext=(kx+0.5, ky+0.5),
                  arrowprops=dict(arrowstyle='->', color='#CC3232', lw=0.9,
                                  shrinkA=8, shrinkB=8, linestyle='dashed'))

# --- Explanation panel ---
ax1c.set_xlim(0, 10); ax1c.set_ylim(0, 10)
ax1c.axis('off')
ax1c.text(0, 9.6, '♞  Knight / ♚ King / pawn   — Fixed-pattern pieces', fontsize=9.5,
          fontweight='bold', va='top')

code_before = (
    "OLD  (_getMoves, called each eval node):\n"
    "  for m in knightMoves:          # 8 iterations\n"
    "    xt, yp = x+m[0], y+m[1]     # 2 adds\n"
    "    if 0<=xt<=7 and 0<=yp<=7:   # 4 comparisons\n"
    "      if board[yp*8+xt] == 0:   # multiply + add + lookup\n"
    "        newBoard |= 1<<(yp*8+xt)\n"
    "        nrMoves += 1\n"
    "      elif board[yp*8+xt] > 7:  # enemy\n"
    "        nrMoves += 2\n"
    "  ≈ 80 Python ops per knight"
)
ax1c.text(0, 8.7, code_before, fontsize=7.5, va='top', family='monospace',
          color='#550000',
          bbox=dict(fc='#FFF0F0', ec='#CC8888', lw=0.8, boxstyle='round,pad=0.4'))

code_after = (
    "NEW  (precomputed at class load — O(1) per eval node):\n"
    "  atk = _KNIGHT_ATTACKS[sq]          # 1 list lookup\n"
    "  reachable = atk & ~own_W_bb        # 1 bitwise AND\n"
    "  cnt = bin(reachable).count('1')    # 1 popcount\n"
    "       + bin(reachable & own_B_bb).count('1')\n"
    "  ≈ 5 Python ops per knight  (16× fewer)"
)
ax1c.text(0, 5.5, code_after, fontsize=7.5, va='top', family='monospace',
          color='#003300',
          bbox=dict(fc='#F0FFF0', ec='#88CC88', lw=0.8, boxstyle='round,pad=0.4'))

# Show the bitboard as a 64-bit number
bb_str = f'KNIGHT_ATTACKS[28] = 0x{KNIGHT_BB:016X}\n'
bb_str += '  bit pattern (LSB=a1, each row=8 bits):\n'
rows = []
for row in range(7, -1, -1):
    bits = [(KNIGHT_BB >> (row*8+col)) & 1 for col in range(8)]
    rows.append('  rank ' + str(row+1) + ': ' + ' '.join('1' if b else '·' for b in bits))
bb_str += '\n'.join(rows)
ax1c.text(0, 2.8, bb_str, fontsize=7, va='top', family='monospace', color='#333',
          bbox=dict(fc='#F8F8FF', ec='#AAAADD', lw=0.8, boxstyle='round,pad=0.3'))

ax1c.text(0, 0.5,
          'Same approach for ♚ king  (KING_ATTACKS[sq])  and  ♙/♟ pawn diagonals  (WPAWN_ATTACKS / BPAWN_ATTACKS)',
          fontsize=8, style='italic', color='#444')

# ─────────────────────────────────────────────────────────────────────
# ROW 2: Sliding pieces (rook) — Before vs After
# ─────────────────────────────────────────────────────────────────────
ax2a = fig.add_axes([0.03, 0.07, 0.19, 0.40])
ax2b = fig.add_axes([0.26, 0.07, 0.19, 0.40])
ax2c = fig.add_axes([0.50, 0.07, 0.46, 0.40])

# Boards show rook on e4 with a blocker on g4 (own piece) and d4 (enemy)
ROOK_BOARD_HL = {}
BLOCKER_OWN = 30    # g4 own piece (white rook blocked)
BLOCKER_ENM = 27    # d4 enemy piece (white rook captures)
ROOK_BOARD_HL[ROOK_SQ] = '#AADAFF'
ROOK_BOARD_HL[BLOCKER_OWN] = '#AADAFF'   # own piece (blue)
ROOK_BOARD_HL[BLOCKER_ENM] = '#FFAAAA'   # enemy piece (red)

# Squares the rook attacks given these blockers:
rook_atk = []
# East: e4→f4 (28→29), then blocked by own on g4(30) — f4 is reachable (29)
for sq in [29]:  rook_atk.append(sq)  # f4
# West: d4 is enemy (27 → captures), stops
for sq in [27]:  rook_atk.append(sq)  # d4 (capture)
# North: e5,e6,e7,e8 = 36,44,52,60
for sq in [36,44,52,60]: rook_atk.append(sq)
# South: e3,e2,e1 = 20,12,4
for sq in [20,12,4]: rook_atk.append(sq)

for sq in rook_atk: ROOK_BOARD_HL[sq] = HL

draw_board(ax2a, highlights=ROOK_BOARD_HL, piece_sq=ROOK_SQ, piece_char='♜',
           attack_squares=rook_atk,
           title='BEFORE: _getMoves → _iterateMovesW/B\nrecomputes x+dx, y+dy, bounds check every step')

# Arrow along east ray showing it stops at own piece
ax2a.annotate('', xy=(BLOCKER_OWN%8+0.5, BLOCKER_OWN//8+0.5),
              xytext=(ROOK_SQ%8+0.5, ROOK_SQ//8+0.5),
              arrowprops=dict(arrowstyle='->', color='#CC0000', lw=1.5, shrinkA=8, shrinkB=4))
ax2a.text(BLOCKER_OWN%8+0.5, BLOCKER_OWN//8-0.25, 'own\n(stop)', ha='center',
          fontsize=5.5, color='#2255AA')
ax2a.annotate('', xy=(BLOCKER_ENM%8+0.5, BLOCKER_ENM//8+0.5),
              xytext=(ROOK_SQ%8+0.5, ROOK_SQ//8+0.5),
              arrowprops=dict(arrowstyle='->', color='#CC0000', lw=1.5, shrinkA=8, shrinkB=4))
ax2a.text(BLOCKER_ENM%8+0.5, BLOCKER_ENM//8-0.25, 'enemy\n(capt)', ha='center',
          fontsize=5.5, color='#880000')

draw_board(ax2b, highlights=ROOK_BOARD_HL, piece_sq=ROOK_SQ, piece_char='♜',
           attack_squares=rook_atk,
           title='AFTER: precomputed ray index lists\nno arithmetic per step — just board[idx]')

ax2b.annotate('', xy=(29%8+0.5, 29//8+0.5), xytext=(ROOK_SQ%8+0.5, ROOK_SQ//8+0.5),
              arrowprops=dict(arrowstyle='->', color='#CC0000', lw=1.5, shrinkA=8, shrinkB=4,
                              linestyle='dashed'))

# Explanation
ax2c.set_xlim(0, 10); ax2c.set_ylim(0, 10)
ax2c.axis('off')
ax2c.text(0, 9.6, '♜♝♛  Rook / Bishop / Queen   — Sliding pieces (board-state dependent)',
          fontsize=9.5, fontweight='bold', va='top')

code_old_slide = (
    "OLD  (_iterateMovesW called per ray, 4×rook, 4×bishop, 8×queen):\n"
    "  t = x + xt                              # add\n"
    "  while t!=8 and p!=8 and t!=-1 and p!=-1: # 4 comparisons per step\n"
    "    idx = p*8 + t                         # multiply + add\n"
    "    if board[idx] == empty: ...           # lookup\n"
    "      t += xt; p += yt                   # 2 more adds\n"
    "  ≈ 10+ Python ops per ray step"
)
ax2c.text(0, 8.8, code_old_slide, fontsize=7.5, va='top', family='monospace',
          color='#550000',
          bbox=dict(fc='#FFF0F0', ec='#CC8888', lw=0.8, boxstyle='round,pad=0.4'))

code_new_slide = (
    "NEW  (precomputed ray index lists — no arithmetic per step):\n"
    "_ROOK_RAYS[28] = [\n"
    "  [29, 30, 31],          # East  ray indices (a1=0…h8=63)\n"
    "  [27, 26, 25, 24],      # West  ray indices\n"
    "  [36, 44, 52, 60],      # North ray indices\n"
    "  [20, 12, 4],           # South ray indices\n"
    "]\n"
    "for ray in _ROOK_RAYS[sq]:      # precomputed, no bounds check\n"
    "  for idx in ray:               # just iterate list\n"
    "    pc = board[idx]             # 1 lookup (no multiply!)\n"
    "    if pc == empty: ...\n"
    "    else: break                 # stop at any blocker\n"
    "  ≈ 1–2 Python ops per ray step  (5–10× fewer)"
)
ax2c.text(0, 5.7, code_new_slide, fontsize=7.5, va='top', family='monospace',
          color='#003300',
          bbox=dict(fc='#F0FFF0', ec='#88CC88', lw=0.8, boxstyle='round,pad=0.4'))

ax2c.text(0, 1.8,
          'How the tables are built  (once at class-load time, stored as class attributes):',
          fontsize=8.5, fontweight='bold', va='top')
init_code = (
    "class chessBoard2:\n"
    "    def _build_attack_tables():\n"
    "        for sq in range(64):\n"
    "            x, y = sq%8, sq//8\n"
    "            # knight: try all 8 L-jumps, keep in-bounds ones\n"
    "            KN[sq] = bitboard_of_valid_jumps(x, y)\n"
    "            # rook east ray: [y*8+x+1, y*8+x+2, …] until x=7\n"
    "            RK[sq] = [build_ray(x,y, dx,dy) for dx,dy in rook_dirs]\n"
    "        return KN, KG, WP, BP, RK, BS, QN  # 7 tables\n"
    "    _KNIGHT_ATTACKS, _KING_ATTACKS, … = _build_attack_tables()\n"
    "    del _build_attack_tables   # clean up temp function"
)
ax2c.text(0, 1.1, init_code, fontsize=7, va='top', family='monospace', color='#333',
          bbox=dict(fc='#F8F8FF', ec='#AAAADD', lw=0.8, boxstyle='round,pad=0.3'))

# ── Bottom summary bar ──────────────────────────────────────────────
fig.text(0.5, 0.025,
         'Net effect: evaluatePosition() no longer calls _getMoves().  '
         'Each non-sliding piece: O(80) ops → O(5) ops.  '
         'Each sliding ray step: O(10) ops → O(2) ops.  '
         'Pre-pass builds own_W_bb / own_B_bb in O(64) before the main loop.',
         ha='center', va='bottom', fontsize=8.5,
         bbox=dict(fc='#FFFBE6', ec='#CCAA00', lw=1, boxstyle='round,pad=0.4'))

plt.savefig('attack_table_diagram.png', dpi=140, bbox_inches='tight',
            facecolor=fig.get_facecolor())
print('Saved attack_table_diagram.png')
plt.show()
