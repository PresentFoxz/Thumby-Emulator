# Viper raycaster, texture generation and HUD.
import micropython
from micropython import const
import Library as lib
import array
from EntityRender import draw_sprites

WX = const(32)
WY = const(32)
WZ = const(16)
COLB = const(24)
ROWB = const(240)
TOPT = const(16)
SIDET = const(16 + 256 * 16)

from Library import (BAYER, world, P, T, SIN, BLOCK_INV, TOOL_INV, TOOLS, DEPTHS)
from Items import hot

def build_tables():
    for i in range(16):
        T[i] = BAYER[i]
    
    for b in range(256):
        for k in range(16):
            T[TOPT + b * 16 + k] = 2
            T[SIDET + b * 16 + k] = 2

# ----------------------------------------------------------------- renderer
@micropython.viper
def trace(world: ptr8, P: ptr32, T: ptr8) -> int:
    # Ray skips faces whose sampled texel is 4; writes hit data to P[14..18].
    px = int(P[0])
    py = int(P[1])
    pz = int(P[2])
    maxt = int(P[8])
    dx = int(P[11])
    dy = int(P[12])
    dz = int(P[13])
    sx = 1
    ax = dx
    if dx < 0:
        sx = 0 - 1
        ax = 0 - dx
    if ax < 1:
        ax = 1
    sy = 1
    ay = dy
    if dy < 0:
        sy = 0 - 1
        ay = 0 - dy
    if ay < 1:
        ay = 1
    sz = 1
    az = dz
    if dz < 0:
        sz = 0 - 1
        az = 0 - dz
    if az < 1:
        az = 1
    tdx = 1048576 // ax
    tdy = 1048576 // ay
    tdz = 1048576 // az
    fx = px & 255
    fy = py & 255
    fz = pz & 255
    tmx = (tdx * fx) >> 8
    if sx > 0:
        tmx = (tdx * (256 - fx)) >> 8
    tmy = (tdy * fy) >> 8
    if sy > 0:
        tmy = (tdy * (256 - fy)) >> 8
    tmz = (tdz * fz) >> 8
    if sz > 0:
        tmz = (tdz * (256 - fz)) >> 8
    x = px >> 8
    y = py >> 8
    z = pz >> 8
    t = 0
    face = 0
    hit = 0
    texel = 0
    n = 36
    while n > 0:
        n -= 1
        if tmx < tmy:
            if tmx < tmz:
                x += sx
                t = tmx
                tmx += tdx
                face = 0
            else:
                z += sz
                t = tmz
                tmz += tdz
                face = 2
        else:
            if tmy < tmz:
                y += sy
                t = tmy
                tmy += tdy
                face = 1
            else:
                z += sz
                t = tmz
                tmz += tdz
                face = 2
        if t > maxt:
            break
        if x < 0 or x >= WX or y < 0 or y >= WY:
            break
        if z < 0 or z >= WZ:
            break
        b = int(world[x + y * WX + z * (WX * WY)])
        if b != 0:
            # Sample the texture at this precise ray/face intersection.
            # A transparent texel (4) lets this ray continue to the next face.
            if face == 0:
                ua = py + ((t * dy) >> 12)
                va = pz + ((t * dz) >> 12)
            elif face == 1:
                ua = px + ((t * dx) >> 12)
                va = pz + ((t * dz) >> 12)
            else:
                ua = px + ((t * dx) >> 12)
                va = py + ((t * dy) >> 12)

            u = (ua >> 6) & 3
            v = (va >> 6) & 3
            if face != 2: v = 3 - v

            k = u | (v << 2)
            if face == 2: texel = int(T[TOPT + b * 16 + k])
            else: texel = int(T[SIDET + b * 16 + k])

            if texel != 4:
                hit = b
                P[22] = texel
                P[23] = ua
                P[24] = va
                P[25] = u
                P[26] = v
                break
    P[14] = x
    P[15] = y
    P[16] = z
    P[17] = t
    P[18] = face
    return hit

@micropython.viper
def shade(T: ptr8, P: ptr32, hit: int) -> int:
    # Only called for the highlighted block. Texture pixel was read in trace().
    color = int(P[22])
    ua = int(P[23])
    va = int(P[24])
    u = int(P[25])
    v = int(P[26])
    face = int(P[18])
    mprog = int(P[6])
    u16 = (ua >> 4) & 15
    v16 = (va >> 4) & 15

    if u16 == 0 or u16 == 15 or v16 == 0 or v16 == 15:
        if color == 0:
            return 1
        return 0
    if mprog > 0:
        if (((u * 5) ^ (v * 3) ^ face) & 7) < mprog:
            return 0
    return color

@micropython.viper
def put(buf: ptr8, sha: ptr8, P: ptr32):
    ps = int(P[7])
    cx = int(P[19])
    cy = int(P[20])
    color = int(P[21])
    if color == 2: color = 3
    elif color == 3: color = 2

    if ps == 1:
        yy = cy
        k = cx + (yy >> 3) * 72
        bit = 1 << (yy & 7)
        if color & 1: buf[k] |= bit
        else: buf[k] &= 255 ^ bit
        
        if color & 2: sha[k] |= bit
        else: sha[k] &= 255 ^ bit
        return

    for j in range(ps):
        yy = cy * ps + j
        k = cx * ps + (yy >> 3) * 72
        bit = 1 << (yy & 7)
        for i in range(ps):
            if color & 1: buf[k + i] |= bit
            else: buf[k + i] &= 255 ^ bit

            if color & 2: sha[k + i] |= bit
            else: sha[k + i] &= 255 ^ bit

