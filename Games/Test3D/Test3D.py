from thumbyGraphics import display as gfx
import thumbyButton as btn
import sys
import random
import micropython
from array import array

modelPath = "/Module/Foxgine"
sys.path.append(modelPath)
from classes import Entities, Camera, Render
import library as lib

gfx.setFPS(20)
sprtPos = [0.5, 1.2, 0.5]
cam = None
plr = None
entIndex = []

objects      = [["cube.obj", 0], ["ball.obj", 0]]
entModel     = []
loadedModels = []

worldVerts  = None
depthBin    = None
worldSprt   = None
worldColors = None
vertCount = 0
sprtCount = 0
fullCount = 0

def initGame():
    global cam, plr, loadedModels, entModel, worldVerts, depthBin, worldSprt, worldColors
    
    entModel.clear()
    loadedModels.clear()
    entIndex.clear()
    
    cam = Camera(0.0, 0.0, -4.0, 0.0, 0.0, 0.0, 0.001, 20.0, 1.12, 0.6, 120.0)
    # plr = Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0)
    # entIndex.append(Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0))

    m = objects[1]
    loadedModels.append(Render.loadOBJ(modelPath + "/" + m[0], m[1]))
    print(loadedModels[0])

    lib.MAX_TRIS = (len(loadedModels[0]["tris"]) * 1)

    worldVerts  = array("h", [0] * (lib.MAX_TRIS * 6))
    depthBin    = array("i", [0] * (lib.MAX_TRIS * 3))
    worldSprt   = [bytearray(2) for _ in range(lib.MAX_SPRT)]
    worldColors = bytearray(lib.MAX_TRIS)

@micropython.native
def addWorld(worldVerts, worldColors, depthBin, count, tris, normals, color):
    if count >= lib.MAX_TRIS: return 0
    
    count += Render.directVerts([0, 0, 0], cam, worldVerts, worldColors, depthBin, count, tris, normals, color)
    return count

@micropython.native
def convertTris(model, x, y, z):
    tri_data    = []
    color_data  = []
    normal_data = []

    if (len(model["tris"]) == 0): return { "tris": tri_data, "normals": normal_data, "color": color_data } 

    verts  = model["verts"]
    tris   = model["tris"]
    normals = model["normal"]
    color  = model["color"]

    for f in range(len(tris)):
        t0, t1, t2 = tris[f]
        v0, v1, v2 = verts[t0], verts[t1], verts[t2]

        v0 = [v0[0] + x, v0[1] - y, v0[2] + z]
        v1 = [v1[0] + x, v1[1] - y, v1[2] + z]
        v2 = [v2[0] + x, v2[1] - y, v2[2] + z]

        tri_data.append([v0, v1, v2])
        color_data.append(color[f])
        normal_data.append(normals[f])
    
    return { "tris": tri_data, "normal": normal_data, "color": color_data }

def main():
    global worldVerts, worldColors, depthBin, vertCount, sprtCount, fullCount, cam, plr, entIndex

    lib.FMath.init_tables()
    lib.buf = gfx.display.buffer
    try:
        initGame()
        print("Initalize Game")
    except Exception as e:
        print(f"Failed To Initalize: {e}")
        return

    while True:
        Render.fill(0)
        lib.buf = gfx.display.buffer

        vertCount = 0
        sprtCount = 0
        fullCount = 0
        
        cam.movement(btn)
        cam.updateFunctions()
        
        # sprtCount += Render.setupSprite(sprtPos, None, cam, None, worldSprt, depthBin, fullCount)
        # fullCount = (vertCount + sprtCount)
        
        for model in loadedModels:
            newModel = convertTris(model, 0, 0, 0)
            vertCount += addWorld(worldVerts, worldColors, depthBin, fullCount, newModel["tris"], newModel["normal"], newModel["color"])
            fullCount = (vertCount + sprtCount)
        
        Render.renderWorld(worldVerts, worldSprt, worldColors, depthBin, fullCount)
        
        # print(f"FullCount: {fullCount} | VertCount: {vertCount} | SprtCount: {sprtCount}")

        lib.interlace ^= 1
        gfx.update()
main()