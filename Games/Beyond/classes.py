import micropython
import random
import bType
import library as lib
from thumbySaves import saveData
from math import *

BIOMES = {
    0: {
        "surface": 1,
        "ground": 2,
    },
    1: {
        "surface": 1,
        "ground": 2,
    },
}

class Blocks:
    def __init__(self, x, y, size, idx):
        self.x = x
        self.y = y
        
        self.size = size
        self.idx  = idx

class Entities:
    def __init__(self, x, y, box, qStep, acc, frict, grav, jump, maxX, maxY, idx):
        self.x = x
        self.y = y
        
        self.vx = 0.0
        self.vy = 0.0
        
        self.acc   = acc
        self.frict = frict
        self.grav  = grav
        self.jump = jump
        
        self.chunk = [0, 0]
        
        self.box = box
        self.idx = idx
        
        self.maxX = maxX
        self.maxY = maxY
        
        self.qStep = qStep
        
        self.ground = False
        self.coyT = 0

        self.jump_ai = 0
        self.move_dir_ai = 0

        self.plrState = 0
        self.cursorX = 0
        self.cursorY = 0
    
    @micropython.native
    def movement(self, btn):
        if btn.buttonB.pressed():
            self.plrState ^= 1

        
        if btn.buttonL.pressed():
            self.vx -= self.acc
        if btn.buttonR.pressed():
            self.vx += self.acc

        if (self.ground or self.coyT < 10) and btn.buttonA.pressed():
            self.coyT = 10
            self.vx *= 1.5
            
            self.vy = -self.jump - abs(self.vx / 2)
            self.ground = False
        
        self.vx *= self.frict
        self.vy += self.grav
        
        if self.vy == self.maxY:
            self.vy = self.maxY
        
        self.coyT += 1
        if self.ground:
            self.coyT = 0
        
        self.ground = False
    
    @micropython.native
    def ai_movement(self, tick):
        if tick == 0:
            self.move_dir_ai = random.randint(-1, 1)
            
            if self.ground:
                rand = random.randint(0, 100)

                if rand >= 90:
                    self.jump_ai = 1

        if self.move_dir_ai == 1:
            self.vx += self.acc
        elif self.move_dir_ai == -1:
            self.vx -= self.acc

        if (self.ground or self.coyT < 10) and self.jump_ai == 1:
            self.coyT = 10
            self.vx *= 1.5
            
            self.vy = -self.jump - abs(self.vx / 3)
            self.ground = False
        
        self.vx *= self.frict
        self.vy += self.grav

        if self.vy == self.maxY:
            self.vy = self.maxY
        
        self.coyT += 1
        if self.ground:
            self.coyT = 0
        
        self.ground = False
        self.jump_ai = 0
    
    @micropython.native
    def checkCollision(self, worldChunks):
        vx = self.vx / self.qStep
        vy = self.vy / self.qStep
        
        for i in range(self.qStep):
            collided = False
            for s in range(2):
                if s == 0: self.x += vx
                elif s == 1: self.y += vy
                
                objPos, hit, side = WorldData.collisionCheck(worldChunks, self, s)

                if hit and side != None:
                    if s == 0:
                        if side == "Left":
                            vx = 0
                            self.vx = 0
                            self.x = (objPos[0] + lib.CUBE_W) - self.box[0]
                        elif side == "Right":
                            vx = 0
                            self.vx = 0
                            self.x = objPos[0] - self.box[2]
                    elif s == 1:
                        if side == "Top":
                            vy = 0
                            self.vy = 0
                            self.y = (objPos[1] + lib.CUBE_H) - self.box[1]
                        elif side == "Bottom":
                            vy = 0
                            self.vy = 0
                            self.y = objPos[1] - self.box[3]
                            self.ground = True

class Camera:
    def __init__(self, x, y, acc):
        self.x = x
        self.y = y
        
        self.acc = acc
    
    @micropython.native
    def glide(self, x, y):
        target_x = x - lib.w_Half
        target_y = y - lib.h_Half
    
        dx = target_x - self.x
        dy = target_y - self.y
    
        self.x += dx * self.acc >> 6
        self.y += dy * self.acc >> 6

