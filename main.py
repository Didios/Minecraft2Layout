# -------------------------------------------------------------------------------
# Author:      Didier Mathias
# Created:     23/05/2023
# -------------------------------------------------------------------------------

from tkinter import Tk, Frame, Label, Button, Entry, StringVar, BooleanVar, IntVar, Checkbutton, Canvas
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.ttk import Combobox, Progressbar
from tkinter.messagebox import showerror, showinfo, showwarning

from PIL import Image, ImageDraw, ImageFont, ImageTk

import sys
from os import path, makedirs, environ

import python_nbt.nbt as nbt

from Image import TkImage

# region utils

def resource_path(relative):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = path.abspath(".")

    return path.join(base_path, relative)

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

class App(Tk):
    PATH_BLOCKS = 'assets/blocks'
    PATH_FONTS = 'assets/includes/fonts/MinecraftRegular.otf'
    PATH_PROPERTIES = 'assets/properties'
    PATH_MASKS = 'assets/masks'

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        # title + icon
        self.title('Minecraft2Layout')
        self.iconbitmap(resource_path('assets/includes/icon.ico'))

        # variables
        self.air_state = -1
        self.textures = {}
        self.current_textures = []
        self.base_current_textures = []
        self.export_progress = IntVar()
        self.missing_textures = []

        self.export_progress.set(0)

        # disposition
        self.frame_file, self.button_file = self.__set_frame_file__()
        self.frame_settings, self.button_settings = self.__set_frame_settings__()
        self.frame_display, self.button_display = self.__set_frame_display__()
        self.frame_debug, self.button_debug = self.__set_frame_debug__()

        self.button_file.grid(row=0, column=0, sticky='nsew')
        self.button_settings.grid(row=1, column=0, sticky='nsew')
        self.button_display.grid(row=2, column=0, sticky='nsew')
        self.button_debug.grid(row=3, column=0, sticky='nsew')

        # Start Button
        Button(self, text='Export', command=self.schematize).grid(row=4, column=0, sticky='nsew')

        # ProgressBar
        Progressbar(self, orient='horizontal', mode='determinate',
                    variable=self.export_progress).grid(row=5, column=0, sticky='nsew')

        self.rowconfigure('all', weight=1)
        self.columnconfigure('all', weight=1)


