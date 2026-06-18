from thumbyGraphics import display
import thumbyButton as btn
import sys
import random

modelPath = "/Games/Thunder3D"
sys.path.append(modelPath)
from classes import Entities, Camera, Render
import library as lib

display.setFPS(20)
sprtPos = [0.5, 1.2, 0.5]
cam = None
plr = None
entIndex = []

objects     = [["cube.obj", 0]]
entModel    = []
blockModels = []

worldVerts  = [bytearray(6) for _ in range(lib.MAX_TRIS)]
depthBin    = [[0, -1, 0] for _ in range(lib.MAX_TRIS)]
worldSprt   = [bytearray(2) for _ in range(lib.MAX_SPRT)]
worldColors = [0] * lib.MAX_TRIS
vertCount = 0
sprtCount = 0
fullCount = 0


chunkData  = [bytearray(lib.CHUNK_SIZE)] * lib.CHUNK_AMT
chunkVerts = [None] * lib.CHUNK_AMT
blockFace = [
    [-1,  0,  0], [1, 0, 0],
    [0, 1, 0], [0, -1, 0],
    [0, 0, -1], [0, 0, 1]
]

def initGame():
    global cam, plr, blockModels, entModel
    
    entModel.clear()
    blockModels.clear()
    entIndex.clear()
    
    cam = Camera(0.0, 0.0, -4.0, 0.0, 0.0, 0.0, 0.001, 20.0, 1.12, 0.6, 120.0)
    # plr = Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0)
    # entIndex.append(Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0))
    
    m = objects[0]
    blockModels.append(Render.loadOBJ(modelPath + "/" + m[0], m[1]))

def addWorld(worldVerts, worldColors, depthBin, count, tris, normals, color):
    if count >= lib.MAX_TRIS: return 0
    
    count += Render.directVerts([0, 0, 0], cam, worldVerts, worldColors, depthBin, count, tris, normals, color)
    return count

def getBlock(chunk, x, y, z, w, h, d):
    if x < 0 or y < 0 or z < 0: return 0
    if x >= w or y >= h or z >= d: return 0
    return chunk[x + y * w + z * w * h]

def createWorld(models, idx):
    chunk = chunkData[idx]
    
    verts = []
    tris  = []
    color = []
    for i in range(len(chunk)):
        chunk[i] = random.randint(0, 1)
    
    tri_data    = []
    color_data  = []
    normal_data = []
    
    cX, cY, cZ = lib.CHUNK_X, lib.CHUNK_Y, lib.CHUNK_Z
    cW, cH, cD = lib.CHUNK_WIDTH, lib.CHUNK_HEIGHT, lib.CHUNK_DEPTH
    for i in range(len(chunk)):
        data = chunk[i]
        if (data == 0): continue
        
        modelIndex = (data - 1)
        if modelIndex >= len(models): continue
        
        model  = models[modelIndex]
        verts  = model["verts"]
        tris   = model["tris"]
        normals = model["normal"]
        color  = model["color"]
        
        x = (i % cX)
        y = ((i // cX) % cY)
        z = (i // (cX * cY))
        
        xPos = lib.FMath.TO_FIXED_BITS(x)
        yPos = lib.FMath.TO_FIXED_BITS(y)
        zPos = lib.FMath.TO_FIXED_BITS(z)
        
        print(f"Pos: X[{x}] | Y[{y}] | Z[{z}]")
        for f in range(0, len(tris), 2):
            face = blockFace[f//2]
            
            nx, ny, nz = x + face[0], y + face[1], z + face[2]
            if getBlock(chunk, nx, ny, nz, cX, cY, cZ) >= 1: continue
            
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
                
            tri_data.append([v0, v1, v2])
            tri_data.append([v3, v4, v5])
            
            color_data.append(color[f])
            color_data.append(color[f+1])
            
            normal_data.append(normals[f])
            normal_data.append(normals[f+1])
    
    print(f"Block Data: {chunkData[idx]}")
    print(f"Tri Count: {len(tri_data)}")
    return { "tris": tri_data, "normals": normal_data, "color": color_data }

def main():
    global worldVerts, worldColors, depthBin, vertCount, sprtCount, fullCount, cam, plr, entIndex
    
    lib.FMath.init_tables()
    lib.buf = display.buffer
    try:
        initGame()
        print("Initalize Game")
    except Exception as e:
        print(f"Failed To Initalize: {e}")
        return
    
    for i in range(lib.CHUNK_AMT): chunkVerts[i] = createWorld(blockModels, i)
    
    while True:
        Render.fill(0)
        lib.buf = display.buffer
        
        vertCount = 0
        sprtCount = 0
        fullCount = 0
        depthBin  = [[0, -1, 0] for _ in range(lib.MAX_TRIS)]
        
        cam.movement(btn)
        cam.updateFunctions()
        
        # sprtCount += Render.setupSprite(sprtPos, None, cam, None, worldSprt, depthBin, fullCount)
        # fullCount = (vertCount + sprtCount)
        
        for model in chunkVerts:
            vertCount += addWorld(worldVerts, worldColors, depthBin, fullCount, model["tris"], model["normals"], model["color"])
            fullCount = (vertCount + sprtCount)
        
        Render.renderWorld(worldVerts, worldSprt, worldColors, depthBin, fullCount)
        
        # print(f"FullCount: {fullCount} | VertCount: {vertCount} | SprtCount: {sprtCount}")
        lib.interlace ^= 1
        display.update()
main()