"""Standalone TinyCraft 4-direction entity sprite editor (desktop Python/Tkinter).

Change SPRITE_WIDTH and SPRITE_HEIGHT to set the dimensions for NEW projects.
Saved projects retain their own dimensions; use New Project to adopt changes.
Pixel IDs: 0 black, 1 white, 2 light gray, 3 dark gray, 4 transparent.
"""
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path

SPRITE_WIDTH = 12
SPRITE_HEIGHT = 12
MAX_SPRITE_ID = 255
DIRECTIONS = ('Front', 'Back', 'Left', 'Right')
PALETTE = ('#000000', '#ffffff', '#aaaaaa', '#555555')
CHECKER = ('#dedede', '#999999')


def blank_sprite(name, w, h):
    return {'name': name, 'faces': {direction: [4] * (w * h) for direction in DIRECTIONS}}


class EntitySpriteEditor:
    def __init__(self, root):
        self.root = root
        self.width = SPRITE_WIDTH
        self.height = SPRITE_HEIGHT
        self.sprites = {0: blank_sprite('Entity 0', self.width, self.height)}
        self.selected_id = 0
        self.direction = tk.StringVar(value='Front')
        self.brush = tk.IntVar(value=2)
        self.name_var = tk.StringVar()
        self.id_var = tk.StringVar()
        self.status = tk.StringVar(value='Create four directional sprites. 4 = transparent.')
        root.title('TinyCraft Entity Sprite Editor')
        root.geometry('920x760')
        root.minsize(690, 600)
        self.create_widgets()
        self.select_sprite(0)

    def create_widgets(self):
        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.pack(fill='x')
        ttk.Label(toolbar, text='Entity:').pack(side='left')
        self.selector = ttk.Combobox(toolbar, state='readonly', width=25)
        self.selector.pack(side='left', padx=5)
        self.selector.bind('<<ComboboxSelected>>', self.choose_sprite)
        ttk.Button(toolbar, text='+ Add', command=self.add_sprite).pack(side='left', padx=2)
        ttk.Button(toolbar, text='− Remove', command=self.remove_sprite).pack(side='left', padx=2)
        ttk.Button(toolbar, text='New Project', command=self.new_project).pack(side='right', padx=2)

        details = ttk.Frame(self.root, padding=(9, 1, 9, 7))
        details.pack(fill='x')
        ttk.Label(details, text='ID').pack(side='left')
        ttk.Entry(details, width=6, textvariable=self.id_var).pack(side='left', padx=4)
        ttk.Button(details, text='Assign ID', command=self.assign_id).pack(side='left', padx=(0, 12))
        ttk.Label(details, text='Name').pack(side='left')
        ttk.Entry(details, width=20, textvariable=self.name_var).pack(side='left', padx=4)
        ttk.Button(details, text='Rename', command=self.rename).pack(side='left')
        self.size_label = ttk.Label(details, text='')
        self.size_label.pack(side='right')

        directions = ttk.LabelFrame(self.root, text='Facing direction', padding=6)
        directions.pack(fill='x', padx=9)
        for direction in DIRECTIONS:
            ttk.Radiobutton(directions, text=direction, variable=self.direction,
                            value=direction, command=self.repaint).pack(side='left', padx=8)
        ttk.Button(directions, text='Copy facing →', command=self.copy_direction).pack(side='right', padx=5)
        ttk.Button(directions, text='Clear facing', command=self.clear_direction).pack(side='right', padx=5)

        work = ttk.Frame(self.root, padding=10)
        work.pack(fill='both', expand=True)
        left = ttk.LabelFrame(work, text='Paint pixels (click or drag)', padding=8)
        left.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.canvas = tk.Canvas(left, background='#777777', highlightthickness=0, cursor='crosshair')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda event: self.repaint())
        self.canvas.bind('<Button-1>', self.paint_at)
        self.canvas.bind('<B1-Motion>', self.paint_at)

        right = ttk.Frame(work)
        right.pack(side='left', anchor='n')
        ttk.Label(right, text='Preview').pack(anchor='w')
        self.preview = tk.Canvas(right, width=180, height=210, bg='#aaa', highlightthickness=1)
        self.preview.pack(pady=(5, 12))
        ttk.Label(right, text='Brush color').pack(anchor='w')
        self.swatches = []
        palette = ttk.Frame(right)
        palette.pack(pady=5)
        for value, name in enumerate(('Black', 'White', 'Light gray', 'Dark gray', 'Transparent')):
            swatch = tk.Canvas(palette, width=93, height=42, highlightthickness=3,
                               highlightbackground='#aaa', cursor='hand2')
            swatch.grid(row=value // 2, column=value % 2, padx=3, pady=3)
            self.paint_swatch(swatch, value)
            swatch.create_text(47, 22, text=f'{value} {name}',
                               fill='black' if value in (1, 2, 4) else 'white',
                               font=('Arial', 9, 'bold'))
            swatch.bind('<Button-1>', lambda event, n=value: self.select_brush(n))
            self.swatches.append(swatch)
        self.select_brush(2)
        ttk.Label(right, text='4 = transparent\nCheckerboard in editor', justify='left').pack(anchor='w', pady=8)

        footer = ttk.Frame(self.root, padding=9)
        footer.pack(fill='x')
        ttk.Button(footer, text='Save Project (.json)', command=self.save_project).pack(side='left', padx=3)
        ttk.Button(footer, text='Load Project', command=self.load_project).pack(side='left', padx=3)
        ttk.Button(footer, text='Export EntitySprites.py', command=self.export_python).pack(side='right', padx=3)
        ttk.Label(self.root, textvariable=self.status, padding=(12, 0, 12, 10)).pack(fill='x')
        self.refresh_selector()

    def paint_swatch(self, canvas, value):
        if value == 4:
            for row in range(2):
                for col in range(4):
                    canvas.create_rectangle(2 + col * 23, 2 + row * 21,
                                            2 + (col + 1) * 23, 2 + (row + 1) * 21,
                                            fill=CHECKER[(row + col) & 1], outline='')
        else:
            canvas.create_rectangle(2, 2, 94, 44, fill=PALETTE[value], outline='')

    def refresh_selector(self):
        self.selector['values'] = [f'{i} — {self.sprites[i]["name"]}' for i in sorted(self.sprites)]

    def choose_sprite(self, event=None):
        if self.selector.get():
            self.select_sprite(int(self.selector.get().split(' — ')[0]))

    def select_sprite(self, sprite_id):
        self.selected_id = sprite_id
        self.id_var.set(str(sprite_id))
        self.name_var.set(self.sprites[sprite_id]['name'])
        self.selector.set(f'{sprite_id} — {self.sprites[sprite_id]["name"]}')
        self.repaint()

    def select_brush(self, value):
        self.brush.set(value)
        for i, swatch in enumerate(self.swatches):
            swatch.configure(highlightbackground='#007acc' if i == value else '#aaa')

    def add_sprite(self):
        free = next((i for i in range(MAX_SPRITE_ID + 1) if i not in self.sprites), None)
        if free is None:
            messagebox.showinfo('Full', 'All sprite IDs 0–255 are used.')
            return
        name = simpledialog.askstring('New Entity', 'Name:', initialvalue=f'Entity {free}', parent=self.root)
        if name is None:
            return
        self.sprites[free] = blank_sprite(name.strip() or f'Entity {free}', self.width, self.height)
        self.refresh_selector()
        self.select_sprite(free)

    def remove_sprite(self):
        if not messagebox.askyesno('Remove', f'Remove entity {self.selected_id}?'):
            return
        del self.sprites[self.selected_id]
        if not self.sprites:
            self.sprites[0] = blank_sprite('Entity 0', self.width, self.height)
        self.refresh_selector()
        self.select_sprite(min(self.sprites))

    def assign_id(self):
        try:
            new = int(self.id_var.get())
        except ValueError:
            messagebox.showerror('Invalid ID', 'ID must be an integer from 0 to 255.')
            return
        if not 0 <= new <= MAX_SPRITE_ID:
            messagebox.showerror('Invalid ID', 'ID must be between 0 and 255.')
            return
        if new != self.selected_id and new in self.sprites:
            messagebox.showerror('ID occupied', 'Remove or reassign the existing sprite first.')
            return
        self.sprites[new] = self.sprites.pop(self.selected_id)
        self.refresh_selector()
        self.select_sprite(new)

    def rename(self):
        self.sprites[self.selected_id]['name'] = self.name_var.get().strip() or f'Entity {self.selected_id}'
        self.refresh_selector()
        self.select_sprite(self.selected_id)

    def clear_direction(self):
        self.sprites[self.selected_id]['faces'][self.direction.get()] = [4] * (self.width * self.height)
        self.repaint()

    def copy_direction(self):
        source = self.direction.get()
        dest = simpledialog.askstring('Copy facing', 'Copy to (Front/Back/Left/Right):', parent=self.root)
        if dest is None:
            return
        dest = next((d for d in DIRECTIONS if d.lower() == dest.strip().lower()), None)
        if dest is None:
            messagebox.showerror('Invalid facing', 'Use Front, Back, Left, or Right.')
            return
        self.sprites[self.selected_id]['faces'][dest] = self.sprites[self.selected_id]['faces'][source][:]
        self.direction.set(dest)
        self.repaint()

    def cell_metrics(self):
        cell = max(1, min((self.canvas.winfo_width() - 12) // self.width,
                          (self.canvas.winfo_height() - 12) // self.height))
        ox = (self.canvas.winfo_width() - self.width * cell) // 2
        oy = (self.canvas.winfo_height() - self.height * cell) // 2
        return cell, ox, oy

    def paint_at(self, event):
        cell, ox, oy = self.cell_metrics()
        x = (event.x - ox) // cell
        y = (event.y - oy) // cell
        if 0 <= x < self.width and 0 <= y < self.height:
            self.sprites[self.selected_id]['faces'][self.direction.get()][y * self.width + x] = self.brush.get()
            self.repaint()

    @staticmethod
    def draw_pixel(canvas, x0, y0, x1, y1, value, outlined=True):
        if value == 4:
            halfx = (x0 + x1) // 2
            halfy = (y0 + y1) // 2
            for a, b, c, d, color in ((x0, y0, halfx, halfy, CHECKER[0]),
                                      (halfx, y0, x1, halfy, CHECKER[1]),
                                      (x0, halfy, halfx, y1, CHECKER[1]),
                                      (halfx, halfy, x1, y1, CHECKER[0])):
                canvas.create_rectangle(a, b, c, d, fill=color, outline='')
        else:
            canvas.create_rectangle(x0, y0, x1, y1, fill=PALETTE[value], outline='')
        if outlined:
            canvas.create_rectangle(x0, y0, x1, y1, fill='', outline='#666666')

    def repaint(self):
        self.canvas.delete('all')
        self.preview.delete('all')
        self.size_label.configure(text=f'{self.width}×{self.height} pixels')
        pixels = self.sprites[self.selected_id]['faces'][self.direction.get()]
        cell, ox, oy = self.cell_metrics()
        for y in range(self.height):
            for x in range(self.width):
                value = pixels[y * self.width + x]
                self.draw_pixel(self.canvas, ox + x * cell, oy + y * cell,
                                ox + (x + 1) * cell, oy + (y + 1) * cell, value)
        pc = max(1, min(180 // self.width, 210 // self.height))
        px = (180 - self.width * pc) // 2
        py = (210 - self.height * pc) // 2
        for y in range(self.height):
            for x in range(self.width):
                self.draw_pixel(self.preview, px + x * pc, py + y * pc,
                                px + (x + 1) * pc, py + (y + 1) * pc,
                                pixels[y * self.width + x], outlined=False)

    def new_project(self):
        if not messagebox.askyesno('New project', 'Discard current project and start fresh?'):
            return
        self.width, self.height = SPRITE_WIDTH, SPRITE_HEIGHT
        self.sprites = {0: blank_sprite('Entity 0', self.width, self.height)}
        self.direction.set('Front')
        self.refresh_selector()
        self.select_sprite(0)

    def save_project(self):
        path = filedialog.asksaveasfilename(title='Save sprites', initialfile='entity-sprites.json',
                                           defaultextension='.json', filetypes=[('JSON files', '*.json')])
        if not path:
            return
        data = {'version': 1, 'width': self.width, 'height': self.height, 'sprites': self.sprites}
        try:
            Path(path).write_text(json.dumps(data, indent=2), encoding='utf-8')
            self.status.set(f'Saved {path}')
        except OSError as e:
            messagebox.showerror('Save failed', str(e))

    def load_project(self):
        path = filedialog.askopenfilename(title='Load sprites', filetypes=[('JSON files', '*.json')])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            w, h = int(data['width']), int(data['height'])
            if not (1 <= w <= 128 and 1 <= h <= 128):
                raise ValueError('Sprite dimensions must be between 1 and 128.')
            sprites = {}
            for id_string, record in data['sprites'].items():
                sprite_id = int(id_string)
                if not 0 <= sprite_id <= MAX_SPRITE_ID or sprite_id in sprites:
                    raise ValueError('Invalid or repeated sprite ID.')
                faces = {}
                for direction in DIRECTIONS:
                    pixels = record['faces'][direction]
                    if len(pixels) != w * h or any(type(pixel) is not int or not 0 <= pixel <= 4 for pixel in pixels):
                        raise ValueError(f'Invalid pixel data for {sprite_id}: {direction}')
                    faces[direction] = list(pixels)
                sprites[sprite_id] = {'name': str(record['name']), 'faces': faces}
            if not sprites:
                raise ValueError('Project has no sprites.')
            self.width, self.height, self.sprites = w, h, sprites
            self.refresh_selector()
            self.select_sprite(min(sprites))
            self.status.set(f'Loaded {path}')
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
            messagebox.showerror('Load failed', str(e))

    def export_python(self):
        path = filedialog.asksaveasfilename(title='Export Python module', initialfile='EntitySprites.py',
                                           defaultextension='.py', filetypes=[('Python source', '*.py')])
        if not path:
            return
        lines = [
            '# Generated by TinyCraft Entity Sprite Editor.',
            '# Row-major pixel data. 0=black, 1=white, 2=light gray, 3=dark gray, 4=transparent.',
            '# Directions: Front, Back, Left, Right.',
            f'SPRITE_WIDTH = {self.width}',
            f'SPRITE_HEIGHT = {self.height}',
            f'DIRECTIONS = {DIRECTIONS!r}',
            'ENTITY_SPRITES = {',
        ]
        for ident in sorted(self.sprites):
            sprite = self.sprites[ident]
            lines.append(f'    {ident}: {{')
            lines.append(f'        "name": {sprite["name"]!r},')
            for direction in DIRECTIONS:
                pixels = sprite['faces'][direction]
                lines.append(f'        "{direction}": bytes((')
                for y in range(self.height):
                    row = pixels[y * self.width:(y + 1) * self.width]
                    lines.append('            ' + ', '.join(map(str, row)) + ',')
                lines.append('        )),')
            lines.append('    },')
        lines.append('}')
        lines.append('')
        try:
            Path(path).write_text('\n'.join(lines), encoding='utf-8')
            self.status.set(f'Exported {path}')
            messagebox.showinfo('Export completed', 'EntitySprites.py is ready for integration with TinyCraft.')
        except OSError as e:
            messagebox.showerror('Export failed', str(e))


if __name__ == '__main__':
    root = tk.Tk()
    EntitySpriteEditor(root)
    root.mainloop()
