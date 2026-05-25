# Piece IDs
empty = 0
Wpawn = 1
Wbishop = 2
Wknight = 3
Wrook = 4
Wqueen = 5
Wking = 6
pieceDivider = 7
Bpawn = 8
Bbishop = 9
Bknight = 10
Brook = 11
Bqueen = 12
Bking = 13

# game states:
onGoing = 0
drawRep = 1
staleMate = 2
blackWin = 3
whiteWin = 4

# This class describes a given move
class Move:
    def __init__(self, x1,y1,x2,y2,isAttacking=0):
        self.data = 0x0000
        self.data |= min(7,x1)
        self.data |= min(7,y1) << 3
        self.data |= min(7,x2) << 6
        self.data |= min(7,y2) << 9
        self.data |= isAttacking << 12

    def getX1(self):
        return self.data & 0b111

    def getY1(self):
        return (self.data & (0b111 << 3)) >> 3

    def getX2(self):
        return (self.data & (0b111 << 6)) >> 6

    def getY2(self):
        return (self.data & (0b111 << 9)) >> 9

    def getAttacking(self):
        return (self.data & (1 << 12)) >> 12

    def setAttacking(self):
        self.data |= 1 << 12

    def __eq__(self, other):
        return other is not None and isinstance(other, Move) and self.data == other.data

    def __hash__(self):
        return hash(self.data)

class LimitedSizeDict:
    def __init__(self, max_size):
        self.max_size = max_size
        self.internal_dict = {}

    def containsKey(self, key) -> bool:
        return key in self.internal_dict

    def __getitem__(self, key):
        return self.internal_dict[key]

    def __setitem__(self, key, value):
        if len(self.internal_dict) >= self.max_size:
            # Implement a policy to remove an item when the size exceeds the limit
            # For example, removing the first item (FIFO policy)
            first_key = next(iter(self.internal_dict))
            del self.internal_dict[first_key]

        self.internal_dict[key] = value

    def __len__(self):
        return len(self.internal_dict)