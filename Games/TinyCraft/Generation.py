import random, time
import Library as lib
from Library import BLOCKS, world, hm, pos

BEDROCK_REGION_Z = -10
CAVE_WORMS_PER_CELL = 3
CAVE_STEPS = 22


def cave_seed(cx, cy, cz):
    return ((cx * 73856093) ^ (cy * 19349663) ^
            (cz * 83492791) ^ 0x5A17C4) & 0x7fffffff


def carve_caves():
    rx, ry, rz = lib.region
    if rz > 0 or rz < BEDROCK_REGION_Z:
        return

    ox, oy, oz = rx * 32, ry * 32, rz * 16
    stone = BLOCKS['Stone']
    ore = BLOCKS['Coal Ore']

    for cz in range(rz - 2, rz + 3):
        for cy in range(ry - 1, ry + 2):
            for cx in range(rx - 1, rx + 2):
                seed = cave_seed(cx, cy, cz)
                for worm in range(CAVE_WORMS_PER_CELL):
                    seed = (seed * 1103515245 + 12345) & 0x7fffffff
                    wx = cx * 32 + 4 + seed % 24
                    seed = (seed * 1103515245 + 12345) & 0x7fffffff
                    wy = cy * 32 + 4 + seed % 24
                    seed = (seed * 1103515245 + 12345) & 0x7fffffff
                    wz = cz * 16 + 2 + seed % 12
                    
                    if worm == 0: wx = cx * 32 - 8
                    elif worm == 1: wy = cy * 32 - 8
                    else: wz = cz * 16 - 8

                    for step in range(CAVE_STEPS):
                        radius = 2 if (step % 11 == 5) else 1
                        for dz in range(-radius, radius + 1):
                            z = wz + dz - oz
                            if z < 0 or z >= 16:
                                continue
                            if rz == BEDROCK_REGION_Z and z == 0:
                                continue
                            for dy in range(-radius, radius + 1):
                                y = wy + dy - oy
                                if y < 0 or y >= 32:
                                    continue
                                for dx in range(-radius, radius + 1):
                                    if dx * dx + dy * dy + dz * dz > radius * radius + 1:
                                        continue
                                    x = wx + dx - ox
                                    if x < 0 or x >= 32:
                                        continue
                                    i = x | (y << 5) | (z << 10)

                                    if world[i] == stone or world[i] == ore:
                                        world[i] = BLOCKS['Air']
                        seed = (seed * 1103515245 + 12345) & 0x7fffffff
                        wx += (1 if worm == 0 else (seed % 3) - 1)
                        seed = (seed * 1103515245 + 12345) & 0x7fffffff
                        wy += (1 if worm == 1 else (seed % 3) - 1)
                        seed = (seed * 1103515245 + 12345) & 0x7fffffff
                        wz += (1 if worm == 2 else (seed % 3) - 1)


