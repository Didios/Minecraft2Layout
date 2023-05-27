# -------------------------------------------------------------------------------
# Name:        nbtviewer
# Purpose:     to visualize minecraft .nbt file in 3D window
#
# Author:      Didier Mathias
#
# Created:     27/04/2023
# -------------------------------------------------------------------------------

# import
import json
import python_nbt.nbt as nbt
from random import choice
from PIL import Image, ImageDraw, ImageFont
import os.path as path
import os


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


def clean_base(value: str) -> str:
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


def get_air_state(palette: list[dict[str: dict | str]]) -> int:
    """
    Get state index of air block for a palette
    Args:
        palette (): palette to analyse

    Returns:
        int index
    """
    air_state = -1
    for i in range(len(palette)):
        if palette[i]['Name'] == 'minecraft:air':
            air_state = i
            break;

    return air_state


def get_random_color() -> str:
    """
    Create a hex random color code
    Returns:
        hex color code
    """
    c = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
    s = '#'
    for i in range(6):
        s += choice(c)
    return s


def get_palette_color(palette: list[dict[str: dict | str]], reference: dict[str: str] = None):
    """
    Get all color of a palette, if no reference is provided, random colors are set
    Args:
        palette (): palette to analyze
        reference (): colors reference for each block

    Returns:
        list of all color, index are the same as in palette
    """
    if reference is None:
        names = []
        colors = []
        for i in palette:
            n = i['Name']
            if n in names:
                colors.append(colors[names.index(n)])
            else:
                names.append(n)
                colors.append(get_random_color())

        return colors  # [get_random_color() for i in palette]

    return [reference[i['Name']] for i in palette]


def rgb_to_hsv(rgb):
    """
    transfrom a rgb code (0-1) to a hsv code (0-1)
    parameters:
        rgb : list with 3 float between 0 and 1
    return:
        list with 3 float, first is between 0-360, others are between 0-1
    """
    _max = max(rgb)
    _min = min(rgb)

    r = rgb[0]
    g = rgb[1]
    b = rgb[2]

    if _max == _min:
        t = 0
    elif _max == r:
        t = (60 * ((g-b)/(_max-_min)) + 360) % 360
    elif _max == g:
        t = 60 * ((b-r)/(_max-_min)) + 120
    elif _max == b:
        t = 60 * ((r-g)/(_max-_min)) + 240

    if _max == 0:
        s = 0
    else:
        s = 1 - (_min/_max)

    v = _max

    return [t, s, v]

def hsv_to_rgb(hsv):
    """
    transfrom a hsv code (0-1) to a rgb code (0-1)
    parameters:
        hsv : list with 3 float, first is between 0-360, others are between 0-1
    return:
        list with 3 float between 0 and 1
    """
    h = hsv[0]
    s = hsv[1]
    v = hsv[2]

    ti = int((h/60) % 6)
    f = (h/60) - ti

    l = v * (1 - s)
    m = v * (1 - f * s)
    n = v * (1 - (1 - f) * s)

    if ti == 0:
        return [v, n, l]
    elif ti == 1:
        return [m, v, l]
    elif ti == 2:
        return [l, v, n]
    elif ti == 3:
        return [l, m, v]
    elif ti == 4:
        return [n, l, v]
    elif ti == 5:
        return [v, l, m]

#endregion