# region set frame

    def __set_frame_file__(self):
        frame = Frame(self)
        Button(frame, text='/\\ File Category /\\', bg='grey',
               command=self._shrink_file_).grid(row=0, column=0, columnspan=3, sticky='nsew')

        self.path_struct = StringVar()
        self.path_dir = StringVar()
        self.create_dir = BooleanVar()
        self.export_name = StringVar()

        self.create_dir.set(True)

        # structure file
        Label(frame, text='Structure file: ').grid(row=1, column=0, sticky='nsew')
        Entry(frame, textvariable=self.path_struct).grid(row=1, column=1, sticky='nsew')
        Button(frame, text='Browse', command=self.__get_path_struct__).grid(row=1, column=2, sticky='nsew')

        # Final dir
        Label(frame, text='Export directory: ').grid(row=2, column=0, sticky='nsew')
        Entry(frame, textvariable=self.path_dir).grid(row=2, column=1, sticky='nsew')
        Button(frame, text='Browse', command=self.__get_path_dir__).grid(row=2, column=2, sticky='nsew')

        # create directory
        Label(frame, text='Create a new folder: ').grid(row=3, column=0, sticky='nsew')
        Checkbutton(frame, anchor='center', variable=self.create_dir,
                    onvalue=True, offvalue=False).grid(row=3, column=1, columnspan=2, sticky='nsew')
        # base name
        Label(frame, text='Export name: ').grid(row=4, column=0, sticky='nsew')
        Entry(frame, textvariable=self.export_name).grid(row=4, column=1, columnspan=2, sticky='nsew')

        frame.rowconfigure('all', weight=1)
        frame.columnconfigure('all', weight=1)
        return frame, Button(self, text='\\/ File Category \\/', bg='grey70', command=self._grow_file_)

    def __set_frame_settings__(self):
        frame = Frame(self)
        Button(frame, text='/\\ Settings Category /\\', bg='grey',
               command=self._shrink_settings_).grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.layout_dir = StringVar()
        self.layout_dir.set('y')

        # orientation
        Label(frame, text='Layout direction:').grid(row=1, column=0, sticky='nsew')
        Combobox(frame, textvariable=self.layout_dir,
                 values=('x', 'y', 'z'), state='readonly').grid(row=1, column=1, sticky='nsew')

        frame.rowconfigure('all', weight=1)
        frame.columnconfigure('all', weight=1)
        return frame, Button(self, text='\\/ Settings Category \\/', bg='grey70', command=self._grow_settings_)

    def __set_frame_display__(self):
        frame = Frame(self)
        Button(frame, text='/\\ Display Category /\\', bg='grey',
               command=self._shrink_display_).grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.block_res = IntVar()
        self.grid_thick = IntVar()
        self.offset_space = IntVar()
        self.legend_pos = StringVar()

        self.block_res.set(64)
        self.grid_thick.set(2)
        self.offset_space.set(50)
        self.legend_pos.set('right')

        # block size
        Label(frame, text='Block size:').grid(row=1, column=0, sticky='nsew')
        Combobox(frame, textvariable=self.block_res,
                 values=(16, 32, 64, 128), state='readonly').grid(row=1, column=1, sticky='nsew')

        # grid size
        Label(frame, text='Grid thickness:').grid(row=2, column=0, sticky='nsew')
        Combobox(frame, textvariable=self.grid_thick,
                 values=tuple(range(1, 129, 1)), state='readonly').grid(row=2, column=1, sticky='nsew')

        # offset
        Label(frame, text='Seams space:').grid(row=3, column=0, sticky='nsew')
        Combobox(frame, textvariable=self.offset_space,
                 values=tuple(range(10, 501, 1)), state='readonly').grid(row=3, column=1, sticky='nsew')

        # legend position
        Label(frame, text='Legend position:').grid(row=4, column=0, sticky='nsew')
        Combobox(frame, textvariable=self.legend_pos,
                 values=('right', 'left', 'top', 'bottom'), state='readonly').grid(row=4, column=1, sticky='nsew')

        frame.rowconfigure('all', weight=1)
        frame.columnconfigure('all', weight=1)
        return frame, Button(self, text='\\/ Display Category \\/', bg='grey70', command=self._grow_display_)

    def __set_frame_debug__(self):
        frame = Frame(self)
        Button(frame, text='/\\ Debug Category /\\', bg='grey',
               command=self._shrink_debug_).grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.create_data = BooleanVar()
        self.create_missing = BooleanVar()

        self.block_canvas = None
        self.block_img = Image.open(self._get_debug_texture_path_())

        self.mask_canvas = None
        self.mask_img = Image.open(path.join(self.PATH_MASKS, 'mask_fence.png'))

        self.result_canvas = None
        self.result_img = Image.new('RGBA', (16, 16))
        self.result_name = StringVar()

        self.create_data.set(False)
        self.create_missing.set(False)
        self.result_name.set('new_texture')

        # create data file
        Label(frame, text='Create Data File: ').grid(row=1, column=0, sticky='nsew')
        Checkbutton(frame, anchor='center', variable=self.create_data,
                    onvalue=True, offvalue=False).grid(row=1, column=1, sticky='nsew')

        # create missing file
        Label(frame, text='Create Missing File: ').grid(row=2, column=0, sticky='nsew')
        Checkbutton(frame, anchor='center', variable=self.create_missing,
                    onvalue=True, offvalue=False).grid(row=2, column=1, sticky='nsew')

        # create new texture
        Label(frame, text='Create new block texture').grid(row=3, column=0, columnspan=2, sticky='nsew')
        sub_frame = Frame(frame)
        sub_frame.grid(row=4, column=0, columnspan=2, sticky='nsew')

        self.block_canvas = TkImage(sub_frame, width=160, height=160, image=self.block_img)
        self.block_canvas.grid(row=0, column=0, sticky='nsew')
        Button(sub_frame, text='Browse', command=self.__get_block_text__).grid(row=1, column=0, rowspan=2, sticky='nsew')

        self.mask_canvas = TkImage(sub_frame, width=160, height=160, image=self.mask_img)
        self.mask_canvas.grid(row=0, column=1, sticky='nsew')
        Button(sub_frame, text='Browse', command=self.__get_mask_text__).grid(row=1, column=1, rowspan=2, sticky='nsew')

        self.result_canvas = TkImage(sub_frame, width=160, height=160, image=self.result_img)
        self.result_canvas.grid(row=0, column=2, sticky='nsew')
        Entry(sub_frame, textvariable=self.result_name).grid(row=1, column=2, sticky='nsew')
        Button(sub_frame, text='Save', command=self.__save_result_text__).grid(row=2, column=2, sticky='nsew')

        self.__process_result_text__()

        sub_frame.rowconfigure('all', weight=1)
        sub_frame.columnconfigure('all', weight=1)

        frame.rowconfigure('all', weight=1)
        frame.columnconfigure('all', weight=1)
        return frame, Button(self, text='\\/ Debug Category \\/', bg='grey70', command=self._grow_debug_)

# endregion set frame

