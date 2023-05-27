# -------------------------------------------------------------------------------
# Author:      Didier Mathias
# Created:     23/05/2023
# -------------------------------------------------------------------------------

from tkinter import Tk, Label, Button, Entry, StringVar, BooleanVar, IntVar, Checkbutton
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Combobox, Progressbar
from tkinter.messagebox import showerror, showinfo, showwarning

from PIL import Image, ImageDraw, ImageFont

from os import path, makedirs

import python_nbt.nbt as nbt

# region utils


def get_nbt_data(filepath: str) -> tuple[list[int, int, int], list[dict[str: list[int, int, int] | int]], list[dict[str: dict | str]]]:
    """
    Retrieve nbt data from a nbt file
    Args:
        filepath (): relative or absolut path to the .nbt file

    Returns:
        size of the structure
        blocks data
        palette data
    """
    data_brut = nbt.read_from_nbt_file(filepath)
    data = data_brut.json_obj(full_json=False)

    size = tuple(data['size'])
    blocks = data['blocks']
    palette = data['palette']

    return size, blocks, palette


def minecraft_clean_base(value: str) -> str:
    """
    Clean a minecraft index name from the '#minecraft:' if present
    Args:
        value (): the string to evaluate

    Returns:
        clean string
    """
    index = value.find('minecraft:')

    if index == 0:
        return value[10::]
    elif index == 1 and value[0] == '#':
        return '#' + value[11::]

    return value


def draw_square(img, x1, y1, x2, y2, color):
    for x in range(x1, x2):
        for y in range(y1, y2):
            img[x, y] = color

# endregion utils


