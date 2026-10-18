
from Library import SIN
from EntitySprites import ENTITY_SPRITES, SPRITE_WIDTH, SPRITE_HEIGHT

ENTITIES = []
PITCH_SQUASH = 192

def facing(sprite_yaw, ex, ey, player_x, player_y):
    a = (sprite_yaw >> 4) & 255
    fx = SIN[(a + 64) & 255]
    fy = SIN[a]
    vx = player_x - ex
    vy = player_y - ey
    
    front = vx * fx + vy * fy
    side = vx * fy - vy * fx
    
    if abs(front) >= abs(side):
        return 'Front' if front >= 0 else 'Back'
    return 'Right' if side >= 0 else 'Left'


def draw_sprites(buf, sha, depths, pos, yaw, pitch, ps, interlace):
    if not ENTITIES: return

    yaw_index = (yaw >> 4) & 255
    pitch_index = (pitch >> 4) & 255
    
    sy = SIN[yaw_index]
    cy = SIN[(yaw_index + 64) & 255]
    sp = SIN[pitch_index]
    cp = SIN[(pitch_index + 64) & 255]
    
    fx = (cp * cy) >> 8
    fy = (cp * sy) >> 8
    fz = sp
    
    rx, ry = sy, -cy
    ux = -((sp * cy) >> 8)
    uy = -((sp * sy) >> 8)
    uz = cp
    
    ncol = 72 // ps
    nrow = 40 // ps
    visible = []
    
    for instance in ENTITIES:
        sid, ex, ey, ez, eyaw, width, height = instance
        if sid == 0: continue

        record = ENTITY_SPRITES.get(sid)
        if record is None: continue
        dx = ex - pos[0]
        dy = ey - pos[1]
        dz = ez + (height >> 1) - pos[2]
        forward = (dx * fx + dy * fy + dz * fz) >> 8
        if forward <= 32 or forward > 12 * 256:
            continue
        right = (dx * rx + dy * ry) >> 8
        up = (dx * ux + dy * uy + dz * uz) >> 8
        
        sx = 36 + (right * 256) // (forward * 5)
        sy_screen = 20 - (up * 256) // (forward * 5)
        screen_w = max(1, (width * 256) // (forward * 5))
        screen_h = max(1, (height * 256) // (forward * 5))
        
        pitch_amount = min(256, abs(pitch) * 256 // 1024)
        squash = 256 - ((pitch_amount * PITCH_SQUASH) >> 8)
        screen_h = max(1, (screen_h * squash) >> 8)

        left = sx - (screen_w >> 1)
        top = sy_screen - (screen_h >> 1)
        if left >= 72 or left + screen_w <= 0 or top >= 40 or top + screen_h <= 0:
            continue
        direction = facing(eyaw, ex, ey, pos[0], pos[1])
        pixels = record[direction]
        
        visible.append((forward, left, top, screen_w, screen_h, pixels))
    
    visible.sort(reverse=True)
    for depth, left, top, width, height, pixels in visible:
        sprite_t = depth << 4
        
        x_start = max(0, left // ps)
        x_end = min(ncol, (left + width + ps - 1) // ps)
        y_start = max(0, top // ps)
        y_end = min(nrow, (top + height + ps - 1) // ps)
        
        for ly in range(y_start, y_end):
            screen_y = ly * ps + ps // 2
            sy_tex = (screen_y - top) * SPRITE_HEIGHT // height
            
            if sy_tex < 0 or sy_tex >= SPRITE_HEIGHT: continue
        
            rowoff = sy_tex * SPRITE_WIDTH
            for lx in range(x_start, x_end):
                if ((lx + ly) & 1) != interlace: continue
                if sprite_t >= depths[ly * ncol + lx]: continue
            
                screen_x = lx * ps + ps // 2
                sx_tex = (screen_x - left) * SPRITE_WIDTH // width
                
                if sx_tex < 0 or sx_tex >= SPRITE_WIDTH: continue
                color = pixels[rowoff + sx_tex]
                if color == 4: continue
                
                if color == 2: color = 3
                elif color == 3: color = 2
                
                for j in range(ps):
                    yy = ly * ps + j
                    bit = 1 << (yy & 7)
                    mask = 255 ^ bit
                    rowbase = (yy >> 3) * 72 + lx * ps
                    for i in range(ps):
                        k = rowbase + i
                        
                        if color & 1: buf[k] |= bit
                        else: buf[k] &= mask
                        
                        if color & 2: sha[k] |= bit
                        else: sha[k] &= mask
