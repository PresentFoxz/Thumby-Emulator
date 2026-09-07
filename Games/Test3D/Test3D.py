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

gfx.setFPS(20)
sprtPos = [0.5, 1.2, 0.5]
cam = None
plr = None
entIndex = []

objects      = [["cube.obj", 0], ["ball.obj", 0]]
entModel     = []

worldVerts  = None
depthBin    = None
worldSprt   = None
worldColors = None
worldModels = None
vertCount = 0
sprtCount = 0
fullCount = 0

@micropython.native
def convertTris(model):
    length = len(model["tris"])

    tri_data    = [0] * (length * 3)
    color_data  = [0] * length
    normal_data = [0] * length

    if (len(model["tris"]) == 0): return { "tris": tri_data, "normals": normal_data, "color": color_data } 

    verts  = model["verts"]
    tris   = model["tris"]
    normals = model["normal"]
    color  = model["color"]

    t = 0
    for f in range(len(tris)):
        t0, t1, t2 = tris[f]
        v0, v1, v2 = verts[t0], verts[t1], verts[t2]

        triID = t * 3
        tri_data[triID]     = v0
        tri_data[triID + 1] = v1
        tri_data[triID + 2] = v2
        color_data[t] = color[f]
        normal_data[t] = normals[f]

        t += 1
    
    return { "tris": tri_data, "normal": normal_data, "color": color_data }

def initGame():
    global cam, plr, entModel, worldVerts, depthBin, worldSprt, worldColors, worldModels
    
    entModel.clear()
    entIndex.clear()
    
    cam = Camera(0.0, 0.0, -4.0, 0.0, 0.0, 0.0, 0.001, 20.0, 1.12, 0.6, 120.0)
    # plr = Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0)
    # entIndex.append(Entities(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0))

    worldModels = []
    m = objects[1]
    loadedModel = Render.loadOBJ(modelPath + "/" + m[0], m[1])
    lib.MAX_TRIS = (len(loadedModel["tris"]) * 1)
    worldModels.append(convertTris(loadedModel))

    worldVerts  = bytearray(lib.MAX_TRIS * 6)
    depthBin    = array("i", [0] * (lib.MAX_TRIS * 3))
    worldSprt   = [bytearray(2) for _ in range(lib.MAX_SPRT)]
    worldColors = bytearray(lib.MAX_TRIS)

@micropython.native
def addWorld(worldVerts, worldColors, depthBin, count, tris, normals, color, x, y, z):
    if count >= lib.MAX_TRIS: return 0
    
    px, py, pz = lib.FMath.TO_FIXED_BITS(x), lib.FMath.TO_FIXED_BITS(y), lib.FMath.TO_FIXED_BITS(z)
    count += Render.directVerts(px, py, pz, cam, worldVerts, worldColors, depthBin, count, tris, normals, color)
    return count

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
        
        for model in worldModels:
            vertCount += addWorld(worldVerts, worldColors, depthBin, fullCount, model["tris"], model["normal"], model["color"], 0, 0, 0)
            fullCount = (vertCount + sprtCount)
        
        Render.renderWorld(worldVerts, worldSprt, worldColors, depthBin, fullCount)
        
        # print(f"FullCount: {fullCount} | VertCount: {vertCount} | SprtCount: {sprtCount}")

        lib.interlace ^= 1
        gfx.update()
main()