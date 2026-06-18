from math import *
interlace = 0

WORLD_SEED = 12345

MAX_CHUNKS = 1
CHUNK_W    = 5
CHUNK_H    = 5
CHUNK_SIZE = (CHUNK_W * CHUNK_H)

CUBE_W = 8
CUBE_H = 8

WORLD_CHUNK_W = 1
WORLD_CHUNK_H = 1
MAX_CHUNKS = WORLD_CHUNK_W * WORLD_CHUNK_H

CHUNK_CUBE_W = CHUNK_W * CUBE_W
CHUNK_CUBE_H = CHUNK_H * CUBE_H

width  = 72
height = 40
w_Half = width//2
h_Half = height//2

positions = [None for _ in range((WORLD_CHUNK_W * 2 + 1) * (WORLD_CHUNK_H * 2 + 1))]