# Blocks and tools have independent IDs and inventories.
from Library import BLOCK_INV, TOOL_INV, BLOCKS, TOOLS, pos, HW, PH, get_block, set_block, inside
from Generation import sand_fall

# Block IDs are looked up by name, so they may be reassigned in Library.
HARDNESS = {'Grass':500, 'Dirt':450, 'Stone':2600, 'Log':1100,
            'Leaves':250, 'Sand':400, 'Planks':1000,
            'Cobble':2600, 'Coal Ore':3000}


def equipped_tier(player):
    if player.equipped_category != 'tool':
        return 0
    t = player.equipped_id
    if t == TOOLS['StonePick'] and TOOL_INV[t]:
        return 2
    if t == TOOLS['WoodPick'] and TOOL_INV[t]:
        return 1
    return 0


def break_time(b, player):
    name = None
    for n, ident in BLOCKS.items():
        if ident == b:
            name = n
            break

    h = HARDNESS.get(name, 0)
    if name in ('Stone', 'Cobble', 'Coal Ore'):
        tier = equipped_tier(player)
        if tier == 1:
            h = h * 35 // 100
        elif tier == 2:
            h = h * 20 // 100
    return h


def drop_of(b, player):
    tier = equipped_tier(player)
    if b in (BLOCKS['Stone'], BLOCKS['Cobble']):
        return BLOCKS['Cobble'] if tier else 0
    if b == BLOCKS['Coal Ore']:
        return BLOCKS['Coal'] if tier else 0
    if b == BLOCKS['Grass']:
        return BLOCKS['Dirt']
    return b


def give_block(b, count=1):
    if 0 < b < len(BLOCK_INV):
        BLOCK_INV[b] = min(99, BLOCK_INV[b] + count)


def give_tool(t, count=1):
    if 0 <= t < len(TOOL_INV):
        TOOL_INV[t] = min(99, TOOL_INV[t] + count)


def hot(category='block'):
    if category == 'tool':
        return [i for i in sorted(TOOLS.values()) if TOOL_INV[i]]
    return [i for i in sorted(BLOCKS.values()) if i and BLOCK_INV[i]]


def cycle_item(category, current, step):
    available = hot(category)
    if not available: return None
    if current in available:
        return available[(available.index(current) + step) % len(available)]
    return available[0]

# Recipe: title, ingredients ((category, id, quantity), ...), output category,
# output ID, count, UI requirements string.
RECIPES = (
    ('4 Planks', (('block', BLOCKS['Log'], 1),), 'block', BLOCKS['Planks'], 4, '1 Wood'),
    ('Wood Pick', (('block', BLOCKS['Planks'], 4),), 'tool', TOOLS['WoodPick'], 1, '4 Planks'),
    ('Stone Pick', (('block', BLOCKS['Cobble'], 3), ('block', BLOCKS['Planks'], 2)),
     'tool', TOOLS['StonePick'], 1, '3 Cobl 2 Plnk'),
)


def inventory(category):
    return TOOL_INV if category == 'tool' else BLOCK_INV


def can_craft(recipe):
    for category, ident, quantity in recipe[1]:
        if inventory(category)[ident] < quantity: return False
    category, ident = recipe[2], recipe[3]
    if category == 'tool' and TOOL_INV[ident]: return False
    return inventory(category)[ident] <= 99 - recipe[4]


def craft(recipe):
    if not can_craft(recipe): return False
    for category, ident, quantity in recipe[1]:
        inventory(category)[ident] -= quantity
    category, ident, quantity = recipe[2], recipe[3], recipe[4]
    if category == 'tool': give_tool(ident, quantity)
    else: give_block(ident, quantity)
    return True


class BlockActions:
    PLACE_REPEAT_MS = 400

    def __init__(self, player):
        self.player = player
        self.mine_target = None
        self.mine_elapsed = 0
        self.place_elapsed = 0

    @property
    def selected(self):
        return self.player.equipped_id

    def mine(self, active, target, dt):
        if not active or not target or target[0][2] <= 0:
            self.mine_target = None
            self.mine_elapsed = 0
            return 0, False
        cell = target[0]
        block = get_block(cell[0], cell[1], cell[2])
        needed = break_time(block, self.player)
        if needed <= 0:
            self.mine_target = None
            self.mine_elapsed = 0
            return 0, False
        if cell != self.mine_target:
            self.mine_target = cell
            self.mine_elapsed = 0
        self.mine_elapsed += dt
        if self.mine_elapsed < needed:
            return self.mine_elapsed * 8 // needed, False
        set_block(cell[0], cell[1], cell[2], BLOCKS['Air'])
        give_block(drop_of(block, self.player))
        sand_fall(cell[0], cell[1], cell[2])
        self.mine_target = None
        self.mine_elapsed = 0
        self.player.validate_equipped()
        return 0, True

    def place(self, pressed, previously_pressed, allow, target, dt):
        fire = False
        if pressed:
            if not previously_pressed:
                self.place_elapsed = 0
                fire = True
            else:
                self.place_elapsed += dt
                if self.place_elapsed >= self.PLACE_REPEAT_MS:
                    self.place_elapsed = 0
                    fire = True
        player = self.player
        b = player.equipped_id
        if player.equipped_category != 'block' or b is None:
            return False
        if b == BLOCKS['Air'] or b not in BLOCKS.values():
            return False
        if not (fire and allow and target and BLOCK_INV[b]): return False
        x, y, z = target[1]
        if not inside(x, y, z): return False

        if get_block(x, y, z) != BLOCKS['Air']: return False
        x0, y0, z0 = x << 8, y << 8, z << 8
        overlap = (pos[0] + HW > x0 and pos[0] - HW < x0 + 256 and
                   pos[1] + HW > y0 and pos[1] - HW < y0 + 256 and
                   pos[2] + PH > z0 and pos[2] < z0 + 256)
        if overlap: return False
        set_block(x, y, z, b)
        BLOCK_INV[b] -= 1
        if b == BLOCKS['Sand']: sand_fall(x, y, z - 1)
        player.validate_equipped()
        return True

    def validate_selection(self):
        self.player.validate_equipped()