def nbt_to_png(filepath, scale=16, grid=2, offset=50, showDebug=True):
    size, block, palette = get_nbt_data(filepath)

    height = size[0]
    nbr_layer = size[1]
    width = size[2]

    scale = 16 * (scale // 16)

    air_state = get_air_state(palette)

    if showDebug:
        print("SIZE: ", size)
        print("PALETTE: ", palette)

    nbt_layer = [[[air_state for __ in range(height)] for __ in range(width)] for _ in range(nbr_layer)]
    for b in block:
        pos = b['pos']
        nbt_layer[pos[1]][pos[2]][pos[0]] = b['state']

    textures_base, textures = get_textures(palette, scale)

    text_offset = 4

    img_size = (
            offset * (text_offset + 1) + width * scale + grid * (width + 1),
            offset * 2 + height * scale + grid * (height + 1))

    i_path = path.join(path.dirname(filepath), path.basename(filepath)[0:-4] + "_layers")
    if not path.exists(i_path):
        os.makedirs(i_path)

    blocks = {}
    font = ImageFont.truetype(path.abspath("../temp/to_schema/textures/fonts/MinecraftRegular.otf"), scale // 2)

    for i_layer, layer in enumerate(nbt_layer):
        img_path = path.join(i_path, path.basename(filepath[0:-4]) + f"_layer_{i_layer+1}.png")
        img = Image.new("RGBA", img_size, (127, 127, 127, 255))
        img_draw = ImageDraw.Draw(img)
        img_grid = img.load()

        # draw grid
        for x in range(offset, img_size[0] - offset * text_offset + 1, scale+grid):
            draw_square(img_grid, x, offset, x + grid, img_size[1] - offset, (0, 0, 0, 255))

        for y in range(offset, img_size[1] - offset + 1, scale + grid):
            draw_square(img_grid, offset, y, img_size[0] - offset * text_offset, y + grid, (0, 0, 0, 255))

        # draw block
        legend = {}
        for i in range(width):
            x = offset + grid + (scale+grid) * i
            for j in range(height):
                if layer[i][j] != air_state:
                    y = offset + grid + (scale+grid) * j

                    img.paste(textures[layer[i][j]], (x, y), mask=textures[layer[i][j]])

                    b = clean_base(palette[layer[i][j]]["Name"])
                    legend[b] = textures_base[layer[i][j]]
                    if b not in blocks.keys():
                        blocks[b] = 1
                    else:
                        blocks[b] += 1

        # draw legend
        x = img_size[0] - offset * text_offset + (grid * 2)
        y = offset
        for k, v in legend.items():
            img.paste(v, (x, y), mask=v)
            img_draw.text((x + scale + 30, y), k, font=font)
            y += v.size[1] + 4

        if showDebug:
            print(f"FINISH IMAGE: {i_layer + 1} / {nbr_layer}")
        else:
            print(f"{int((i_layer + 1) / nbr_layer * 100)}%", end=" - ")

        img.save(img_path)

    with open(path.join(i_path, path.basename(filepath[0:-4]) + "_data.csv"), 'w') as file:
        file.write("Block; Number; Stack x64; Stack x16")
        for k, v in blocks.items():
            file.write(f"\n{k};{v};{str(v//64) + ' stack and ' + str(v%64)};{str(v//16) + ' stack and ' + str(v%16)}")

    if showDebug:
        print("DATA FILE CREATED")
    else:
        print("")

def draw_square(img, x1, y1, x2, y2, color):
    for x in range(x1, x2):
        for y in range(y1, y2):
            img[x, y] = color

def get_textures(palette, size):
    texture_path = "../temp/to_schema/textures/blocks"

    unexisting_file = []
    unexisting_properties = []

    textures = []
    textures_base = []
    for tex in palette:
        tex_path = path.join(texture_path, clean_base(tex["Name"]) + ".png")
        if not path.exists(tex_path):
            if path.basename(tex_path) not in unexisting_file:
                unexisting_file.append(path.basename(tex_path))
            tex_path = path.join(texture_path, "debug.png")

        img = Image.open(tex_path).convert("RGBA")
        textures_base.append(img.copy().resize((size, size)))

        if "Properties" in tex.keys():
            properties = tex["Properties"]
            keys = list(properties.keys())

            if "waterlogged" in keys:
                if properties["waterlogged"]:
                    img_2 = Image.open(path.join(texture_path, "properties", "waterlogged.png")).convert("RGBA")
                    img_2.paste(img, (0, 0), mask=img)
                keys.remove("waterlogged")

            if "part" in keys:
                if properties["part"] == "head":
                    img = img.crop((0, 0, 16, 16))
                else:
                    img = img.crop((0, 16, 16, 32))
                keys.remove("part")

            for i in keys:
                img_path = path.join(texture_path, "properties", i + "_" + tex["Properties"][i] + ".png")
                if not path.exists(img_path):
                    if path.basename(img_path) not in unexisting_file:
                        unexisting_properties.append(path.basename(img_path))
                else:
                    addon = Image.open(img_path).convert("RGBA")
                    img.paste(addon, (0, 0), mask=addon)

        textures.append(img.resize((size, size)))

    if unexisting_file != []:
        print("Needed files:", unexisting_file)
    if unexisting_properties != []:
        print("Needed properties:", unexisting_properties)

    return textures_base, textures

def apply_color(img, img_modify, blend):
    tex_path = "../temp/to_schema/textures/blocks"
    img = path.join(tex_path, img)
    img_modify = path.join(tex_path, img_modify)
    # apply color to sprite
    blend = rgb_to_hsv(blend)

    img = Image.open(img).convert("RGBA")
    img_draw = img.load()
    img_size = img.size
    for x in range(img_size[0]):
        for y in range(img_size[1]):
            color = img_draw[x, y]

            alpha = color[3]
            color = rgb_to_hsv(list(color[0:3]))

            color = [int(i) for i in hsv_to_rgb((blend[0], blend[1], (blend[2] + color[2]) / 2))]

            img_draw[x, y] = tuple(color + [alpha])

    img.save(img_modify)

def make_mask(img_base_path, img_path, mask_path):
    tex_path = "../temp/to_schema/textures/blocks"
    img_base_path = path.join(tex_path, img_base_path)
    img_path = path.join(tex_path, img_path)

    mask = Image.open(mask_path).load()
    img_draw = Image.open(img_base_path).load()

    img_slab = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    img_slab_draw = img_slab.load()
    for x in range(16):
        for y in range(16):
            if mask[x, y][3] == 255:
                img_slab_draw[x, y] = img_draw[x, y]

    img_slab.save(img_path)

if __name__ == "__main__":
    mask_slab = "../temp/to_schema/textures/masks/mask_slab.png"
    mask_stairs = "../temp/to_schema/textures/masks/mask_stairs.png"
    mask_fence = "../temp/to_schema/textures/masks/mask_fence.png"
    mask_sign = "../temp/to_schema/textures/masks/mask_sign.png"
    mask_wall_sign = "../temp/to_schema/textures/masks/mask_wall_sign.png"

    # make_mask("spruce_planks.png", "spruce_slab.png", mask_slab)
    # make_mask("spruce_planks.png", "spruce_stairs.png", mask_stairs)
    # make_mask("smooth_quartz.png", "smooth_quartz_stairs.png", mask_stairs)
    # make_mask("smooth_quartz.png", "smooth_quartz_slab.png", mask_slab)
    # make_mask("spruce_planks.png", "spruce_fence.png", mask_fence)
    # make_mask("dark_oak_planks.png", "dark_oak_wall_sign.png", mask_wall_sign)
    # make_mask("dark_oak_planks.png", "dark_oak_sign.png", mask_sign)
    # make_mask("smooth_sandstone.png", "smooth_sandstone_stairs.png", mask_stairs)
    # make_mask("oak_planks.png", "oak_stairs.png", mask_stairs)
    # make_mask("oak_planks.png", "oak_slab.png", mask_slab)

    # apply_color("blend/redstone.png", "redstone_wire.png", (255, 0, 0))
    # apply_color("blend/water_still.png", "water.png", (72, 80, 204))

    nbt_to_png("../temp/to_schema/cod.nbt", 16, 3, 50, False)
    nbt_to_png("../temp/to_schema/pufferfish.nbt", 32, 6, 100, False)
    nbt_to_png("../temp/to_schema/salmon_0.nbt", 32, 6, 100, False)
    nbt_to_png("../temp/to_schema/salmon_1.nbt", 32, 6, 100, False)

    print("FINISH !")
