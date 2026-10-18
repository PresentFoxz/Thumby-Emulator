"""TinyCraft grayscale 4x4 texture editor. Requires desktop Python 3 + Tkinter."""
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path

# Texture IDs 1..255 are editable; ID 0 is reserved for air.
MAX_ID = 255
PALETTE = ('#000000', '#ffffff', '#aaaaaa', '#555555', '#d0d0d0')  # 4 = transparent (checkerboard in editor)
BLOCKS = [(1, 'Grass'), (2, 'Dirt'), (3, 'Stone'), (4, 'Wood'),
          (5, 'Leaves'), (6, 'Sand'), (7, 'Planks'), (8, 'Cobble'),
          (9, 'CoalOre'), (10, 'Bedrock')]
SPEC = {1:(9,2,5,2),2:(5,2,5,2),3:(7,1,7,1),4:(6,1,4,1),5:(6,3,6,3),
        6:(11,1,11,1),7:(9,0,9,0),8:(6,3,6,3),9:(7,1,7,1),10:(3,2,3,2)}

def to_palette(value):
    return (0, 3, 2, 1)[max(0, min(3, int(value) // 4))]

def defaults():
    seed = 4242
    def rnd(n):
        nonlocal seed
        seed = (seed * 75 + 74) % 65537
        return seed % n
    result = {}
    for block_id, (tb, tn, sb, sn) in SPEC.items():
        top, side = [], []
        for v in range(4):
            for u in range(4):
                t = tb + (rnd(2 * tn + 1) - tn if tn else 0)
                s = sb + (rnd(2 * sn + 1) - sn if sn else 0)
                if block_id == 1:
                    if v == 3: s = 9 + rnd(3) - 1
                    elif v == 2 and rnd(2): s = 8
                elif block_id == 4:
                    t = 7 if (u in (1,2) and v in (1,2)) else 4
                    s = 5 if (u & 1) else 3
                elif block_id == 7:
                    t = s = 9 if v % 2 == 0 else 7
                elif block_id == 9 and rnd(5) < 2:
                    t = s = 2
                top.append(to_palette(t))
                side.append(to_palette(s))
        result[block_id] = {'name': dict(BLOCKS)[block_id], 'Top': top,
                            'Side': side, 'enabled': {'Top': True, 'Side': True}}
    return result

def new_entry(name):
    return {'name': name, 'Top': [2] * 16, 'Side': [2] * 16,
            'enabled': {'Top': True, 'Side': True}}

class Editor:
    def __init__(self, root):
        self.root = root
        root.title('TinyCraft Texture Editor — grayscale + transparent (4)')
        root.geometry('830x680')
        root.minsize(790, 600)
        self.data = defaults()
        self.selected_id = 3
        self.face = tk.StringVar(value='Side')
        self.brush = tk.IntVar(value=2)
        self.block_name = tk.StringVar()
        self.block_id = tk.StringVar()
        self.enabled = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='Edit block IDs independently. Disabled and missing faces export as null (light gray).')
        self.make_widgets()
        self.refresh_selector()
        self.select_block(3)

    def make_widgets(self):
        toolbar = ttk.Frame(self.root, padding=10)
        toolbar.pack(fill='x')
        ttk.Label(toolbar, text='Texture:').pack(side='left')
        self.selector = ttk.Combobox(toolbar, state='readonly', width=23)
        self.selector.pack(side='left', padx=6)
        self.selector.bind('<<ComboboxSelected>>', self.choose_block)
        ttk.Button(toolbar, text='+ Add', command=self.add_block).pack(side='left', padx=3)
        ttk.Button(toolbar, text='− Remove', command=self.remove_block).pack(side='left', padx=3)
        ttk.Label(toolbar, text='IDs 1–255', foreground='#666').pack(side='right')

        details = ttk.Frame(self.root, padding=(12, 2, 12, 8))
        details.pack(fill='x')
        ttk.Label(details, text='Block ID:').pack(side='left')
        ttk.Entry(details, width=5, textvariable=self.block_id).pack(side='left', padx=(4, 6))
        ttk.Button(details, text='Assign ID', command=self.assign_id).pack(side='left', padx=(0, 15))
        ttk.Label(details, text='Name:').pack(side='left')
        ttk.Entry(details, width=18, textvariable=self.block_name).pack(side='left', padx=5)
        ttk.Button(details, text='Rename', command=self.rename).pack(side='left')

        facebar = ttk.Frame(self.root, padding=(12, 0, 12, 5))
        facebar.pack(fill='x')
        for face in ('Top', 'Side'):
            ttk.Radiobutton(facebar, text=face, value=face, variable=self.face,
                            command=self.change_face).pack(side='left', padx=(0, 14))
        ttk.Checkbutton(facebar, text='This face has texture data', variable=self.enabled,
                        command=self.toggle_enabled).pack(side='left', padx=(12, 0))
        ttk.Button(facebar, text='Reset face to light gray', command=self.reset_face).pack(side='right')

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill='both', expand=True)
        left = ttk.LabelFrame(main, text='Paint 4×4 texture', padding=10)
        left.pack(side='left', anchor='n', padx=(0, 16))
        self.paint = tk.Canvas(left, width=320, height=320, highlightthickness=0, cursor='crosshair')
        self.paint.pack()
        self.paint.bind('<Button-1>', self.paint_at)
        self.paint.bind('<B1-Motion>', self.paint_at)

        right = ttk.Frame(main)
        right.pack(side='left', fill='both', expand=True)
        ttk.Label(right, text='Preview (or light gray if data disabled)').pack(anchor='w')
        self.preview = tk.Canvas(right, width=240, height=240,
                                 highlightthickness=1, highlightbackground='#888')
        self.preview.pack(anchor='w', pady=(7, 10))
        ttk.Label(right, text='Brush color').pack(anchor='w')
        palette = ttk.Frame(right)
        palette.pack(anchor='w', pady=6)
        self.palette_buttons = []
        for idx, name in enumerate(('Black', 'White', 'L-gray', 'D-gray', 'Transparent')):
            swatch = tk.Canvas(palette, width=95, height=48, highlightthickness=3,
                               highlightbackground='#aaa', cursor='hand2')
            swatch.grid(row=idx // 2, column=idx % 2, padx=3, pady=3)
            self.draw_pixel(swatch, 4, 4, 91, 44, idx)
            swatch.create_text(47, 24, text=f'{idx} {name}',
                               fill='black' if idx in (1, 2, 4) else 'white', font=('Arial', 10, 'bold'))
            swatch.bind('<Button-1>', lambda e, value=idx: self.select_brush(value))
            self.palette_buttons.append(swatch)
        self.select_brush(2)
        ttk.Label(right, text='0 Black  •  1 White  •  2 Light gray  •  3 Dark gray  •  4 Transparent\n'
                              'Null faces and missing block IDs display as light gray.',
                  foreground='#555').pack(anchor='w', pady=(12,0))
        actions = ttk.Frame(self.root, padding=10)
        actions.pack(fill='x')
        ttk.Button(actions, text='Save project (.json)', command=self.save_project).pack(side='left', padx=3)
        ttk.Button(actions, text='Load project', command=self.load_project).pack(side='left', padx=3)
        ttk.Button(actions, text='Export Textures.py', command=self.export_py).pack(side='right', padx=3)
        ttk.Label(self.root, textvariable=self.status, padding=(12,0,12,10)).pack(fill='x')

    def refresh_selector(self):
        self.ids = sorted(self.data)
        self.selector['values'] = [f'{i} — {self.data[i]["name"]}' for i in self.ids]

    def choose_block(self, event=None):
        val = self.selector.get()
        if val:
            self.select_block(int(val.split(' — ')[0]))

    def select_block(self, block_id):
        self.selected_id = block_id
        tex = self.data[block_id]
        self.block_name.set(tex['name'])
        self.block_id.set(str(block_id))
        self.enabled.set(tex['enabled'][self.face.get()])
        self.selector.set(f'{block_id} — {tex["name"]}')
        self.repaint()

    def change_face(self):
        self.enabled.set(self.data[self.selected_id]['enabled'][self.face.get()])
        self.repaint()

    def toggle_enabled(self):
        self.data[self.selected_id]['enabled'][self.face.get()] = self.enabled.get()
        self.repaint()

    def add_block(self):
        free = next((i for i in range(1, MAX_ID + 1) if i not in self.data), None)
        if free is None:
            messagebox.showinfo('No free IDs', 'All texture IDs from 1 to 255 are occupied.\n'
                                'Remove a texture to free an ID.')
            return
        name = simpledialog.askstring('New texture', 'Texture name:', initialvalue=f'Block {free}', parent=self.root)
        if name is None: return
        self.data[free] = new_entry(name.strip() or f'Block {free}')
        self.refresh_selector()
        self.select_block(free)

    def remove_block(self):
        block_id = self.selected_id
        if not messagebox.askyesno('Remove texture',
                f'Remove texture for ID {block_id}? It will export as null (light gray).'):
            return
        del self.data[block_id]
        if not self.data:
            self.data[1] = new_entry('Block 1')
            self.data[1]['enabled'] = {'Top': False, 'Side': False}
            self.status.set('Created a disabled placeholder; remove/assign its ID as needed.')
        self.refresh_selector()
        self.select_block(sorted(self.data)[0])

    def assign_id(self):
        try:
            new_id = int(self.block_id.get().strip())
        except ValueError:
            messagebox.showerror('Invalid ID', 'Enter a whole-number block ID from 1 to 255.')
            return
        if not 1 <= new_id <= MAX_ID:
            messagebox.showerror('Unsupported ID', 'Valid texture IDs are 1 through 255 (0 is reserved for Air).')
            return
        old_id = self.selected_id
        if new_id != old_id:
            if new_id in self.data:
                messagebox.showerror('ID in use', f'Block ID {new_id} already has a texture.\n'
                                     'Remove it or assign it another ID first.')
                return
            self.data[new_id] = self.data.pop(old_id)
        self.refresh_selector()
        self.select_block(new_id)
        self.status.set(f'Texture assigned to actual block ID {new_id}.')

    def rename(self):
        self.data[self.selected_id]['name'] = self.block_name.get().strip() or f'Block {self.selected_id}'
        self.refresh_selector()
        self.select_block(self.selected_id)

    def select_brush(self, value):
        self.brush.set(value)
        for idx, swatch in enumerate(self.palette_buttons):
            swatch.configure(highlightbackground='#007acc' if idx == value else '#aaa')

    def paint_at(self, event):
        if not self.enabled.get(): return
        u, v = event.x // 80, event.y // 80
        if 0 <= u < 4 and 0 <= v < 4:
            self.data[self.selected_id][self.face.get()][u + 4*v] = self.brush.get()
            self.repaint()

    def draw_pixel(self, canvas, x0, y0, x1, y1, value):
        if value == 4:
            # Checkerboard distinguishes a skipped pixel from any solid gray.
            mx = (x0 + x1) // 2
            my = (y0 + y1) // 2
            for a, b, c, d, shade in (
                (x0, y0, mx, my, '#ffffff'),
                (mx, y0, x1, my, '#aaaaaa'),
                (x0, my, mx, y1, '#aaaaaa'),
                (mx, my, x1, y1, '#ffffff')):
                canvas.create_rectangle(a, b, c, d, fill=shade, outline='')
        else:
            canvas.create_rectangle(x0, y0, x1, y1, fill=PALETTE[value], outline='')

    def repaint(self):
        self.paint.delete('all')
        self.preview.delete('all')
        tex = self.data[self.selected_id]
        enabled = tex['enabled'][self.face.get()]
        pixels = tex[self.face.get()] if enabled else [2] * 16
        for v in range(4):
            for u in range(4):
                value = pixels[u + v*4]
                self.paint.create_rectangle(u*80, v*80, (u+1)*80, (v+1)*80,
                                            fill=PALETTE[value], outline='#666', width=2)
                self.paint.create_text(u*80+40, v*80+40, text=str(value) if enabled else 'null',
                                       fill='black' if value in (1, 2, 4) else 'white',
                                       font=('Arial', 12 if not enabled else 16, 'bold'))
                self.preview.create_rectangle(u*60, v*60, (u+1)*60, (v+1)*60,
                                               fill=PALETTE[value], outline='#777')
        self.paint.configure(cursor='crosshair' if enabled else 'arrow')

    def reset_face(self):
        self.data[self.selected_id][self.face.get()] = [2] * 16
        self.repaint()

    def save_project(self):
        path = filedialog.asksaveasfilename(title='Save project', initialfile='tinycraft-textures.json',
                  defaultextension='.json', filetypes=[('JSON project', '*.json')])
        if not path: return
        Path(path).write_text(json.dumps({'version': 3, 'textures': self.data}, indent=2), encoding='utf-8')
        self.status.set(f'Saved {path}')

    def load_project(self):
        path = filedialog.askopenfilename(title='Load project', filetypes=[('JSON project', '*.json')])
        if not path: return
        try:
            raw = json.loads(Path(path).read_text(encoding='utf-8'))
            entries = raw.get('textures', raw)  # Supports old editor's JSON format.
            data = {}
            for key, record in entries.items():
                block_id = int(key)
                if not 1 <= block_id <= MAX_ID or block_id in data:
                    raise ValueError(f'Unsupported or duplicate block ID: {block_id}')
                entry = new_entry(record.get('name', dict(BLOCKS).get(block_id, f'Block {block_id}')))
                enabled = record.get('enabled', {})
                for face in ('Top', 'Side'):
                    values = record.get(face)
                    if values is None:
                        entry['enabled'][face] = False
                        continue
                    if len(values) != 16 or any(type(v) is not int or not 0 <= v <= 16 for v in values):
                        raise ValueError(f'Invalid {face} pixels at ID {block_id}')
                    entry[face] = [to_palette(v) if v > 4 else v for v in values]
                    entry['enabled'][face] = bool(enabled.get(face, True))
                data[block_id] = entry
            if not data: raise ValueError('Project contains no textures')
            self.data = data
            self.refresh_selector()
            self.select_block(sorted(data)[0])
            self.status.set(f'Loaded {path}')
        except (ValueError, TypeError, OSError, AttributeError) as exc:
            messagebox.showerror('Load error', str(exc))

    def export_py(self):
        path = filedialog.asksaveasfilename(title='Export Python texture data',
                  initialfile='Textures.py', defaultextension='.py', filetypes=[('Python module', '*.py')])
        if not path: return
        lines = [
            '# Generated by TinyCraft Texture Editor.',
            '# Index in TEXTURES is the actual block ID, not selection order.',
            '# None = no texture data; shown as solid light gray (color 2).',
            '# Each entry is (top, side). Each face may independently be None.',
            '# Pixel 4 = transparent: skip drawing this pixel in Renderer.py.',
            'TEXTURES = [',
        ]
        for block_id in range(MAX_ID + 1):
            entry = self.data.get(block_id)
            if entry is None:
                lines.append(f'    None,  # block ID {block_id}: no texture')
            else:
                faces = [tuple(entry[f]) if entry['enabled'][f] else None for f in ('Top', 'Side')]
                safe_name = str(entry['name']).replace('\r', ' ').replace('\n', ' ')
                lines.append(f'    ({faces[0]!r}, {faces[1]!r}),  # block ID {block_id}: {safe_name}')
        lines += [
            ']', '',
            'def apply_textures(T):',
            '    """Write all block slots; None faces render as solid light gray."""',
            '    TOPT = 16',
            '    SIDET = TOPT + 256 * 16',
            '    for block_id, entry in enumerate(TEXTURES):',
            '        top, side = entry if entry is not None else (None, None)',
            '        if top is None: top = (2,) * 16',
            '        if side is None: side = (2,) * 16',
            '        for k in range(16):',
            '            T[TOPT + block_id * 16 + k] = top[k]',
            '            T[SIDET + block_id * 16 + k] = side[k]',
            '',
        ]
        Path(path).write_text('\n'.join(lines), encoding='utf-8')
        self.status.set(f'Exported {path} — indexed by block ID; null = solid light gray.')
        messagebox.showinfo('Export complete', 'Place Textures.py beside Renderer.py.')

if __name__ == '__main__':
    root = tk.Tk()
    Editor(root)
    root.mainloop()