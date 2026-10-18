# Single fixed-size world; no chunks or sliding-window state.
import math, array, os, sys
SAVE_DIR = "Saves/TinyCraft" if sys.platform == "win32" else "/Saves/TinyCraft"
SAVE_FILE = SAVE_DIR + "/player.bin"
REGION_DIR = SAVE_DIR + "/regions"
region = [0, 0, 0]  # Absolute XYZ region coordinates (32x32x16 blocks).
BLOCKS = {'Air':0,'Grass':1,'Dirt':2,'Stone':3,'Log':4,'Leaves':5,'Sand':6,'Planks':7,'Cobble':8,'Coal Ore':9,'Bedrock':10,'Coal':11}
TOOLS = {'WoodPick':0,'StonePick':1}

INTERLACE = 0

HW = 77
PH = 450
EYE = 400
DAY_MS = 360000
BAYER = (0,8,2,10,12,4,14,6,3,11,1,9,15,7,13,5)

WORLD_X = 32
WORLD_Y = 32
WORLD_Z = 16
WORLD_VOLUME = WORLD_X * WORLD_Y * WORLD_Z
world = bytearray(WORLD_VOLUME)
render_world = world  # Alias for compatibility; no second buffer.
hm = bytearray(WORLD_X * WORLD_Y)
BLOCK_INV = bytearray(256)
TOOL_INV = bytearray(16)
pos = [0, 0, 0]
P = array.array('i', [0] * 362)
T = bytearray(16 + 256 * 16 * 2)
SIN = [int(round(256 * math.sin(2 * math.pi * i / 256))) for i in range(256)]
DEPTHS = array.array('H', [65535] * (72 * 40))

def ensure_dirs():
    base = "Saves" if sys.platform == "win32" else "/Saves"
    try: os.mkdir(base)
    except OSError: pass
    try: os.mkdir(SAVE_DIR)
    except OSError: pass
    try: os.mkdir(REGION_DIR)
    except OSError: pass

def inside(x, y, z):
    return 0 <= x < WORLD_X and 0 <= y < WORLD_Y and 0 <= z < WORLD_Z

def flat_index(x, y, z):
    return x + WORLD_X * (y + WORLD_Y * z)

def get_block(x, y, z):
    if not inside(x, y, z): return 0
    return world[flat_index(x,y,z)]

def set_block(x, y, z, block, dirty=True):
    if not inside(x, y, z): return False
    world[flat_index(x,y,z)] = block
    return True

def cell(x, y, z):
    return get_block(x,y,z)

def solid(x, y, z):
    if z < 0: return True
    if z >= WORLD_Z: return False
    if x < 0 or y < 0 or x >= WORLD_X or y >= WORLD_Y: return True
    return get_block(x,y,z) != 0


def region_path(rx=None, ry=None, rz=None):
    if rx is None: rx = region[0]
    if ry is None: ry = region[1]
    if rz is None: rz = region[2]
    # Preserve old horizontal region files at Z=0.
    if rz == 0:
        return REGION_DIR + '/%d_%d.bin' % (rx, ry)
    return REGION_DIR + '/%d_%d_%d.bin' % (rx, ry, rz)

def replace_file(tmp, path):
    if hasattr(os, 'replace'):
        os.replace(tmp, path)
    else:
        try: os.remove(path)
        except OSError: pass
        os.rename(tmp, path)

def save_region():
    ensure_dirs()
    path = region_path()
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(world)
    replace_file(tmp, path)

def load_region():
    try:
        with open(region_path(), 'rb') as f:
            if f.readinto(world) != WORLD_VOLUME: return False
            return not f.read(1)
    except OSError:
        return False
