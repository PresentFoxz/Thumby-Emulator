from thumbyGraphics import display as gfx
import thumbyButton as btn
import sys
import random
import micropython
from array import array

modulePath = "/Module/Foxgine"
modelPath  = "/Games/Belory"
sys.path.append(modulePath)
from classes import Entities, Camera, Render
import library as lib

sys.path.append(modelPath)
import chunkLib

gfx.setFPS(20)
sprtPos = [0.5, 1.2, 0.5]
cam = None
plr = None
entIndex = []

objects     = [["cube.obj", 0]]
entModel    = []
blockModels = []

worldVerts  = None
depthBin    = None
worldSprt   = None
worldColors = None
vertCount = 0
sprtCount = 0
fullCount = 0

currChunk = None
lastChunk = None

def initGame():
    global cam, plr, blockModels, entModel
    
    entModel.clear()
    blockModels.clear()
    entIndex.clear()
    
    cam = Camera(0.0, 0.0, -4.0, 0.0, 0.0, 0.0, 0.001, 20.0, 1.01, 0.15, 60.0)
    # plr = Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0)
    # entIndex.append(Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0))

    m = objects[0]
    blockModels.append(Render.loadOBJ(modelPath + "/" + m[0], m[1]))
    print(blockModels[0])

def initLists():
    global worldVerts, depthBin, worldSprt, worldColors

    worldVerts  = array("h", [0] * (lib.MAX_TRIS * 6))
    depthBin    = array("i", [0] * (lib.MAX_TRIS * 3))
    worldSprt   = [bytearray(2) for _ in range(lib.MAX_SPRT)]
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
    global worldVerts, worldColors, depthBin, vertCount, sprtCount, fullCount, cam, plr, entIndex, lastChunk, currChunk
    
    lib.FMath.init_tables()
    chunkLib.chunkSurroundings()
    try:
        initGame()

        for i in range(chunkLib.CHUNK_AMT):
            chunkLib.createData(i)
            world = chunkLib.createWorld(blockModels, i, 0, 0, 0, 0, 0, 0)
            lib.MAX_TRIS += (len(world["tris"])) // 3
    
        currChunk = (0, 0)
        lastChunk = currChunk
        
        initLists()
        print("Initalize Game")
    except Exception as e:
        print(f"Failed To Initalize: {e}")
        return


    chunkLib.RUNNING = True
    while True:
        lib.buf = gfx.display.buffer
        Render.fill(0)
        
        vertCount = 0
        sprtCount = 0
        fullCount = 0
        
        cam.movement(btn)
        cam.updateFunctions()

        currChunk = chunkLib.getChunk(cam.x, cam.z)
        if currChunk[0] != lastChunk[0] or currChunk[1] != lastChunk[1]:
            print(f"Current Chunk: {currChunk} | Last Chunk: {lastChunk}")
        
        # sprtCount += Render.setupSprite(sprtPos, None, cam, None, worldSprt, depthBin, fullCount)
        # fullCount = (vertCount + sprtCount)
        
        cx = int(lib.FMath.FROM_FIXED_BITS(cam.x))
        cy = int(lib.FMath.FROM_FIXED_BITS(cam.y))
        cz = int(lib.FMath.FROM_FIXED_BITS(cam.z))
        for i in range(chunkLib.CHUNK_AMT):
            chunkVerts = chunkLib.createWorld(blockModels, i, cx, cy, cz, cam.norm_x, cam.norm_y, cam.norm_z)
            added = addWorld(worldVerts, worldColors, depthBin, fullCount, chunkVerts["tris"], chunkVerts["normal"], chunkVerts["color"], int(chunkLib.chunkPos[i][0] * chunkLib.BLOCK_X), 0, int(chunkLib.chunkPos[i][1] * chunkLib.BLOCK_Z))
            vertCount += added
            fullCount = (vertCount + sprtCount)
        
        Render.renderWorld(worldVerts, worldSprt, worldColors, depthBin, fullCount, False)

        lastChunk = currChunk
        lib.interlace ^= 1
        gfx.update()
main()