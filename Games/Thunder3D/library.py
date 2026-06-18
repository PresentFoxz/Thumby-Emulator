from math import *

FIXED_BITS = 8
FP24x8_ONE = (1 << FIXED_BITS)
INV_FIXED = 1.0 / FP24x8_ONE
TABLE_SIZE = 256
SIN_FIXED = [0]*256
COS_FIXED = [0]*256

interlace = 0
frameCount = 0

CHUNK_WIDTH    = 1
CHUNK_HEIGHT   = 1
CHUNK_DEPTH    = 1
CHUNK_AMT      = CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_DEPTH

CHUNK_X  = 2
CHUNK_Y  = 2
CHUNK_Z  = 2
CHUNK_SIZE   = (CHUNK_X * CHUNK_Y * CHUNK_Z)

MAX_TRIS_CHUNK = 192
MAX_TRIS       = (MAX_TRIS_CHUNK * CHUNK_AMT)
MAX_SPRT       = 0
MAX_DEPTH      = 20

EVEN_MASK = 0b01010101
ODD_MASK  = 0b10101010

buf    = None
width  = 72
height = 40
w_Half = width//2
h_Half = height//2

BAYER4x4_FLAT = bytearray([0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5])

class FMath:
    @staticmethod
    def TO_FIXED_BITS(a):
        return int(a * FP24x8_ONE)

    @staticmethod
    def FROM_FIXED_BITS(a):
        return a * INV_FIXED
        
    @staticmethod
    def FIXED_MUL(a, b):
        return (a * b) >> FIXED_BITS

    @staticmethod
    def FIXED_DIV(a, b):
        return (a << FIXED_BITS) // b
    
    @staticmethod
    def angle_to_index(fixed_angle):
        return (fixed_angle >> FIXED_BITS) & 255
    
    @staticmethod
    def FIXED_SIN(a):
        return SIN_FIXED[a & (TABLE_SIZE-1)]
    
    @staticmethod
    def FIXED_COS(a):
        return COS_FIXED[a & (TABLE_SIZE-1)]
    
    @staticmethod
    def init_tables():
        step = 6.28318530718 / TABLE_SIZE

        angle = 0.0
        for i in range(TABLE_SIZE):
            SIN_FIXED[i] = int(sin(angle) * FP24x8_ONE)
            COS_FIXED[i] = int(cos(angle) * FP24x8_ONE)
            angle += step