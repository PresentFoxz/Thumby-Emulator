# Player controls, collision, movement and health.
# Edit these constants to tune the character without touching Main.py.
from Library import (pos, SIN, HW, PH, EYE, solid, cell, WORLD_X, WORLD_Y, WORLD_Z)

WALK_SPEED = 1100             # Fixed-point units / second
TURN_SPEED = 450              # Yaw units / second before acceleration
TURN_ACCELERATION = 2         # Added turn speed per held millisecond
TURN_ACCEL_LIMIT_MS = 500
LOOK_SPEED = 700              # Pitch units / second
MAX_PITCH = 950
JUMP_VELOCITY = 2500
GRAVITY = 7168
MAX_FALL_SPEED = 6000
AUTO_HOP_HEIGHT = 300
AUTO_HOP_REACH = 110
HEALTH_MAX = 20
REGEN_INTERVAL_MS = 3500
FALL_SAFE_BLOCKS = 3
ITEM_CYCLE_REPEAT_MS = 300
MINING_IDLE_DELAY_MS = 250  # Hold A without D-pad this long before mining

def hits(x, y, z, hw=HW, ph=PH):
    x0 = (x - hw) >> 8
    x1 = (x + hw) >> 8
    y0 = (y - hw) >> 8
    y1 = (y + hw) >> 8
    z0 = z >> 8
    z1 = (z + ph - 1) >> 8

    for cx in range(x0, x1 + 1):
        for cy in range(y0, y1 + 1):
            for cz in range(z0, z1 + 1):
                if solid(cx, cy, cz):
                    return True

    return False

def move_axis(a, d, p=pos, hw=HW, ph=PH):
    if d == 0:
        return False

    s = 1 if d > 0 else -1
    n = d * s

    while n > 0:
        st = n if n < 64 else 64
        base = p[a]
        p[a] = base + s * st

        if hits(p[0], p[1], p[2], hw, ph):
            lo = 0
            hi = st

            while hi - lo > 1:
                mid = (lo + hi) >> 1
                p[a] = base + s * mid

                if hits(p[0], p[1], p[2], hw, ph):
                    hi = mid
                else:
                    lo = mid

            p[a] = base + s * lo
            return True

        n -= st

    return False

def pick(fx, fy, fz):
    """March along the view direction. Returns (hit cell, previous cell) or None."""
    x = pos[0]
    y = pos[1]
    z = pos[2] + EYE
    lx = x >> 8
    ly = y >> 8
    lz = z >> 8
    sx = fx >> 3
    sy = fy >> 3
    sz = fz >> 3
    for _ in range(40):
        x += sx
        y += sy
        z += sz
        cx = x >> 8
        cy = y >> 8
        cz = z >> 8
        if cx != lx or cy != ly or cz != lz:
            if cx < 0 or cy < 0 or cx >= WORLD_X or cy >= WORLD_Y or cz < 0:
                return None
            if cz < WORLD_Z and cell(cx, cy, cz) != 0:
                return (cx, cy, cz), (lx, ly, lz)
            lx = cx
            ly = cy
            lz = cz
    return None