class WorldData:
    @staticmethod
    @micropython.native
    def makeEntities(worldChunks):
        entities = []
        entInterlace = 0

        for _, chunk in enumerate(worldChunks):
            cx = chunk[1]
            cy = chunk[2]

            rand = random.randint(0, 5)
            for i in range(rand):
                entities.append([Entities(0.0 + (cx * lib.WORLD_CHUNK_W), 0.0 + (cy * lib.WORLD_CHUNK_H), [0, 0, 5, 10], 4, 1.2, 0.6, 0.8, 5.0, 2.0, 5.0, 0), _, entInterlace])
                entInterlace ^= 1
        return entities

    @staticmethod
    @micropython.native
    def saveChunks(_, chunk, entities):
        chunkEnts = []
        entRemove = []
        for idx, ent in enumerate(entities):
            if ent[1] == _:
                # x, y, box, qStep, acc, frict, grav, jump, maxX, maxY, idx
                chunkEnts.append([ent[0].x, ent[0].y, ent[0].box, ent[0].qStep, ent[0].acc, ent[0].frict, ent[0].grav, ent[0].jump, ent[0].maxX, ent[0].maxY, ent[0].idx])
                entRemove.append(idx)

        saveData.setName(f"b_chunks/{lib.WORLD_SEED}/{int(chunk[1])}_{int(chunk[2])}")
        saveData.delItem("Chunks")
        saveData.delItem("Entities")

        saveData.setItem("Chunks", chunk[0])
        if len(chunkEnts) > 0:
            saveData.setItem("Entities", chunkEnts)

        saveData.save()

        for rem in reversed(entRemove):
            del entities[rem]

    @staticmethod
    @micropython.native
    def loadChunks(cx, cy, idx, chunk, entities):
        chunk[1] = cx
        chunk[2] = cy
        saveData.setName(f"b_chunks/{lib.WORLD_SEED}/{int(cx)}_{int(cy)}")

        chunkData = saveData.getItem("Chunks")
        entList = saveData.getItem("Entities")

        if chunkData is None:
            return False
        
        chunk[0] = chunkData
        if not entList is None:
            for ent in entList:
                entities.append([Entities(ent[0], ent[1], ent[2], ent[3], ent[4], ent[5], ent[6], ent[7], ent[8], ent[9], ent[10]), idx, random.randint(0, 1)])
        
        return True

    @staticmethod
    @micropython.native
    def getChunk(x, y, px, py):
        chunk_x = ((x // lib.CUBE_W) // lib.CHUNK_W) + px
        chunk_y = ((y // lib.CUBE_H) // lib.CHUNK_H) + py
        
        return int(chunk_x), int(chunk_y)
    
    @staticmethod
    @micropython.native
    def noise2d(x, y):
        n = x * 374761393 + y * 668265263 + (lib.WORLD_SEED * 1442695040888963407)
        
        n ^= n >> 13
        n *= 1274126177

        n ^= n >> 16
        n *= 2246822519

        n ^= n >> 13

        return n & 0x7FFFFFFF
    
    @staticmethod
    @micropython.native
    def fractalNoise2d(x, y):
        n = 0
        
        n += WorldData.noise2d(x >> 5, y >> 5) & 255
        n += (WorldData.noise2d(x >> 4, y >> 4) & 255) >> 1
        n += (WorldData.noise2d(x >> 3, y >> 3) & 255) >> 2
        n += (WorldData.noise2d(x >> 2, y >> 2) & 255) >> 3
    
        return n
    
    @staticmethod
    @micropython.native
    def collisionCheck(worldChunks, obj, idx):
        chunk_cube_w = lib.CHUNK_CUBE_W
        chunk_cube_h = lib.CHUNK_CUBE_H
    
        chunk_w = lib.CHUNK_W
        chunk_h = lib.CHUNK_H
        
        cube_w = lib.CUBE_W
        cube_h = lib.CUBE_H
    
        ox = int(obj.x + obj.box[0])
        oy = int(obj.y + obj.box[1])
        ow = ox + obj.box[2]
        oh = oy + obj.box[3]

        for _, chunk in enumerate(worldChunks):
            cx = chunk[1] * chunk_cube_w
            cy = chunk[2] * chunk_cube_h
            cw = cx + chunk_cube_w
            ch = cy + chunk_cube_h
            # print(f"Chunk: [{cx}, {cy}, {cw}, {ch}]")
            
            canDetect = False
            if ox < cw and ow > cx and oy < ch and oh > cy:
                canDetect = True
            
            if not canDetect:
                continue

            chunk_x = chunk[1] * chunk_cube_w
            chunk_y = chunk[2] * chunk_cube_h

            for y in range(chunk_h):
                for x in range(chunk_w):
                    block = chunk[0][y * chunk_w + x]
                    if block == 0:
                        continue
    
                    bx = chunk_x + x * cube_w
                    by = chunk_y + y * cube_h
    
                    bw = bx + cube_w
                    bh = by + cube_h
                    
                    if ox < bw and ow > bx and oy < bh and oh > by:
                        side = None
                        if idx == 0:
                            pen_left   = bw - ox
                            pen_right  = ow - bx
                            
                            if pen_left < pen_right:
                                side = "Left"
                            else:
                                side = "Right"
                        else:
                            pen_top    = bh - oy
                            pen_bottom = oh - by
                            
                            if pen_top < pen_bottom:
                                side = "Top"
                            else:
                                side = "Bottom"
                            
                        return [bx, by], True, side
        return None, False, None
    
    @staticmethod
    @micropython.native
    def getBiome(world_x, world_y):
        n = WorldData.fractalNoise2d(world_x, world_y)
        return 0 if n < 128 else 1
    
    @staticmethod
    @micropython.native
    def generateWorld(worldChunks, entities, px, py, save, load):
        chunk_cube_w = lib.CHUNK_CUBE_W
        chunk_cube_h = lib.CHUNK_CUBE_H
    
        chunk_w = lib.CHUNK_W
        chunk_h = lib.CHUNK_H
        
        cube_w = lib.CUBE_W
        cube_h = lib.CUBE_H
        
        plr_chunk_x = (px // chunk_cube_w)
        plr_chunk_y = (py // chunk_cube_h)
        
        required = []
        for pos in lib.positions:
            cx = plr_chunk_x + pos[0]
            cy = plr_chunk_y + pos[1]
            required.append((cx, cy))
        
        missing = []
        for cx, cy in required:
            exists = False
    
            for chunk in worldChunks:
                if chunk[1] == cx and chunk[2] == cy:
                    exists = True
                    break
    
            if not exists:
                missing.append((cx, cy))
    
        if not missing:
            return
        
        missing_idx = 0
        for _, chunk in enumerate(worldChunks):
            if missing_idx >= len(missing):
                break
    
            keep = False
    
            for cx, cy in required:
                if chunk[1] == cx and chunk[2] == cy:
                    keep = True
                    break
    
            if keep:
                continue
            
            if save:
                WorldData.saveChunks(_, chunk, entities)

            cx, cy = missing[missing_idx]
            missing_idx += 1

            chunk[1] = cx
            chunk[2] = cy

            if load:
                loaded = WorldData.loadChunks(cx, cy, _, chunk, entities)
                if loaded:
                    continue
            
            chunk[0] = bytearray(lib.CHUNK_SIZE)
    
            chunk_world_x = cx * chunk_cube_w
            chunk_world_y = cy * chunk_cube_h
            
            biome = WorldData.getBiome(chunk_world_x, chunk_world_y)
            b = BIOMES[biome]

            for yy in range(chunk_h):
                row = yy * chunk_w
    
                for xx in range(chunk_w):
                    world_x = chunk_world_x + xx * cube_w
                    world_y = chunk_world_y + yy * cube_h
    
                    n0 = 20 + (WorldData.fractalNoise2d(world_x, 0) >> 3)
                    height = 20 + (WorldData.fractalNoise2d(world_x, n0) >> 3)
    
                    i = row + xx
    
                    if world_y > height:
                        chunk[0][i] = b["ground"]
                    elif world_y >= height - cube_h:
                        chunk[0][i] = b["surface"]
                    else:
                        chunk[0][i] = 0
                    
                    if yy != 0:
                        if chunk[0][(yy-1) * chunk_w + xx] == 0 and chunk[0][i] == 2:
                            chunk[0][i] = 1
                        
                        if chunk[0][(yy-1) * chunk_w + xx] != 0 and chunk[0][i] == 1:
                            chunk[0][i] = 2

class Render:
    @staticmethod
    @micropython.native
    def worldRender(worldChunks, cam, gfx):
        cam_x = int(cam.x)
        cam_y = int(cam.y)
        
        chunk_cube_w = lib.CHUNK_CUBE_W
        chunk_cube_h = lib.CHUNK_CUBE_H
        
        cube_w = lib.CUBE_W
        cube_h = lib.CUBE_H
        
        chunk_w = lib.CHUNK_W
        chunk_h = lib.CHUNK_H
        for chunk in worldChunks:
            chunk_world_x = chunk[1] * chunk_cube_w
            chunk_world_y = chunk[2] * chunk_cube_h
            
            if (chunk_world_x + chunk_cube_w < cam.x or chunk_world_x > cam.x + 72 or chunk_world_y + chunk_cube_h < cam.y or chunk_world_y > cam.y + 40):
                continue
            
            for by in range(chunk_h):
                row = by * chunk_w
                for bx in range(chunk_w):
                    block = chunk[0][row + bx]
                    if block == 0:
                        continue
                    
                    world_x = chunk_world_x + (bx * cube_w)
                    world_y = chunk_world_y + (by * cube_h)
            
                    x = world_x - cam_x
                    y = world_y - cam_y
                    
                    if ((x + cube_w < 0 or x > 72) or (y + cube_h < 0 or y > 40)):
                        continue
                    
                    bType.Tiles[block].x = x
                    bType.Tiles[block].y = y
                    gfx.drawSprite(bType.Tiles[block])
                    # gfx.drawFilledRectangle(x, y, cube_w, cube_h, block)