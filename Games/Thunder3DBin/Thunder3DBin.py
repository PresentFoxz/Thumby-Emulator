import thumbyButton as btn
import sys
import random
import micropython
from array import array
import gc

modulePath = "/Module/Foxgine"
modelPath  = "/Games/Thunder3DBin"
sys.path.append(modulePath)
from classes import Entities, Camera, Render
import library as lib
from thumbyGrayscale import display as gfx
from thumbyGrayscale import Sprite

sys.path.append(modelPath)
import chunkLib
import cover

title = Sprite(72, 40, (cover.b0, cover.b1), 0, 0)

gfx.setFPS(15)
cam = None
plr = None
entIndex = []

objects     = [["cube.obj", 0]]
entModel    = []
blockModels = []

worldVerts  = None
depthBin    = None
bucketHead  = None
bucketNext  = None
worldColors = None
worldModels = None
vertCount = 0
fullCount = 0

currChunk = None
lastChunk = None

def initGame():
    global cam, plr, blockModels, entModel
    
    entModel.clear()
    blockModels.clear()
    entIndex.clear()
    
    cam = Camera(0.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.001, 20.0, 1.01, 0.15, 60.0)
    # plr = Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0)
    # entIndex.append(Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0))

    m = objects[0]
    blockModels.append(Render.loadOBJ(modelPath + "/" + m[0], m[1]))

def initLists():
    global worldVerts, depthBin, bucketHead, bucketNext, worldColors
    
    worldVerts  = array("h", [0] * (lib.MAX_TRIS * 6))
    depthBin    = array("i", [0] * (lib.MAX_TRIS * 2))
    bucketHead = array("h", [-1] * lib.DEPTH_BUCKETS)
    bucketNext = array("h", [-1] * lib.MAX_TRIS)
    worldColors = bytearray(lib.MAX_TRIS)

@micropython.native
def addWorld(worldVerts, worldColors, depthBin, count, tris, normals, color, x, y, z):
    if count >= lib.MAX_TRIS: return 0
    
    px = lib.FMath.TO_FIXED_BITS(x)
    py = lib.FMath.TO_FIXED_BITS(y)
    pz = lib.FMath.TO_FIXED_BITS(z)

    added = 0
    added += Render.directVerts(px, py, pz, cam, worldVerts, worldColors, depthBin, count, tris, normals, color)
    return added

def main():
    global worldVerts, worldColors, depthBin, vertCount, fullCount, cam, plr, entIndex, lastChunk, currChunk, bucketHead, bucketNext
    
    while True:
        gfx.fill(0)
        gfx.drawSprite(title)
        
        if btn.buttonA.justPressed(): break
    
        gfx.update()
    
    worldChunkX = 0
    worldChunkZ = 0

    lib.FMath.init_tables()
    chunkLib.chunkSurroundings()
    lib.buf = gfx.display.buffer
    lib.shd = gfx.display.shading
    try:
        initGame()

        lib.MAX_TRIS = 200
        for i in range(chunkLib.CHUNK_AMT):
            chunkLib.createData(i, worldChunkX + chunkLib.chunkPos[i][0], worldChunkZ + chunkLib.chunkPos[i][1])
    
        currChunk = (0, 0)
        lastChunk = currChunk
        
        gc.collect()
        initLists()
        print("Initalize Game")
    except Exception as e:
        print(f"Failed To Initalize: {e}")
        return


    chunkLib.RUNNING = True
    while True:
        Render.fill(0)
        Render.clear_depth_buckets(bucketHead)
        
        vertCount = 0
        fullCount = 0
        
        cam.movement(btn)
        cam.updateFunctions()

        # print(f"Player Pos: [ {cam.x}, {cam.y}, {cam.z} ]")
        currChunk = chunkLib.getChunk(cam.x, cam.z)
        if currChunk[0] != lastChunk[0] or currChunk[1] != lastChunk[1]:
            worldChunkX += currChunk[0]
            worldChunkZ += currChunk[1]

            cam.x -= currChunk[0] * chunkLib.BLOCK_X_FIXED
            cam.z -= currChunk[1] * chunkLib.BLOCK_Z_FIXED

            for i in range(chunkLib.CHUNK_AMT):
                chunkLib.createData(i, worldChunkX + chunkLib.chunkPos[i][0], worldChunkZ + chunkLib.chunkPos[i][1])

            print(f"World Chunk: [ {worldChunkX} | {worldChunkZ} ]")
            
            currChunk = (0, 0)
        
        cx = int(lib.FMath.FROM_FIXED_BITS(cam.x))
        cy = int(lib.FMath.FROM_FIXED_BITS(cam.y))
        cz = int(lib.FMath.FROM_FIXED_BITS(cam.z))
        for i in range(chunkLib.CHUNK_AMT):
            renderChunkX = chunkLib.chunkPos[i][0]
            renderChunkZ = chunkLib.chunkPos[i][1]

            chunkVerts = chunkLib.createWorld(blockModels, i, cx, cy, cz, cam.norm_x, cam.norm_y, cam.norm_z)
            added = addWorld(worldVerts, worldColors, depthBin, fullCount, chunkVerts["tris"], chunkVerts["normal"], chunkVerts["color"], int(renderChunkX * chunkLib.BLOCK_X), 0, int(renderChunkZ * chunkLib.BLOCK_Z))
            vertCount += added
            fullCount = vertCount
        
        Render.renderWorld(worldVerts, worldColors, depthBin, fullCount, False, bucketHead, bucketNext)

        lastChunk = currChunk
        lib.interlace ^= 1
        gfx.update()
main()