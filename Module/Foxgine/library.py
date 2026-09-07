from math import *
import micropython

FIXED_BITS = 8
FP24x8_ONE = (1 << FIXED_BITS)
INV_FIXED = 1.0 / FP24x8_ONE

TABLE_SIZE = 256
SIN_FIXED = [0]*TABLE_SIZE
COS_FIXED = [0]*TABLE_SIZE

TABLE_SIZE_LUT = 520
FP16x16_ONE = (1 << 16)
DIV_LUT = [0]*TABLE_SIZE_LUT

interlace = 0
frameCount = 0

MAX_TRIS  = 0
MAX_SPRT  = 0
MAX_DEPTH = 20

EVEN_MASK = 0b01010101
ODD_MASK  = 0b10101010

buf    = None
width  = 72
height = 40
w_Half = width//2
h_Half = height//2

BAYER4x4_FLAT = bytearray([0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5])

interlace = 0
frameCount = 0

@micropython.native
def DIV_OPP(value):
    if value == 0:
        return 0

    sign = 1
    if value < 0:
        sign = -1
        value = -value

    shift = 0

    while value >= TABLE_SIZE_LUT:
        value >>= 1
        shift += 1

    recip = DIV_LUT[value]

    while shift:
        recip >>= 1
        shift -= 1

    return -recip if sign < 0 else recip

@micropython.native
def MUL_OPP(value, divisor): return (value * DIV_OPP(divisor)) >> 16

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
        if b == 0: return 0
        return MUL_OPP(a << FIXED_BITS, b)
    
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
        
        for i in range(TABLE_SIZE_LUT):
            if i == 0: DIV_LUT[i] = 0
            else: DIV_LUT[i] = int(FP16x16_ONE // i)
    
    @staticmethod
    def FLOOR_DIV(a, b):
        if b == 0: return 0

        q = a // b
        return q