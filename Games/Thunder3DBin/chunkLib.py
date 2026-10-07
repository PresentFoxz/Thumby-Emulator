import micropython
import random
import sys
from math import *

modulePath = "/Module/Foxgine"
sys.path.append(modulePath)
import library as lib

SEED = 123456789

BLOCK_X  = 2
BLOCK_Y  = 7
BLOCK_Z  = 2
CHUNK_SIZE   = (BLOCK_X * BLOCK_Y * BLOCK_Z)

CHUNK_X = 1
CHUNK_Z = 1

RANGE_X = ((CHUNK_X * 2) + 1)
RANGE_Z = ((CHUNK_Z * 2) + 1)
CHUNK_AMT = (RANGE_X * RANGE_Z)

BLOCK_X_FIXED = BLOCK_X << lib.FIXED_BITS
BLOCK_Y_FIXED = BLOCK_Y << lib.FIXED_BITS
BLOCK_Z_FIXED = BLOCK_Z << lib.FIXED_BITS

MAX_TRIS_CHUNK = (CHUNK_SIZE * CHUNK_AMT)

RUNNING = False

print(f"Chunk Size: {CHUNK_SIZE} | Chunk Amount: {CHUNK_AMT} | Max Tris: {MAX_TRIS_CHUNK}")

chunkData = [bytearray(CHUNK_SIZE) for _ in range(CHUNK_AMT)]
chunkPos  = []

blockFace = [
    [-1,  0,  0], [1, 0, 0],
    [0, -1, 0], [0, 1, 0],
    [0, 0, -1], [0, 0, 1]
]

@micropython.viper
def getBlock(chunk, i:int) -> int:
    data = ptr8(chunk)
    return int(data[i])

@micropython.viper
def setBlock(chunk, i:int, value:int): chunk[i] = value

@micropython.viper
def getBlockIndex(x:int, y:int, z:int) -> int:
    BX:int = int(BLOCK_X)
    BY:int = int(BLOCK_Y)
    BZ:int = int(BLOCK_Z)

    if x < 0 or y < 0 or z < 0: return -1
    if x >= BX or y >= BY or z >= BZ: return -1
    return x + y * BX + z * BX * BY

@micropython.native
def getVoxelSafe(cx, cz, x, y, z):
    idx = getBlockIndex(x, y, z)
    if idx < 0:
        return False

    for i in range(CHUNK_AMT):
        if chunkPos[i][0] == cx and chunkPos[i][1] == cz:
            return getBlock(chunkData[i], idx) != 0

    return False

@micropython.native
def block_exists(chunkID:int, nx:int, ny:int, nz:int) -> bool:
    newChunk:int = int(chunkID)
    blockID:int = int(getBlockIndex(nx, ny, nz))

    if int(blockID) >= 0:
        return bool(getBlock(chunkData[newChunk], int(blockID)) != 0)

    cX:int = int(chunkPos[newChunk][0])
    cZ:int = int(chunkPos[newChunk][1])

    if (nx < 0):
        cX -= 1
        nx = int(BLOCK_X - 1)
    elif (nx >= BLOCK_X):
        cX += 1
        nx = 0
    
    if (nz < 0):
        cZ -= 1
        nz = int(BLOCK_Z - 1)
    elif (nz >= BLOCK_Z):
        cZ += 1
        nz = 0
    
    return bool(getVoxelSafe(cX, cZ, nx, ny, nz))

@micropython.viper
def getChunk(x:int, z:int):
    cx:int = x // int(BLOCK_X_FIXED)
    cz:int = z // int(BLOCK_Z_FIXED)

    return (cx, cz)

@micropython.native
def createData(idx, cx, cz):
    random.seed(SEED + (cx * 100) + (cz * 100))
    chunk = chunkData[idx]

    for i in range(CHUNK_SIZE):
        chunk[i] = random.randint(0, 1)

@micropython.viper
def checkDist(x:int, y:int, z:int, cx:int, cy:int, cz:int, fx:int, fy:int, fz:int, idx:int, distAmt:int) -> bool:
    if bool(RUNNING):
        bx:int = int(x + (int(chunkPos[idx][0]) * int(BLOCK_X)))
        by:int = (0 - y)
        bz:int = int(z + (int(chunkPos[idx][1]) * int(BLOCK_Z)))

        dx:int = bx - cx
        dy:int = by - cy
        dz:int = bz - cz

        dist:int = dx*dx + dy*dy + dz*dz
        if (dist > distAmt): return True

        dot:int = (lib.FMath.FIXED_MUL(dx << int(lib.FIXED_BITS), fx) + lib.FMath.FIXED_MUL(dy << int(lib.FIXED_BITS), (0 - fy)) + lib.FMath.FIXED_MUL(dz << int(lib.FIXED_BITS), fz))
        if (int(dot) <= 0): return True
    
    return False

@micropython.native
def createWorld(models, idx, camX, camY, camZ, fx, fy, fz):
    chunk = chunkData[idx]

    verts = []
    tris  = []
    color = []
    
    tri_data    = []
    color_data  = []
    normal_data = []
    
    visible = [False] * 6
    for i in range(CHUNK_SIZE):
        data = getBlock(chunk, i)
        if data == 0: continue

        modelIndex = data - 1
        if modelIndex >= len(models): continue

        model   = models[modelIndex]
        verts   = model["verts"]
        tris    = model["tris"]
        normals = model["normal"]
        color   = model["color"]

        x = i % BLOCK_X
        y = (i // BLOCK_X) % BLOCK_Y
        z = i // (BLOCK_X * BLOCK_Y)

        if checkDist(x, y, z, camX, camY, camZ, fx, fy, fz, idx, 30): continue

        xPos = lib.FMath.TO_FIXED_BITS(x)
        yPos = lib.FMath.TO_FIXED_BITS(y)
        zPos = lib.FMath.TO_FIXED_BITS(z)

        for f in range(0, len(tris), 2):
            face = blockFace[f // 2]

            nx = x + face[0]
            ny = y + face[1]
            nz = z + face[2]

            if block_exists(idx, nx, ny, nz):
                continue
            
            t0, t1, t2 = tris[f]
            t3, t4, t5 = tris[f+1]
            v0, v1, v2 = verts[t0], verts[t1], verts[t2]
            v3, v4, v5 = verts[t3], verts[t4], verts[t5]
            
            v0 = [v0[0] + xPos, v0[1] - yPos, v0[2] + zPos]
            v1 = [v1[0] + xPos, v1[1] - yPos, v1[2] + zPos]
            v2 = [v2[0] + xPos, v2[1] - yPos, v2[2] + zPos]
            v3 = [v3[0] + xPos, v3[1] - yPos, v3[2] + zPos]
            v4 = [v4[0] + xPos, v4[1] - yPos, v4[2] + zPos]
            v5 = [v5[0] + xPos, v5[1] - yPos, v5[2] + zPos]
            
            tri_data.append(v0)
            tri_data.append(v1)
            tri_data.append(v2)
            tri_data.append(v3)
            tri_data.append(v4)
            tri_data.append(v5)
            
            color_data.append(color[f])
            color_data.append(color[f+1])
            
            normal_data.append(normals[f])
            normal_data.append(normals[f+1])
    
    return { "tris": tri_data, "normal": normal_data, "color": color_data }

@micropython.native
def chunkSurroundings():
    idx = 0

    for x in range(-CHUNK_X, CHUNK_X + 1):
        for z in range(-CHUNK_Z, CHUNK_Z + 1):
            chunkPos.append([x, z])
            print(f"Chunk[{idx}] | Pos: X[{x}] | Z[{z}]")
            idx += 1