class App:
    PATH_BLOCKS = 'assets/blocks'
    PATH_FONTS = 'assets/fonts'
    PATH_PROPERTIES = 'assets/properties'

    def __init__(self):
        self.root = Tk()
        self.root.title('Minecraft2Layout')
        self.root.iconbitmap('assets/icon.ico')

        self.textures = {}
        self.current_textures = []
        self.base_current_textures = []

        self.filepath = StringVar()
        self.size = IntVar()
        self.grid_size = IntVar()
        self.offset = IntVar()
        self.legend_position = StringVar()
        self.orientation = StringVar()
        self.create_directory = BooleanVar()
        self.create_data = BooleanVar()
        self.progressvalue = IntVar()

        self.missing_textures = []

        # directory
        Label(self.root, text='Location: ').grid(row=0, column=0, sticky='nsew')
        Entry(self.root, textvariable=self.filepath).grid(row=0, column=1, sticky='nsew')
        Button(self.root, text='Browse', command=self.get_location).grid(row=0, column=2, sticky='nsew')

        # size
        Label(self.root, text='Block size: ').grid(row=1, column=0, sticky='nsew')
        Combobox(self.root, textvariable=self.size,
                 values=(16, 32, 64, 128), state='readonly').grid(row=1, column=1, sticky='nsew')
        Label(self.root, text='pixels').grid(row=1, column=2, sticky='nsew')

        # grid size
        Label(self.root, text='Grid size: ').grid(row=2, column=0, sticky='nsew')
        Combobox(self.root, textvariable=self.grid_size,
                 values=tuple(range(1, 129, 1)), state='readonly').grid(row=2, column=1, sticky='nsew')
        Label(self.root, text='pixels').grid(row=2, column=2, sticky='nsew')

        # offset
        Label(self.root, text='Offset: ').grid(row=3, column=0, sticky='nsew')
        Combobox(self.root, textvariable=self.offset,
                 values=tuple(range(10, 501, 1)), state='readonly').grid(row=3, column=1, sticky='nsew')
        Label(self.root, text='pixels').grid(row=3, column=2, sticky='nsew')

        # legend position
        Label(self.root, text='Legend Position: ').grid(row=4, column=0, sticky='nsew')
        Combobox(self.root, textvariable=self.legend_position,
                 values=('right', 'left', 'top', 'bottom'), state='readonly').grid(row=4, column=1, sticky='nsew')
        Label(self.root, text='around grid').grid(row=4, column=2, sticky='nsew')

        # orientation
        Label(self.root, text='Layout Orientation: ').grid(row=5, column=0, sticky='nsew')
        Combobox(self.root, textvariable=self.orientation,
                 values=('x', 'y', 'z'), state='readonly').grid(row=5, column=1, sticky='nsew')
        Label(self.root, text='axe').grid(row=5, column=2, sticky='nsew')

        # create directory
        Label(self.root, text='Create Directory: ').grid(row=6, column=0, sticky='nsew')
        Checkbutton(self.root, anchor='center', variable=self.create_directory,
                    onvalue=True, offvalue=False).grid(row=6, column=1, sticky='nsew')
        Label(self.root, text='create a directory\nfor all generated file').grid(row=6, column=2, sticky='nsew')

        # create data file
        Label(self.root, text='Create Data File: ').grid(row=7, column=0, sticky='nsew')
        Checkbutton(self.root, anchor='center', variable=self.create_data,
                    onvalue=True, offvalue=False).grid(row=7, column=1, sticky='nsew')
        Label(self.root, text='create a file\nwith all block count').grid(row=7, column=2, sticky='nsew')

        # Start Button
        Button(self.root, text='Start', command=self.schematize).grid(row=8, column=0, columnspan=3, sticky='nsew')

        # ProgressBar
        Progressbar(self.root, orient='horizontal', mode='determinate',
                    variable=self.progressvalue).grid(row=9, column=0, columnspan=3, sticky='nsew')

        self.set_default()
        self.grid_config()

    def launch(self):
        self.root.mainloop()

    def grid_config(self):
        # self.root.rowconfigure(0, weight=1)
        # self.root.rowconfigure(1, weight=1)
        # self.root.rowconfigure(2, weight=1)
        # self.root.rowconfigure(3, weight=1)
        # self.root.rowconfigure(4, weight=1)
        # self.root.rowconfigure(5, weight=1)

        # self.root.columnconfigure(0, weight=0)
        # self.root.columnconfigure(1, weight=1)
        # self.root.columnconfigure(2, weight=0)

        self.root.resizable(width=False, height=False)

    def set_default(self):
        self.progressvalue.set(0)
        self.filepath.set('')
        self.size.set(16)
        self.grid_size.set(2)
        self.offset.set(50)
        self.legend_position.set('right')
        self.orientation.set('y')
        self.create_directory.set(True)
        self.create_data.set(True)

    def get_location(self):
        new_filepath = askopenfilename(title='File to schematize', filetypes=[("vanilla structure (.nbt)", '*.nbt')])

        if new_filepath and new_filepath != '':
            self.filepath.set(new_filepath)

    def slice(self, size, blocks):
        # get direction
        direction_x, direction_y, direction_z = self.get_direction()

        # create layout
        nbt_layer = [[[0 for ___ in range(size[direction_z])] for __ in range(size[direction_y])] for _ in range(size[direction_x])]

        # position blocks
        for block in blocks:
            position = block['pos']
            state = block['state']

            nbt_layer[position[direction_x]][position[direction_y]][position[direction_z]] = state

        return nbt_layer

    def get_direction(self):
        orientation = self.orientation.get()
        if orientation == 'x':
            return 0, 2, 1
        elif orientation == 'y':
            return 1, 2, 0

        return 2, 0, 1

    def get_block_texture(self, block_data):
        name = minecraft_clean_base(block_data['Name'])
        filename = name
        properties = None
        keys = None

        if 'Properties' in block_data.keys():
            properties = block_data['Properties']
            keys = list(properties.keys())
            keys.sort()

            for k in keys:
                filename += f'.{k}_{properties[k]}'

        filename += '.png'

        if filename in self.textures.keys():
            return self.textures[filename]

        block_path = path.join(self.PATH_BLOCKS, name + '.png')
        if not path.exists(block_path):
            self.missing_textures.append('block - ' + name + '.png')
            block_path = path.join(self.PATH_BLOCKS, 'debug.png')

        img = Image.open(block_path).convert('RGBA')
        if properties is not None:
            if 'waterlogged' in keys:
                if properties['waterlogged']:
                    img_2 = Image.open(path.join(self.PATH_PROPERTIES, 'waterlogged.png')).convert('RGBA')
                    img_2.paste(img, (0, 0), mask=img)
                keys.remove('waterlogged')

            if 'part' in keys:
                if properties['part'] == 'head':
                    img = img.crop((0, 0, 16, 16))
                else:
                    img = img.crop((0, 16, 16, 32))
                keys.remove('part')

            for k in keys:
                img_path = path.join(self.PATH_PROPERTIES, k + "_" + properties[k] + ".png")
                if path.exists(img_path):
                    addon = Image.open(img_path).convert('RGBA')
                    img.paste(addon, (0, 0), mask=addon)
                else:
                    self.missing_textures.append('block - ' + name + ' - property - ' + k + "_" + properties[k] + '.png')

        self.textures[filename] = img
        return img

    def get_textures(self, palette, size):
        self.current_textures = []
        self.base_current_textures = []

        dimension = (size, size)
        for block_data in palette:
            img = self.get_block_texture(block_data)
            self.current_textures.append(img.resize(dimension))

            img_base = self.get_block_texture({'Name': block_data['Name']})
            self.base_current_textures.append(img_base.resize(dimension))

    def retrieve_data(self, filepath):
        """
        blocks separate by layer
        offset top bottom right left
        legend by layer
        """
        data = {
            'size': (),
            'layout': [],
            'legend': [],
            'count': {},
            'right': 0,
            'left': 0,
            'top': 0,
            'bottom': 0
        }

        size, blocks, palette = get_nbt_data(filepath)

        scale = self.size.get()
        self.get_textures(palette, scale)

        data['layout'] = self.slice(size, blocks)
        grid_size = self.grid_size.get()

        legend_position = self.legend_position.get()
        legend_offset = []

        length_x = len(data['layout'])
        length_y = len(data['layout'][0])
        length_z = len(data['layout'][0][0])
        data['size'] = (length_x, length_y, length_z)
        for x in range(length_x):
            data['legend'].append({})
            legend_offset.append([])
            for y in range(length_y):
                for z in range(length_z):
                    state = data['layout'][x][y][z]

                    name = minecraft_clean_base(palette[state]["Name"])
                    if name != 'air':
                        data['legend'][-1][name] = self.base_current_textures[state]

                        if name not in data['count'].keys():
                            data['count'][name] = 1
                        else:
                            data['count'][name] += 1

                        if name not in legend_offset[-1]:
                            legend_offset[-1].append(name)

        offset = self.offset.get()
        data['right'] = offset
        data['left'] = offset
        data['top'] = offset
        data['bottom'] = offset

        legend_size = 0
        if legend_position in ['top', 'bottom']:
            for legend_layer in legend_offset:
                legend_size = max(legend_size, len(legend_layer))
            print(scale, legend_size, grid_size)
            legend_size = scale * 2 + scale * legend_size + grid_size * legend_size
        else:
            for legend_layer in legend_offset:
                for name in legend_layer:
                    legend_size = max(legend_size, (scale // 3) * len(name))
            legend_size += scale * 2

        data[legend_position] = max(offset, legend_size)

        return data

    def schematize(self):
        self.set_progress(0)
        self.missing_textures = []

        # check valid filepath
        filepath = self.filepath.get()
        if not path.exists(filepath):
            showerror('Incorrect File', 'File is incorrect, must be a valid path')
            return

        data = self.retrieve_data(filepath)
        scale = self.size.get()
        size = data['size']
        grid_size = self.grid_size.get()

        self.set_progress(10)

        font = ImageFont.truetype(path.join(self.PATH_FONTS, 'MinecraftRegular.otf'), scale // 2)
        legend_position = self.legend_position.get()

        # calculate image dimension
        dimension = (
            data['right'] + data['left'] + size[1] * scale + grid_size * (size[1] + 1),
            data['top'] + data['bottom'] + size[2] * scale + grid_size * (size[2] + 1)
        )

        # determine main directory
        basename = path.basename(filepath)[0:-4]
        directory_path = path.dirname(filepath)
        if self.create_directory.get():
            directory_path = path.join(directory_path, basename + '_layers')
            if not path.exists(directory_path):
                makedirs(directory_path)

        self.set_progress(15)

        # create grid template
        grid_dimension = (dimension[0] - data['right'] - data['left'], dimension[1] - data['top'] - data['bottom'])
        grid_img = Image.new('RGBA', grid_dimension, (0, 0, 0, 0))
        grid_load = grid_img.load()
        for x in range(0, grid_dimension[0] + 1, scale + grid_size):
            draw_square(grid_load, x, 0, x + grid_size, grid_dimension[1], (0, 0, 0, 255))
        for y in range(0, grid_dimension[1] + 1, scale + grid_size):
            draw_square(grid_load, 0, y, grid_dimension[0], y + grid_size, (0, 0, 0, 255))

        self.set_progress(20)
        advance = size[0] // (99 - 20)

        # draw
        for i_layer, layer in enumerate(data['layout']):
            layer_img_path = path.join(directory_path, basename + f'_layer_{i_layer + 1}.png')
            layer_img = Image.new('RGBA', dimension, (127, 127, 127, 255))
            layer_draw = ImageDraw.Draw(layer_img)

            # draw grid
            layer_img.paste(grid_img, (data['left'], data['top']), mask=grid_img)

            # draw block
            legend = {}
            for i in range(size[1]):
                x = data['left'] + grid_size + (scale + grid_size) * i
                for j in range(size[2]):
                    y = dimension[1] - data['bottom'] - (grid_size + scale) - (scale + grid_size) * j

                    texture = self.current_textures[layer[i][j]]
                    layer_img.paste(texture, (x, y), mask=texture)

            # draw legend
            if legend_position in ['right', 'left']:
                x = scale // 2
                y = data['top']
                if legend_position == 'right':
                    x += dimension[0] - data['right']

                space = int(scale * 1.5)
                for name, texture in data['legend'][i_layer].items():
                    layer_img.paste(texture, (x, y), mask=texture)
                    layer_draw.text((x + space, y), name, font=font)
                    y += scale + grid_size
            else:
                sign = 1

                x = data['left']
                if legend_position == 'bottom':
                    y = data['top'] + grid_dimension[1] + (scale // 2)
                else:
                    y = data['top'] - scale - (scale // 2)
                    sign = -1

                space = int(scale * 1.5)
                for name, texture in data['legend'][i_layer].items():
                    layer_img.paste(texture, (x, y), mask=texture)
                    layer_draw.text((x + space, y), name, font=font)
                    y += ((scale + grid_size) * sign)

            layer_img.save(layer_img_path)
            self.set_progress(self.progressvalue.get() + advance)
        self.set_progress(99)

        if self.create_data.get():
            with open(path.join(directory_path, basename + "_data.csv"), 'w') as file:
                file.write("Block; Number; Stack x64; Stack x16")
                for k, v in data['count'].items():
                    file.write(f"\n{k};{v};{str(v // 64) + ' stack and ' + str(v % 64)};{str(v // 16) + ' stack and ' + str(v % 16)}")

        self.set_progress(100)
        showinfo('Finish', 'This File has finished to proceed !')
        if len(self.missing_textures) > 0:
            text = ''
            for i in self.missing_textures:
                text += f'{i}\n'
            showwarning('Missing textures', 'Those textures are missing and cannot be drawn:\n' + text)

    def set_progress(self, value):
        self.progressvalue.set(value)
        self.root.update()


if __name__ == "__main__":
    app = App()
    app.launch()
