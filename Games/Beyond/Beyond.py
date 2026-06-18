import thumbyButton as btn
import sys
import random
import micropython
from thumbySaves import saveData

sys.path.append("/Games/Beyond")
from classes import Entities, Camera, WorldData, Render
import library as lib
from thumbyGrayscale import display

display.setFont("lib/font3x5.bin", 3, 5, 1)
display.setFPS(20)

@micropython.native
def createChunkAlign():
    idx = 0
    for y in range(-lib.WORLD_CHUNK_H, lib.WORLD_CHUNK_H + 1):
        for x in range(-lib.WORLD_CHUNK_W, lib.WORLD_CHUNK_W + 1):
            lib.positions[idx] = [x, y]
            idx += 1

def initGame():
    cam = Camera(0, 0, 20)
    player = Entities(0.0, 0.0, [0, 0, 5, 10], 4, 1.2, 0.6, 0.8, 5.0, 2.0, 5.0, 0)

    createChunkAlign()

    return cam, player

@micropython.native
def handleEntities(cam, player, entities, tick, worldChunks, radius):
    # for ent in entities:
    #     if ent[2] != lib.interlace:
    #         continue

    #     canDetect = False
    #     ox = int(ent[0].x + ent[0].box[0])
    #     oy = int(ent[0].y + ent[0].box[1])
    #     ow = ox + ent[0].box[2]
    #     oh = oy + ent[0].box[3]

    #     ent_cx, ent_cy = WorldData.getChunk(ent[0].x, ent[0].y, 0, 0)

    #     for _, chunk in enumerate(worldChunks):
    #         if chunk[1] == ent_cx and chunk[2] == ent_cy:
    #             ent[1] = _
    #             break
        
    #     dx = ent[0].x - player.x
    #     dy = ent[0].y - player.y
    #     if (dx * dx + dy * dy) < radius * radius:
    #         ent[0].ai_movement(tick)
    #         ent[0].checkCollision(worldChunks)

    #         ex, ey, ew, eh = int(ent[0].x + ent[0].box[0]) - cam.x, int(ent[0].y + ent[0].box[1]) - cam.y, ent[0].box[2], ent[0].box[3]
    #         if ex + ew < lib.width or ex > 0 or ey + eh < lib.height or ey > 0:
    #             display.drawFilledRectangle(ex, ey, ew, eh, 3)

    px, py, pw, ph = int(player.x + player.box[0]) - cam.x, int(player.y + player.box[1]) - cam.y, player.box[2], player.box[3]
    if px + pw < lib.width or px > 0 or py + ph < lib.height or py > 0:
        display.drawFilledRectangle(px, py, pw, ph, 2)

def main():
    cam = None
    player = None
    entities = []

    worldChunks = [[bytearray(lib.CHUNK_SIZE), None, None] for _ in range((lib.WORLD_CHUNK_W * 2 + 1) * (lib.WORLD_CHUNK_H * 2 + 1))]
    sprtCount = 0
    tick = 0

    try:
        cam, player = initGame()
        WorldData.generateWorld(worldChunks, entities, int(player.x + player.box[0] + (player.box[2] // 2)), int(player.y + player.box[1] + (player.box[3] // 2)), False, False)
        entities = WorldData.makeEntities(worldChunks)
        print("Initalize Game")
    except Exception as e:
        print(f"Failed To Initalize: {e}")
        return
    
    tick = 0
    game = False

    while True:
        display.fill(0)
        
        if game:
            player.movement(btn)
            player.checkCollision(worldChunks)
            px = int(player.x + player.box[0] + (player.box[2] // 2))
            py = int(player.y + player.box[1] + (player.box[3] // 2))

            cam.glide(px, py)
        
            new_x, new_y = WorldData.getChunk(px, py, 0, 0)
            if player.chunk[0] != new_x or player.chunk[1] != new_y:
                WorldData.generateWorld(worldChunks, entities, px, py, False, False)
            
            Render.worldRender(worldChunks, cam, display)
            handleEntities(cam, player, entities, tick, worldChunks, 50)
            
            player.chunk = [new_x, new_y]

            pos = str(f"P: [{int(px) // lib.CUBE_W},{int(py) // lib.CUBE_H}]")
            cnk = str(f"C: {player.chunk}")

            lenTxt = len(pos)
            if lenTxt < len(cnk):
                lenTxt = len(cnk)

            display.drawFilledRectangle(0, 0, (lenTxt * 4) + 2, 16, 0)
            display.drawText(pos, 2, 2, 3)
            display.drawText(cnk, 2, 9, 3)

            tick -= 1
            if tick < 0:
                tick = 20
        else:
            if btn.buttonU.pressed():
                lib.WORLD_SEED += 1
            elif btn.buttonD.pressed():
                lib.WORLD_SEED -= 1

            display.drawText("Press A to Start..", 2, 16, 3)
            display.drawText(f"Seed: {lib.WORLD_SEED}", 2, 22, 3)

            if btn.buttonA.pressed():
                game = True
        
        lib.interlace ^= 1
        display.update()
main()