# region shrink & grow

    def _shrink_file_(self):
        self.frame_file.grid_forget()
        self.button_file.grid(row=0, column=0, sticky='nsew')

    def _grow_file_(self):
        self.frame_file.grid(row=0, column=0, sticky='nsew')
        self.button_file.grid_forget()

    def _shrink_settings_(self):
        self.frame_settings.grid_forget()
        self.button_settings.grid(row=1, column=0, sticky='nsew')

    def _grow_settings_(self):
        self.frame_settings.grid(row=1, column=0, sticky='nsew')
        self.button_settings.grid_forget()

    def _shrink_display_(self):
        self.frame_display.grid_forget()
        self.button_display.grid(row=2, column=0, sticky='nsew')

    def _grow_display_(self):
        self.frame_display.grid(row=2, column=0, sticky='nsew')
        self.button_display.grid_forget()

    def _shrink_debug_(self):
        self.frame_debug.grid_forget()
        self.button_debug.grid(row=3, column=0, sticky='nsew')

    def _grow_debug_(self):
        self.frame_debug.grid(row=3, column=0, sticky='nsew')
        self.button_debug.grid_forget()

# endregion shrink & grow

# region settings function

    def __get_path_struct__(self):
        filepath = askopenfilename(title='Structure File', filetypes=[("vanilla Minecraft structure (.nbt)", '*.nbt')])

        if filepath and filepath != '':
            self.path_struct.set(filepath)

            if self.path_dir.get() == '':
                self.path_dir.set(path.dirname(filepath))
            if self.export_name.get() == '':
                self.export_name.set(path.basename(filepath)[0:-4])

    def __get_path_dir__(self):
        dirpath = askdirectory(title='Export Folder', mustexist=True)

        if dirpath and dirpath != '':
            self.path_dir.set(dirpath)

    def __process_result_text__(self):
        self.result_img = Image.new('RGBA', self.block_img.size)

        block_data = self.block_img.load()
        mask_data = self.mask_img.load()
        result_data = self.result_img.load()

        width, height = self.mask_img.size
        for x in range(width):
            for y in range(height):
                if mask_data[x, y][3] == 255:
                    result_data[x, y] = block_data[x, y]
                else:
                    result_data[x, y] = (0, 0, 0, 0)

        self.result_canvas.set_image(self.result_img)

    def __get_block_text__(self):
        filepath = askopenfilename(title='Block Texture', filetypes=[("texture (.png)", '*.png')],
                                   initialdir=self.PATH_BLOCKS)

        if filepath and filepath != '':
            self.block_img = Image.open(filepath)
            self.block_canvas.set_image(self.block_img)
            self.__process_result_text__()

    def __get_mask_text__(self):
        filepath = askopenfilename(title='Mask Texture', filetypes=[("texture (.png)", '*.png')],
                                   initialdir=self.PATH_MASKS)

        if filepath and filepath != '':
            self.mask_img = Image.open(filepath)
            self.mask_canvas.set_image(self.mask_img)
            self.__process_result_text__()

    def __save_result_text__(self):
        self.result_img.save(path.join(self.PATH_BLOCKS, self.result_name.get() + '.png'))

# endregion settings function