def gen():
    x, y, rz = lib.region
    random.seed((x * 73856093 ^ y * 19349663 ^ rz * 83492791 ^ 0x5443) & 0x7fffffff)
    ri = random.randint
    for i in range(len(world)):
        world[i] = 0
    if rz > 0:
        for i in range(len(hm)): hm[i] = 0
        return
    if rz < 0:
        for i in range(len(world)): world[i] = BLOCKS['Stone']
        for i in range(len(hm)): hm[i] = 15
        for _ in range(90):
            x = ri(1, 30)
            y = ri(1, 30)
            z = ri(1, 14)
            world[x | (y << 5) | (z << 10)] = BLOCKS['Coal Ore']
        if rz <= BEDROCK_REGION_Z:
            for i in range(lib.WORLD_X * lib.WORLD_Y):
                world[i] = BLOCKS['Bedrock']
        carve_caves()
        return
    g = [[ri(0, 255) for _ in range(9)] for _ in range(9)]
    for y in range(32):
        gy = y >> 2
        fy = y & 3
        for x in range(32):
            gx = x >> 2
            fx = x & 3
            a = g[gy][gx]
            b = g[gy][gx + 1]
            c = g[gy + 1][gx]
            d = g[gy + 1][gx + 1]
            top = a * (4 - fx) + b * fx
            bot = c * (4 - fx) + d * fx
            v = top * (4 - fy) + bot * fy
            h = 5 + (v * 6) // 4080
            hm[x | (y << 5)] = h
            sandy = h <= 6
            o = x | (y << 5)
            
            world[o] = BLOCKS["Stone"]
            for z in range(1, h + 1):
                if z == h: b_ = BLOCKS["Sand"] if sandy else BLOCKS["Grass"]
                elif z >= h - 3: b_ = BLOCKS["Sand"] if sandy else BLOCKS["Dirt"]
                else: b_ = BLOCKS["Stone"]
                world[o | (z << 10)] = b_
    
    for n in range(7):
        cx = ri(3, 28)
        cy = ri(3, 28)
        cz = ri(2, 5)
        for s in range(45):
            for d in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                x = cx + d[0]
                y = cy + d[1]
                z = cz + d[2]
                if 0 <= x < 32 and 0 <= y < 32 and z >= 1 and z <= hm[x | (y << 5)] - 2:
                    world[x | (y << 5) | (z << 10)] = BLOCKS["Air"]
            cx = max(2, min(29, cx + ri(-1, 1)))
            cy = max(2, min(29, cy + ri(-1, 1)))
            cz = max(2, min(7, cz + ri(-1, 1)))
    
    for n in range(110):
        x = ri(0, 31)
        y = ri(0, 31)
        z = ri(1, 7)
        i = x | (y << 5) | (z << 10)
        if world[i] == BLOCKS["Stone"]:
            world[i] = BLOCKS["Coal Ore"]
            if ri(0, 1) and x < 31 and world[i + 1] == BLOCKS["Stone"]:
                world[i + 1] = BLOCKS["Coal Ore"]
    
    carve_caves()

    for n in range(26):
        x = ri(3, 28)
        y = ri(3, 28)
        h = hm[x | (y << 5)]
        if h > 9 or world[x | (y << 5) | (h << 10)] != BLOCKS["Grass"]:
            continue
        for z in range(h + 1, h + 5):
            world[x | (y << 5) | (z << 10)] = BLOCKS["Log"]
        for z in range(h + 3, h + 6):
            r = 2 if z < h + 5 else 1
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if r == 2 and abs(dx) == 2 and abs(dy) == 2:
                        continue
                    i = (x + dx) | ((y + dy) << 5) | (z << 10)
                    if world[i] == BLOCKS["Air"]:
                        world[i] = BLOCKS["Leaves"]

def find_spawn():
    best = None
    for r in range(0, 12):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                x = 16 + dx
                y = 16 + dy
                z = 15
                while z > 0 and world[x | (y << 5) | (z << 10)] == 0:
                    z -= 1
                if world[x | (y << 5) | (z << 10)] in (BLOCKS["Grass"], BLOCKS["Sand"]):
                    best = (x, y, z)
                    break
            if best:
                break
        if best:
            break
    if not best:
        best = (16, 16, 12)
    pos[0] = best[0] * 256 + 128
    pos[1] = best[1] * 256 + 128
    pos[2] = (best[2] + 1) * 256

def sand_fall(x, y, z):
    zz = z + 1
    while zz < 16 and world[x | (y << 5) | (zz << 10)] == BLOCKS["Sand"]:
        lz = zz
        while lz > 0 and world[x | (y << 5) | ((lz - 1) << 10)] == 0:
            lz -= 1
        if lz != zz:
            world[x | (y << 5) | (zz << 10)] = 0
            world[x | (y << 5) | (lz << 10)] = BLOCKS["Sand"]
        zz += 1

def rtick():
    ri = random.randint
    x = ri(0, 31)
    y = ri(0, 31)
    z = 15
    while z > 0 and world[x | (y << 5) | (z << 10)] == 0:
        z -= 1
    i = x | (y << 5) | (z << 10)
    b = world[i]
    above = world[i + 1024] if z < 15 else 0
    if b == BLOCKS["Dirt"] and above == 0:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < 32 and 0 <= ny < 32:
                for nz in (z - 1, z, z + 1):
                    if 0 <= nz < 16 and world[nx | (ny << 5) | (nz << 10)] == BLOCKS["Grass"]:
                        world[i] = BLOCKS["Grass"]
                        return
    elif b == BLOCKS["Grass"] and above != 0:
        world[i] = BLOCKS["Dirt"]