class Player:
    def __init__(self, spawn, yaw=0, pitch=0, health=HEALTH_MAX):
        self.spawn = spawn
        self.yaw = yaw
        self.pitch = pitch
        self.hp = health
        self.vertical_speed = 0
        self.peak = pos[2]
        self.regen_elapsed = 0
        self.turn_held_ms = 0
        self.item_held_ms = 0
        self.mine_idle_ms = 0
        # Explicit equipped state. IDs may overlap across categories.
        self.equipped_category = 'block'  # 'block' or 'tool'
        self.equipped_id = None

    def equip_category(self, category):
        if category not in ('block', 'tool'):
            return
        self.equipped_category = category
        self.validate_equipped()

    def validate_equipped(self):
        from Items import hot
        available = hot(self.equipped_category)
        if self.equipped_id not in available:
            self.equipped_id = available[0] if available else None

    def cycle_equipped(self, step):
        from Items import cycle_item
        self.equipped_id = cycle_item(self.equipped_category, self.equipped_id, step)

    def handle_input(self, keys, previous, dt, items):
        # D-pad: forward/back and left/right strafe.
        # A + D-pad: look up/down and turn left/right.
        # B + Left/Right: cycle items; B + Up: jump.
        # Hold A with no D-pad for a short delay to start mining.
        u, d, l, r, a, b = (keys[k] for k in ('U', 'D', 'L', 'R', 'A', 'B'))
        forward, sideways, jump = 0, 0, False
        controlling_view = a and (u or d or l or r)

        if a:
            self.item_held_ms = 0
            self.turn(l, r, dt)
            self.look(u, d, dt)
            self.mine_idle_ms = 0 if controlling_view else self.mine_idle_ms + dt
        else:
            self.mine_idle_ms = 0
            self.turn_held_ms = 0

            if b and (l or r):
                self.item_held_ms += dt
                if ((l and not previous['L']) or (r and not previous['R']) or self.item_held_ms >= ITEM_CYCLE_REPEAT_MS):
                    self.item_held_ms = 0
                    self.cycle_equipped(-1 if l else 1)
            else:
                self.item_held_ms = 0
                sideways = (1 if r else 0) - (1 if l else 0)
            forward = (1 if u else 0) - (1 if d else 0)
            jump = b and u
        
        mining_allowed = a and not controlling_view and self.mine_idle_ms >= MINING_IDLE_DELAY_MS
        return not mining_allowed, (forward, sideways), jump

    def look(self, up, down, dt):
        if up: self.pitch += LOOK_SPEED * dt // 1000
        if down: self.pitch -= LOOK_SPEED * dt // 1000
        self.pitch = max(-MAX_PITCH, min(MAX_PITCH, self.pitch))

    def turn(self, left, right, dt):
        if left or right:
            self.turn_held_ms += dt
            speed = TURN_SPEED + min(self.turn_held_ms, TURN_ACCEL_LIMIT_MS) * TURN_ACCELERATION
            amount = speed * dt // 1000
            if left: self.yaw += amount
            if right: self.yaw -= amount
            self.yaw &= 4095
        else: self.turn_held_ms = 0

    def walk(self, movement, dt):
        forward, sideways = movement
        if not forward and not sideways: return False

        yaw_idx = (self.yaw >> 4) & 255
        distance = dt * WALK_SPEED // 1000

        if forward and sideways: distance = (distance * 181) >> 8

        c = SIN[(yaw_idx + 64) & 255]
        s = SIN[yaw_idx]
        
        dx = ((c * forward + s * sideways) * distance) >> 8
        dy = ((s * forward - c * sideways) * distance) >> 8
        blocked_x = move_axis(0, dx)
        blocked_y = move_axis(1, dy)

        if not (blocked_x or blocked_y): return False

        hop_x = pos[0] + (AUTO_HOP_REACH if dx > 0 else -AUTO_HOP_REACH) if blocked_x else pos[0]
        hop_y = pos[1] + (AUTO_HOP_REACH if dy > 0 else -AUTO_HOP_REACH) if blocked_y else pos[1]

        return not hits(hop_x, hop_y, pos[2] + AUTO_HOP_HEIGHT)

    def gravity_and_jump(self, dt, jumping):
        if hits(pos[0], pos[1], pos[2] - 1):
            self.peak = pos[2]
            if jumping: self.vertical_speed = JUMP_VELOCITY
        steps = (dt + 39) // 40
        sub = dt // steps

        for _ in range(steps):
            self.vertical_speed = max(-MAX_FALL_SPEED, self.vertical_speed - GRAVITY * sub // 1000)
            if move_axis(2, self.vertical_speed * sub // 1000):
                if self.vertical_speed < 0:
                    fall = (self.peak - pos[2]) >> 8
                    if fall > FALL_SAFE_BLOCKS: self.hp -= fall - FALL_SAFE_BLOCKS

                    self.peak = pos[2]
                self.vertical_speed = 0
            elif pos[2] > self.peak: self.peak = pos[2]

    def update(self, movement, jump, dt):
        hop = self.walk(movement, dt)
        self.gravity_and_jump(dt, jump or hop)
        self.regen_elapsed += dt
        if self.regen_elapsed >= REGEN_INTERVAL_MS:
            self.regen_elapsed = 0
            if 0 < self.hp < HEALTH_MAX: self.hp += 1
        return self.hp <= 0

    def respawn(self):
        pos[0], pos[1], pos[2] = self.spawn
        self.vertical_speed = 0
        self.hp = HEALTH_MAX
        self.peak = pos[2]

import random

ENTITY_HW = 60
ENTITY_PH = 220
ENTITY_SPEED = 10
ENTITY_JUMP = 65
ENTITY_GRAVITY = 6
ENTITY_MAX_FALL = 80

ENTITY_SEARCH_RADIUS = 4
ENTITY_MAX_PATH_NODES = 24
ENTITY_TARGET_ATTEMPTS = 3
ENTITY_STUCK_LIMIT = 12

ENTITY_STATES = {}


def EntityCanStand(bx, by, bz, hw=ENTITY_HW, ph=ENTITY_PH):
    x = (bx << 8) + 128
    y = (by << 8) + 128
    z = bz << 8

    if not (0 <= bx < WORLD_X and 0 <= by < WORLD_Y and 0 <= bz < WORLD_Z): return False
    return (not hits(x, y, z, hw, ph) and hits(x, y, z - 1, hw, ph))


def EntityPath(sx, sy, sz, gx, gy, gz, hw=ENTITY_HW, ph=ENTITY_PH):

    start = (sx, sy, sz)
    goal = (gx, gy, gz)

    if start == goal: return []

    queue = [start]
    parents = {start: None}
    head = 0

    directions = (
        (1, 0), (-1, 0),
        (0, 1), (0, -1)
    )

    while head < len(queue) and len(queue) < ENTITY_MAX_PATH_NODES:
        current = queue[head]
        head += 1

        x, y, z = current

        for dx, dy in directions:
            nx = x + dx
            ny = y + dy

            for dz in (0, 1, -1):
                nz = z + dz
                nxt = (nx, ny, nz)

                if nxt in parents: continue
                if abs(nx - sx) > ENTITY_SEARCH_RADIUS: continue
                if abs(ny - sy) > ENTITY_SEARCH_RADIUS: continue
                if not EntityCanStand(nx, ny, nz, hw, ph): continue
                
                if dz == 1:
                    if hits((x << 8) + 128, (y << 8) + 128, (z + 1) << 8, hw, ph): continue
                    if hits((nx << 8) + 128, (ny << 8) + 128, (nz + 1) << 8, hw, ph): continue

                parents[nxt] = current

                if nxt == goal:
                    path = []
                    node = nxt

                    while node != start:
                        path.append(node)
                        node = parents[node]

                    path.reverse()
                    return path

                queue.append(nxt)

                if len(queue) >= ENTITY_MAX_PATH_NODES:
                    break

    return None

def EntityFindTarget(x, y, z, last_block=None, failed_block=None, hw=ENTITY_HW, ph=ENTITY_PH):
    sx = x >> 8
    sy = y >> 8
    sz = z >> 8

    current = (sx, sy, sz)

    for _ in range(ENTITY_TARGET_ATTEMPTS):
        gx = sx + random.randint(-ENTITY_SEARCH_RADIUS, ENTITY_SEARCH_RADIUS)
        gy = sy + random.randint(-ENTITY_SEARCH_RADIUS, ENTITY_SEARCH_RADIUS)

        for gz in (sz, sz + 1, sz - 1):
            target = (gx, gy, gz)

            if target == current: continue
            if target == last_block: continue
            if target == failed_block: continue

            if not EntityCanStand(gx, gy, gz, hw, ph): continue
            path = EntityPath(sx, sy, sz, gx, gy, gz, hw, ph)
            if path: return path

    return []

def initStates(amt):
    for i in range(amt):
        state = {
            "path": [],
            "vz": 0,
            "stuck": 0,
            "last_block": None,
            "failed_block": None,
            "target": None,
            "last_pos": None
        }
        ENTITY_STATES[i] = state

def GetEntityState(i):
    state = ENTITY_STATES.get(i)

    if state is None:
        state = {
            "path": [],
            "vz": 0,
            "stuck": 0,
            "last_block": None,
            "failed_block": None,
            "target": None,
            "last_pos": None
        }
        ENTITY_STATES[i] = state

    return state


def EntityPhysics(x, y, z, state, HW=ENTITY_HW, PH=ENTITY_PH, GRAVITY=ENTITY_GRAVITY, MAX_FALL=ENTITY_MAX_FALL):
    p = [x, y, z]
    vz = state["vz"]

    grounded = hits(x, y, z - 1, HW, PH)

    if not grounded or vz > 0: vz = max(-MAX_FALL, vz - GRAVITY)
    else: vz = 0

    if vz != 0:
        if move_axis(2, vz, p, HW, PH): vz = 0

    state["vz"] = vz
    return p[0], p[1], p[2]


def MoveEntity(x, y, z, yaw, state, HW=ENTITY_HW, PH=ENTITY_PH, SPEED=ENTITY_SPEED, JUMP=ENTITY_JUMP, GRAVITY=ENTITY_GRAVITY, MAX_FALL=ENTITY_MAX_FALL):
    p = [x, y, z]
    path = state["path"]
    
    if not path:
        path = EntityFindTarget(x, y, z, state["last_block"], state["failed_block"], HW, PH)

        state["path"] = path
        state["stuck"] = 0
        state["last_pos"] = None

        if path: state["target"] = path[-1]
        else: state["target"] = None

    if path:
        tx, ty, tz = path[0]

        target_x = (tx << 8) + 128
        target_y = (ty << 8) + 128
        target_z = tz << 8

        dx = target_x - p[0]
        dy = target_y - p[1]
        
        if (abs(dx) < 32 and
            abs(dy) < 32 and
            abs(p[2] - target_z) < 32):

            state["last_block"] = (tx, ty, tz)
            path.pop(0)

            state["stuck"] = 0
            state["last_pos"] = None

            if not path: state["target"] = None

        else:
            distance = max(1, int((dx * dx + dy * dy) ** 0.5))

            mx = dx * SPEED // distance
            my = dy * SPEED // distance

            grounded = hits(p[0], p[1], p[2] - 1, HW, PH)
            
            if (grounded and target_z > p[2] + 64 and state["vz"] <= 0): state["vz"] = JUMP
                
            blocked_x = move_axis(0, mx, p, HW, PH)
            blocked_y = move_axis(1, my, p, HW, PH)
            
            previous = state["last_pos"]
            if previous is not None:
                moved = (abs(p[0] - previous[0]) + abs(p[1] - previous[1]))

                if moved < 8 or blocked_x or blocked_y: state["stuck"] += 1
                else: state["stuck"] = 0

            state["last_pos"] = (p[0], p[1])
            
            if state["stuck"] >= ENTITY_STUCK_LIMIT:
                state["failed_block"] = state["target"]

                state["path"] = []
                state["target"] = None
                state["last_pos"] = None
                state["stuck"] = 0

            best = 0
            best_dot = -999999999

            for a in range(0, 256, 8):
                dot = (SIN[(a + 64) & 255] * dx + SIN[a] * dy )

                if dot > best_dot:
                    best_dot = dot
                    best = a

            yaw = best << 4

    return p[0], p[1], p[2], yaw