import time, gc, os, struct, sys
import thumbyButton as btn

sys.path.append("/Games/TinyCraft/")
from thumbyGrayscale import display as gfx
import Library as lib
from Library import (SAVE_DIR, SAVE_FILE, DAY_MS, EYE, world, render_world, BLOCK_INV, TOOL_INV, pos, P, T, BLOCKS, TOOLS)
from Renderer import build_tables, setup_view, render, render_entities, hud
from Generation import gen, find_spawn, rtick, BEDROCK_REGION_Z
from Entities import Player, pick, MoveEntity, initStates, GetEntityState, EntityPhysics, hits
from Items import RECIPES, can_craft, craft, hot, BlockActions
from Textures import apply_textures
from EntityRender import ENTITIES
import random

gfx.setFont("/lib/font3x5.bin", 3, 5, 1)

# Sprite ID, X, Y, Z, Yaw, Width, Height
ENT_LIMIT = 10
for i in range(ENT_LIMIT):
    ENTITIES.append([
        random.randint(0, 1),
        random.randint(0, 4096),
        4096,
        random.randint(0, 4096),
        0,
        192,
        384
    ])

def text(s, x, y):
    gfx.drawText(s, x, y, 1)

def draw_list(lines, cur, info):
    gfx.fill(0)
    n = len(lines)
    start = max(0, min(cur - 1, n - 4)) if n > 4 else 0

    for k in range(min(4, n - start)):
        i = start + k
        text(("> " if i == cur else "  ") + lines[i], 0, k * 8)
    
    text(info, 0, 33)
    gfx.update()