#TEST @Mathias - sort function in regions

    def _get_debug_texture_path_(self):
        return path.join(self.PATH_BLOCKS, 'debug.png')

    def _get_axis_order_(self):
        layout_dir = self.layout_dir.get()

        if layout_dir == 'x':
            return 0, 2, 1
        elif layout_dir == 'y':
            return 1, 2, 0
        return 2, 0, 1

    def _get_preslice_(self, size, blocks):
        # get direction
        direction_x, direction_y, direction_z = self._get_axis_order_()

        # create layout
        nbt_layer = [[[0 for ___ in range(size[direction_z])] for __ in range(size[direction_y])] for _ in range(size[direction_x])]

        # position blocks
        for block in blocks:
            position = block['pos']
            state = block['state']

            nbt_layer[position[direction_x]][position[direction_y]][position[direction_z]] = state

        return nbt_layer

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
            self._add_missing_texture_('block: ' + name + '.png')
            block_path = self._get_debug_texture_path_()

        img = Image.open(block_path).convert('RGBA')
        if properties is not None:
            if 'waterlogged' in keys:
                if properties['waterlogged']:
                    img_2 = Image.open(path.join(self.PATH_PROPERTIES, 'waterlogged.png')).convert('RGBA')
                    img_2.paste(img, (0, 0), mask=img)
                keys.remove('waterlogged')

            # for bed
            if 'part' in keys:
                if properties['part'] == 'head':
                    img = img.crop((0, 0, 16, 16))
                else:
                    img = img.crop((0, 16, 16, 32))
                keys.remove('part')

            # for door
            if 'half' in keys and 'door' in name:
                if properties['half'] == 'upper':
                    img = img.crop((0, 0, 16, 16))
                else:
                    img = img.crop((0, 16, 16, 32))
                keys.remove('half')

            for k in keys:
                img_path = path.join(self.PATH_PROPERTIES, k + "_" + properties[k] + ".png")
                if path.exists(img_path):
                    addon = Image.open(img_path).convert('RGBA')
                    img.paste(addon, (0, 0), mask=addon)
                else:
                    self._add_missing_texture_('property: ' + k + "_" + properties[k] + '.png' + ' - block: ' + name)

        self.textures[filename] = img
        return img

    def _add_missing_texture_(self, missing):
        if missing not in self.missing_textures:
            self.missing_textures.append(missing)

    def get_textures(self, palette, size):
        self.current_textures = []
        self.base_current_textures = []

        dimension = (size, size)
        for block_data in palette:
            img = self.get_block_texture(block_data)
            self.current_textures.append(img.resize(dimension, resample=Image.NEAREST))

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

        scale = self.block_res.get()
        self.get_textures(palette, scale)

        data['layout'] = self._get_preslice_(size, blocks)
        grid_size = self.grid_thick.get()

        legend_position = self.legend_pos.get()
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
                    else:
                        self.air_state = state

        offset = self.offset_space.get()
        data['right'] = offset
        data['left'] = offset
        data['top'] = offset
        data['bottom'] = offset

        legend_size = 0
        if legend_position in ['top', 'bottom']:
            for legend_layer in legend_offset:
                legend_size = max(legend_size, len(legend_layer))
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
        self.air_state = -1

        # check valid filepath
        filepath = self.path_struct.get()
        if not path.exists(filepath):
            self._grow_file_()
            showerror('Incorrect File', 'File is incorrect, must be a valid path')
            return

        data = self.retrieve_data(filepath)
        scale = self.block_res.get()
        size = data['size']
        grid_size = self.grid_thick.get()

        self.set_progress(10)

        font_path = self.PATH_FONTS
        font = ImageFont.truetype(resource_path(font_path), scale // 2)
        legend_position = self.legend_pos.get()

        # calculate image dimension
        dimension = (
            data['right'] + data['left'] + size[1] * scale + grid_size * (size[1] + 1),
            data['top'] + data['bottom'] + size[2] * scale + grid_size * (size[2] + 1)
        )

        # determine main directory
        basename = self.export_name.get()
        directory_path = path.dirname(filepath)
        if self.create_dir.get():
            directory_path = path.join(directory_path, basename)
            if not path.exists(directory_path):
                makedirs(directory_path)

        self.set_progress(15)

        # create grid template
        grid_dimension = (dimension[0] - data['right'] - data['left'], dimension[1] - data['top'] - data['bottom'])
        grid_img = Image.new('RGBA', grid_dimension, (0, 0, 0, 0))
        grid_load = grid_img.load()
        for x in range(0, grid_dimension[0] + 1, scale + grid_size):  # draw x line
            draw_square(grid_load, x, 0, x + grid_size, grid_dimension[1], (0, 0, 0, 255))
        for y in range(0, grid_dimension[1] + 1, scale + grid_size):  # draw y line
            draw_square(grid_load, 0, y, grid_dimension[0], y + grid_size, (0, 0, 0, 255))

        self.set_progress(20)
        advance = size[0] // (99 - 20)

        # draw
        previous_texture = Image.open(path.join(self.PATH_PROPERTIES, 'previous_block.png')
                                      ).resize((self.block_res.get(), self.block_res.get()), resample=Image.NEAREST)
        previous_layer = None
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

                    if previous_layer and previous_layer[i][j] != self.air_state:
                        layer_img.paste(previous_texture, (x, y), mask=previous_texture)
            previous_layer = layer

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
            self.set_progress(self.export_progress.get() + advance)
        self.set_progress(99)

        if self.create_data.get():
            with open(path.join(directory_path, basename + '_data.csv'), 'w') as file:
                file.write('Block; Number; Stack x64; Stack x16')
                for k, v in data['count'].items():
                    file.write(f"\n{k};{v};{str(v // 64) + ' stack and ' + str(v % 64)};{str(v // 16) + ' stack and ' + str(v % 16)}")

        self.set_progress(100)
        showinfo('Finish', 'This File has finished to proceed !')
        if len(self.missing_textures) > 0:
            text = ''
            self.missing_textures.sort()
            for i in self.missing_textures:
                text += f'{i}\n'
            showwarning('Missing textures', 'Those textures are missing and cannot be drawn:\n\n' + text)

            if self.create_missing.get():
                with open(path.join(directory_path, basename + '_missing.txt'), 'w') as file:
                    file.write(text)

    def set_progress(self, value):
        self.export_progress.set(value)
        self.update()


if __name__ == "__main__":
    app = App()
    app.mainloop()