@micropython.viper
def render(buf: ptr8, sha: ptr8, world: ptr8, P: ptr32, T: ptr8):
    interlace = int(lib.INTERLACE)
    ps = int(P[7])
    skyl = int(P[10])

    ncol = 72 // ps
    nrow = 40 // ps
    depths = ptr16(DEPTHS)
    for i in range(ncol * nrow): depths[i] = 65535
    
    for cx in range(ncol):
        ox = int(P[COLB + cx * 3])
        oy = int(P[COLB + cx * 3 + 1])
        oz = int(P[COLB + cx * 3 + 2])

        P[19] = cx
        for cy in range(nrow):
            dz = oz + int(P[ROWB + cy * 3 + 2])
            P[11] = ox + int(P[ROWB + cy * 3])
            P[12] = oy + int(P[ROWB + cy * 3 + 1])
            P[13] = dz

            if ((cx + cy) & 1) != interlace: continue

            hit = int(trace(world, P, T))
            if hit != 0:
                depth = int(P[17])
            
                if depth > 65535:
                    depth = 65535
                elif depth < 0:
                    depth = 0
            
                depths[cy * ncol + cx] = depth

            if hit != 0:
                tl = int(P[22])
                if (int(P[14]) == int(P[3]) and
                    int(P[15]) == int(P[4]) and
                    int(P[16]) == int(P[5])):
                    tl = int(shade(T, P, hit))
            else:
                brightness = skyl + (dz >> 7)

                if brightness < 4: tl = 0
                elif brightness < 8: tl = 3
                elif brightness < 12: tl = 2
                else: tl = 1

            P[20] = cy
            P[21] = tl
            put(buf, sha, P)

def render_entities(buf, sha, P):
    draw_sprites(
        buf, sha, DEPTHS,
        (P[0], P[1], P[2]),
        P[360], P[361],
        P[7], lib.INTERLACE
    )

def setup_view(yaw, pitch, ps):
    yi = (yaw >> 4) & 255
    pi = (pitch >> 4) & 255
    sy = SIN[yi]
    cy = SIN[(yi + 64) & 255]
    sp = SIN[pi]
    cp = SIN[(pi + 64) & 255]
    fx = (cp * cy) >> 8
    fy = (cp * sy) >> 8
    fz = sp
    rx = sy
    ry = -cy
    ux = -((sp * cy) >> 8)
    uy = -((sp * sy) >> 8)
    uz = cp

    for i in range(72 // ps):
        a = (((2 * i + 1) * ps - 72) * 5) >> 1
        o = COLB + i * 3
        P[o] = fx + ((a * rx) >> 8)
        P[o + 1] = fy + ((a * ry) >> 8)
        P[o + 2] = fz
    
    for j in range(40 // ps):
        b = ((40 - (2 * j + 1) * ps) * 5) >> 1
        o = ROWB + j * 3
        P[o] = (b * ux) >> 8
        P[o + 1] = (b * uy) >> 8
        P[o + 2] = (b * uz) >> 8
    
    return fx, fy, fz

DIG = []
DIG_ROWS = ("111101101101111", "010110010010111", "111001111100111",
            "111001111001111", "101101111001001", "111100111001111",
            "111100111101111", "111001001001001", "111101111101111",
            "111101111001111")

for _d in DIG_ROWS:
    _cols = []
    for _c in range(3):
        _v = 0
        for _r in range(5):
            if _d[_r * 3 + _c] == "1": _v |= 1 << _r
        _cols.append(_v)
    DIG.append(_cols)

ICONL = (0, 9, 5, 7, 5, 6, 11, 9, 6, 7, 3)

def icon_level(category, ident):
    if category == 'tool': return 10 if ident == TOOLS['StonePick'] else 7
    return ICONL[ident] if 0 <= ident < len(ICONL) else 8

def draw_num(buf, x, n):
    s = str(n)
    for ch in s:
        g = DIG[ord(ch) - 48]
        for c in range(3):
            buf[288 + x + c] |= g[c] << 2
        x += 4

def crosshair_pixel(buf, sha, x, y, color):
    k = x + (y >> 3) * 72
    bit = 1 << (y & 7)
    mask = 255 ^ bit

    if color == 1:
        buf[k] |= bit
        sha[k] &= mask
    else:
        buf[k] &= mask
        sha[k] &= mask


def hud(buf, sha, category, selected, hp):
    for x in range(72):
        buf[288 + x] &= 1

    entries = hot(category)
    n = len(entries)

    if n:
        si = entries.index(selected) if selected in entries else 0
        start = max(0, min(si - 2, n - 5)) if n > 5 else 0

        for k in range(min(5, n - start)):
            ident = entries[start + k]
            x0 = k * 8
            lvl = icon_level(category, ident)

            for c in range(5):
                col = 0
                for r in range(5):
                    if lvl > BAYER[(c & 3) | ((r & 3) << 2)]:
                        col |= 1 << r
                buf[288 + x0 + 1 + c] |= col << 2

            if ident == selected:
                for c in range(7):
                    buf[288 + x0 + c] |= 0x82
                buf[288 + x0] |= 0xFE
                buf[288 + x0 + 6] |= 0xFE

        if selected in entries:
            bag = TOOL_INV if category == 'tool' else BLOCK_INV
            draw_num(buf, 41, bag[selected])

    for i in range(20): buf[288 + 51 + i] |= 0x38 if i < hp else 0x10
    for cx, cy in ((36, 18), (36, 22), (34, 20), (38, 20), (35, 19), (37, 19), (35, 21), (37, 21)): crosshair_pixel(buf, sha, cx, cy, 0)
    for cx, cy in ((36, 20), (35, 20), (37, 20), (36, 19), (36, 21)): crosshair_pixel(buf, sha, cx, cy, 1)