def bag_screen(player):
    tab = player.equipped_category
    cur = 0

    while True:
        bag = TOOL_INV if tab == 'tool' else BLOCK_INV
        names = TOOLS if tab == 'tool' else BLOCKS

        entries = [
            (name, ident, bag[ident])
            for name, ident in names.items()
            if bag[ident] and (tab == 'tool' or ident != BLOCKS['Air'])
        ]

        if cur >= len(entries):
            cur = max(0, len(entries) - 1)

        # Draw the inventory screen
        gfx.fill(0)

        title = "< TOOLS >" if tab == 'tool' else "< BAG >"
        text(title, max(0, (72 - len(title) * 6) // 2), 0)

        if not entries:
            text("(empty)", 15, 14)
        else:
            start = max(0, min(cur - 1, len(entries) - 3))

            for k in range(min(3, len(entries) - start)):
                i = start + k
                name, ident, count = entries[i]

                prefix = ">" if i == cur else " "
                line = prefix + name + " " + str(count)

                text(line[:12], 0, 9 + k * 8)
            
        text("A:Equip | B:Back", 0, 33)
        gfx.update()
        
        if btn.buttonL.justPressed() or btn.buttonR.justPressed():
            tab = 'tool' if tab == 'block' else 'block'
            cur = 0
        
        elif btn.buttonU.justPressed() and cur > 0:
            cur -= 1
        
        elif btn.buttonD.justPressed() and cur < len(entries) - 1:
            cur += 1
            
        elif btn.buttonA.justPressed():
            if entries:
                player.equipped_category = tab
                player.equipped_id = entries[cur][1]
                player.validate_equipped()
                return

        elif btn.buttonB.justPressed(): return


SAVE_MAGIC = b'TC07'  # Edge-travel player metadata (separate region files).

def save_game(yaw, pitch, hp, tod):
    try:
        lib.save_region()
        lib.ensure_dirs()
        tmp = SAVE_FILE + '.tmp'
        with open(tmp, 'wb') as f:
            f.write(SAVE_MAGIC)
            f.write(struct.pack('<10i', pos[0], pos[1], pos[2], yaw, pitch, hp, tod, lib.region[0], lib.region[1], lib.region[2]))
            f.write(BLOCK_INV)
            f.write(TOOL_INV)
        lib.replace_file(tmp, SAVE_FILE)
        return 'Saved!'
    except Exception as e:
        print('Save error:', e)
        return 'Save failed'

def load_game():
    try:
        with open(SAVE_FILE, 'rb') as f:
            magic = f.read(4)
            if magic == b'TC07':
                hdr = f.read(40)
                if len(hdr) != 40: return None
                values = struct.unpack('<10i', hdr)
                new_region = values[7:10]
            elif magic == b'TC06':
                # Backward compatibility with old XY-only save files.
                hdr = f.read(36)
                if len(hdr) != 36: return None
                values = struct.unpack('<9i', hdr)
                new_region = (values[7], values[8], 0)
            else:
                return None
            bag = f.read(len(BLOCK_INV))
            tools = f.read(len(TOOL_INV))
            if len(bag) != len(BLOCK_INV) or len(tools) != len(TOOL_INV) or f.read(1): return None
        lib.region[:] = new_region
        if not lib.load_region(): return None
        BLOCK_INV[:] = bag
        TOOL_INV[:] = tools
        pos[:] = values[:3]
        return values[3], values[4], values[5], values[6]
    except Exception as e:
        print('Load error:', e)
        return None

def edge_direction(fx, fy, fz):
    # B at a world border, looking outward in the dominant axis.
    x, y, z = pos
    margin = 2 * 256
    ax, ay, az = abs(fx), abs(fy), abs(fz)
    if az >= ax and az >= ay:
        if fz > 100 and z >= lib.WORLD_Z * 256 - margin: return (0, 0, 1)
        if fz < -100 and z < margin and lib.region[2] > BEDROCK_REGION_Z: return (0, 0, -1)
    elif ax >= ay:
        if fx > 100 and x >= lib.WORLD_X * 256 - margin: return (1, 0, 0)
        if fx < -100 and x < margin: return (-1, 0, 0)
    else:
        if fy > 100 and y >= lib.WORLD_Y * 256 - margin: return (0, 1, 0)
        if fy < -100 and y < margin: return (0, -1, 0)
    return None

def enter_region(dx, dy, dz, player, tod):
    # Preserve the other two coordinates while changing only the crossed axis.
    if lib.region[2] + dz < BEDROCK_REGION_Z:
        return False

    old_region = tuple(lib.region)
    old_pos = tuple(pos)

    # Compute the arrival point without changing the live player position.
    nx, ny, nz = old_pos
    if dx:
        nx = 384 if dx > 0 else (lib.WORLD_X - 2) * 256 + 128
    if dy:
        ny = 384 if dy > 0 else (lib.WORLD_Y - 2) * 256 + 128
    if dz > 0:
        nz = 256  # Near the bottom of the upper region
    elif dz < 0:
        nz = (lib.WORLD_Z - 3) * 256  # Near the top of the lower region

    try:
        lib.save_region()
        lib.region[:] = [old_region[0] + dx,
                         old_region[1] + dy,
                         old_region[2] + dz]
        if not lib.load_region():
            gen()
            lib.save_region()

        # Never spawn inside solid terrain. Keep old region if blocked.
        if hits(nx, ny, nz):
            lib.region[:] = old_region
            lib.load_region()
            print('Region entrance blocked')
            return False

    except Exception as e:
        print('Region transition error:', e)
        lib.region[:] = old_region
        lib.load_region()
        return False

    pos[:] = [nx, ny, nz]
    player.spawn = tuple(pos)
    player.peak = nz
    player.vertical_speed = 0
    print('Entered region', lib.region[0], lib.region[1], lib.region[2])
    return True

def has_save():
    try:
        os.stat(SAVE_FILE)
        return True
    except OSError:
        return False

def wait_menu_release():
    """Consume the A+B opening gesture before accepting menu input."""
    while btn.buttonA.pressed() or btn.buttonB.pressed():
        gfx.update()


def crafting_screen():
    """Browse all recipes by output category; no persistent menu state."""
    tab = 'block'
    cur = 0
    while True:
        recipes = [r for r in RECIPES if r[2] == tab]
        gfx.fill(0)
        heading = '< BLOCKS >' if tab == 'block' else '< TOOLS >'
        text(heading, max(0, (72 - len(heading) * 6) // 2), 0)

        if not recipes:
            text('(none)', 8, 15)
            info = 'L/R:Tab B:Back'
        else:
            if cur >= len(recipes):
                cur = len(recipes) - 1
            start = max(0, min(cur - 1, len(recipes) - 3))
            for row in range(min(3, len(recipes) - start)):
                i = start + row
                r = recipes[i]
                text(('>' if i == cur else ' ') + r[0], 0, 9 + row * 8)
            selected = recipes[cur]
            if selected[2] == 'tool' and TOOL_INV[selected[3]]:
                info = 'Owned'
            elif can_craft(selected):
                info = selected[5] + ' OK'
            else:
                info = 'Need ' + selected[5]
        text(info[:12], 0, 33)
        gfx.update()

        if btn.buttonL.justPressed() or btn.buttonR.justPressed():
            tab = 'tool' if tab == 'block' else 'block'
            cur = 0
        elif btn.buttonU.justPressed() and cur > 0:
            cur -= 1
        elif btn.buttonD.justPressed() and cur < len(recipes) - 1:
            cur += 1
        elif btn.buttonA.justPressed() and recipes:
            chosen = recipes[cur]
            if can_craft(chosen):
                craft(chosen)
        elif btn.buttonB.justPressed():
            return


def menu(state, player):
    """Main menu; A+B opening press cannot trigger a menu action."""
    entries = ['Crafting', 'Bag', 'Detail', 'Help', 'Save', 'Resume']
    cur = 0
    draw_list(entries, cur, 'A: open')
    wait_menu_release()

    while True:
        e = entries[cur]
        if e == 'Detail':
            info = 'A: ' + ('HIGH' if state['ps'] == 1 else 'LOW(fast)')
        elif e == 'Save':
            info = 'A: save game'
        elif e == 'Resume':
            info = 'A: resume'
        else:
            info = 'A: open'
        draw_list(entries, cur, info)

        if btn.buttonU.justPressed() and cur > 0:
            cur -= 1
        elif btn.buttonD.justPressed() and cur < len(entries) - 1:
            cur += 1
        elif btn.buttonA.justPressed():
            if e == 'Crafting':
                crafting_screen()
            elif e == 'Bag':
                bag_screen(player)
            elif e == 'Help':
                help_screen()
            elif e == 'Detail':
                state['ps'] = 2 if state['ps'] == 1 else 1
                state['auto'] = False
            elif e == 'Save':
                state['msg'] = save_game(state['yaw'], state['pitch'], state['hp'], state['tod'])
                return
            else:
                return
        elif btn.buttonB.justPressed():
            return

def help_screen():
    pages = (
        ("-- MOVE --", "DPad:   walk", "A+DPad: turn", "Up+B:   jump", "(auto-hops!)"),
        ("- Inv -", "Hold A: mine", "B: place", "B+L/R: Cycle", "Inventory"),
        ("-- MENU --", "Press A + B", "Craft Planks", "then Pickaxe", "Saves by itself"),
    )

    for pg in pages:
        gfx.fill(0)
        for i in range(5):
            text(pg[i], 0, i * 8)
        text(">", 66, 32)
        gfx.update()
        
        while True:
            if btn.buttonA.justPressed():
                break
            if btn.buttonB.justPressed():
                return

def title(can_load):
    gfx.fill(0)
    text("TINYCRAFT", 9, 4)
    if can_load:
        text("A: Continue", 0, 20)
        text("B: New world", 0, 30)
    else:
        text("A: New world", 0, 24)

    gfx.update()

    while True:
        gfx.update()

        if btn.buttonA.justPressed():
            return can_load

        if can_load and btn.buttonB.justPressed():
            return False

def banner(s1, s2=""):
    gfx.fill(0)
    text(s1, 0, 10)
    text(s2, 0, 22)
    gfx.update()
def get_buffer():
    try:
        return gfx.gfx.buffer, gfx.gfx.shading, False
    except Exception:
        return bytearray(360), bytearray(360), True

def ambient(tod):
    p = tod // 88
    if p < 2400:
        return 16
    if p < 2900:
        return 16 - ((p - 2400) * 10) // 500
    if p < 3500:
        return 6
    return 6 + ((p - 3500) * 10) // 600

def read_buttons():
    return {'U': btn.buttonU.pressed(), 'D': btn.buttonD.pressed(),
            'L': btn.buttonL.pressed(), 'R': btn.buttonR.pressed(),
            'A': btn.buttonA.pressed(), 'B': btn.buttonB.pressed()}

def ambient(tod):
    p = tod // 88
    if p < 2400: return 16
    if p < 2900: return 16 - ((p - 2400) * 10) // 500
    if p < 3500: return 6
    return 6 + ((p - 3500) * 10) // 600

def main():
    build_tables()
    apply_textures(T)

    buf, sha, fallback = get_buffer()
    gfx.setFPS(20)
    gc.collect()
    for i in range(len(BLOCK_INV)): BLOCK_INV[i] = 0
    for i in range(len(TOOL_INV)): TOOL_INV[i] = 0

    result = None
    if title(has_save()):
        banner('Loading', 'world...')
        result = load_game()
    fresh = result is None
    if fresh:
        banner('Generating', 'world...')
        for i in range(len(BLOCK_INV)): BLOCK_INV[i] = 0
        for i in range(len(TOOL_INV)): TOOL_INV[i] = 0
        lib.region[:] = [0, 0, 0]
        gen()
        find_spawn()
        yaw, pitch, hp, tod = 0, 0, 20, 0
    else:
        yaw, pitch, hp, tod = result
        old_pos = (pos[0], pos[1], pos[2])
        find_spawn()
        spawn = (pos[0], pos[1], pos[2])
        pos[0], pos[1], pos[2] = old_pos
    if fresh:
        spawn = (pos[0], pos[1], pos[2])
        help_screen()

    player = Player(spawn, yaw, pitch, max(1, hp))

    player.validate_equipped()
    actions = BlockActions(player)
    state = {'ps': 1, 'auto': True, 'msg': ''}
    previous = {'U': False, 'D': False, 'L': False, 'R': False, 'A': False, 'B': False}
    message, message_ms, slow_frames = '', 0, 0
    dirty, since_save = False, 0
    saved_pos = (pos[0], pos[1], pos[2])
    last = time.ticks_ms()
    P[8] = 12 * 4096

    entity_tick = 0

    initStates(ENT_LIMIT)

    while True:
        now = time.ticks_ms()
        dt = max(1, min(150, time.ticks_diff(now, last)))
        last = now
        tod = (tod + dt) % DAY_MS
        keys = read_buttons()
        lib.INTERLACE ^= 1

        if keys['A'] and keys['B'] and (not previous['A'] or not previous['B']):
            state.update({'yaw': player.yaw, 'pitch': player.pitch,
                          'hp': player.hp, 'tod': tod, 'msg': ''})
            menu(state, player)
            if state['msg']:
                message, message_ms = state['msg'], 1500
                since_save, dirty = 0, False
                saved_pos = (pos[0], pos[1], pos[2])
            else:
                dirty = True
            actions.validate_selection()
            previous = {'U': False, 'D': False, 'L': False, 'R': False, 'A': True, 'B': True}
            last = time.ticks_ms()
            continue

        alternate, walking, jumping = player.handle_input(keys, previous, dt, actions)
        died = player.update(walking, jumping, dt)
        if died:
            banner('YOU DIED')
            time.sleep_ms(1500)
            player.respawn()
            last = time.ticks_ms()
            continue

        fx, fy, fz = setup_view(player.yaw, player.pitch, state['ps'])
        target = pick(fx, fy, fz)
        if target:
            P[3], P[4], P[5] = target[0]
        else:
            P[3], P[4], P[5] = -1, -1, -1

        P[6], mined = actions.mine(keys['A'] and not alternate, target, dt)
        # B at the outer border travels to the adjacent saved region.
        direction = edge_direction(fx, fy, fz) if not keys['A'] else None
        traveled = False
        if direction and keys['B'] and not previous['B']:
            banner('Moving to', 'next region...')
            traveled = enter_region(direction[0], direction[1], direction[2], player, tod)
            if traveled:
                message = save_game(player.yaw, player.pitch, player.hp, tod)
                message_ms = 1200
                dirty, since_save = False, 0
                saved_pos = tuple(pos)
                actions = BlockActions(player)
                previous = keys
                last = time.ticks_ms()
                continue
        placed = actions.place(keys['B'] and not direction, previous['B'],
                               not keys['A'] and not keys['U'], target, dt)
        dirty = dirty or mined or placed
        actions.validate_selection()
        rtick()

        since_save += dt
        if since_save >= 45000:
            since_save = 0
            moved = (abs(pos[0] - saved_pos[0]) > 768 or
                     abs(pos[1] - saved_pos[1]) > 768)
            if dirty or moved:
                message = save_game(player.yaw, player.pitch, player.hp, tod)
                message_ms = 900
                dirty = False
                saved_pos = (pos[0], pos[1], pos[2])
            
        amb = ambient(tod)
        P[0], P[1], P[2] = pos[0], pos[1], pos[2] + EYE
        P[7], P[9], P[10] = state['ps'], amb, (amb - 2) >> 2
        t0 = time.ticks_ms()
        P[360] = player.yaw
        P[361] = player.pitch
        
        entity_tick = (entity_tick + 1) % 4
        for i, ent in enumerate(ENTITIES):
            if ent[0] == 0: continue
            if i % 4 != entity_tick: continue

            entState = GetEntityState(i)
            
            x, y, z, yaw = MoveEntity(ent[1], ent[2], ent[3], ent[4], entState)
            x, y, z = EntityPhysics(x, y, z, entState)

            ent[1] = x
            ent[2] = y
            ent[3] = z
            ent[4] = yaw
        
        render(buf, sha, world, P, T)
        render_entities(buf, sha, P)
        elapsed = time.ticks_diff(time.ticks_ms(), t0)
        if state.get('auto', False) and state.get('ps', 0) == 1:
            if elapsed > 150:
                slow_frames += 1
                if slow_frames > 6:
                    state['ps'], state['auto'] = 2, False
                    message, message_ms = 'Detail: LOW', 1500
            else:
                slow_frames = 0
        hud(buf, sha, player.equipped_category, player.equipped_id, player.hp)
        if fallback:
            gfx.blit((buf, sha), 0, 0, 72, 40, -1, 0, 0)
        if message_ms > 0:
            message_ms -= dt
            for x in range(72): buf[x] = 0
            text(message, 0, 0)
        gfx.update()
        previous = keys

main()