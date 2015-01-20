
import os, glob
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps

"""Make pretty maps - fantasy and satellite style - from DF exports.

Currently using some simplifying assumptions:
    * Exported maps, base images, and this script are in same dir.
"""

def get_region_info():
    """Returns a tuple of strings for an available region and date.
    Eg: ('region1', '00250-01-01')

    Taken from legends processor & in PyLNP and slightly modified
    """
    globbed = glob.glob('region*-*.png') + glob.glob('region*-*.bmp')
    if globbed:
        fname = os.path.basename(globbed[0])
        idx = fname.index('-')
        return (fname[:idx], fname[idx+1:idx+12])
    raise RuntimeError('No maps available.')

def get_png_maps():
    """Returns dict of map IDs as keys and filenames are values.
    Bitmaps are silently compressed to .png"""
    maps = ('bm', 'el', 'elw', 'tmp', 'veg', 'vol')
    fnames = {}
    for k in maps:
        m = glob.glob('-'.join(get_region_info()) + '-' + k + '.???')
        if m and m[0].endswith('.png'):
            fnames[k] = m[0]
        elif m and m[0].endswith('.bmp'):
            Image.open(m[0]).save(m[0].replace('.bmp', '.png'),
                                  format='PNG', optimize=True)
            os.remove(m[0])
            fnames[k] = m[0].replace('.bmp', '.png')
    if len(fnames) < len(maps):
        raise RuntimeError('Insufficient maps available.')
    return fnames

def get_base_images():
    """Returns a dict of base pics short names and paths."""
    return {'dirt':'f_dirt.png',
            'mountains':'f_mountains.png',
            'trees':'f_trees.png'}

def tile_pic(pic, size):
    """Repeat an image to the requested size (tile pics across map)."""
    result_image = Image.new('RGBA', size)
    x = 0
    while x < size[0]:
        y = 0
        while y < size[1]:
            result_image.paste(pic, (x, y))
            y += pic.size[1]
        x += pic.size[0]
    return result_image

def ocean_mask(image_elw):
    """Returns an oceanmask layer; white==ocean."""
    image_oceanMask = Image.new('L', image_elw.size, color=0)
    pixdata = image_elw.load()
    oceanMask = image_oceanMask.load()
    for y in range(image_elw.size[1]):
        for x in range(image_elw.size[0]):
            # if green channel, pixel is not ocean
            if not pixdata[x, y][1] > 0:
                oceanMask[x, y] = 255
    return image_oceanMask

def ocean_layer(image_bm, image_el, mask, dirt):
    """Returns an ocean layer, colored oceans and transparent land."""
    image_ocean = Image.new('RGBA', image_el.size, (0, 0, 0, 255))
    bm = image_bm.load()
    el = image_el.load()
    ocean = image_ocean.load()
    mask = mask.load()
    dirt = dirt.filter(ImageFilter.BLUR).load()
    for y in range(image_el.size[1]):
        for x in range(image_el.size[0]):
            if mask[x, y]:
                if not bm[x, y][1]:
                    bm[x, y] = (0, 128, 255)
                blue = int((bm[x, y][2] + el[x, y][2]*3) / 3 * 1.2)
                if bm[x, y][1] == 255:
                    ocean[x, y] = (int(dirt[x, y]*1.5), 255, 255, 0)
                else:
                    green = int((bm[x, y][1] / bm[x, y][2]) * blue)
                    ocean[x, y] = (0, green, blue, 0)
    return image_ocean

def mountain_mask(image_bm):
    """Return a mountain biome mask, white=mountains"""
    mtns_mask = Image.new('L', image_bm.size, (0))
    mtns = mtns_mask.load()
    bm = image_bm.load()
    for y in range(image_bm.size[1]):
        for x in range(image_bm.size[0]):
            # mountain biome is mid-grey
            if bm[x, y] == (128, 128, 128):
                mtns[x, y] = 255
    return mtns_mask

def mountain_layer(image_mtns, image_el, mask):
    """Return a mountain layer, including elevation for snowcaps."""
    mtns_layer = Image.new('RGBA', image_el.size, (0, 0, 0, 255))
    mtns = mtns_layer.load()
    image_mtns = image_mtns.load()
    el = image_el.load()
    mask = mask.load()
    for y in range(image_el.size[1]):
        for x in range(image_el.size[0]):
            if mask[x, y]:
                if el[x, y][0] > 200: # above snow line
                    g = int((el[x, y][0] * image_mtns[x, y][0]) * 3.2 / 255)
                else:
                    g = int((el[x, y][0] * image_mtns[x, y][0]) * 1.6 / 255)
                mtns[x, y] = (g, g, g)
    return mtns_layer

def make_fantasy_map():
    """Makes the fantasy map - a work in progress."""
    maps = get_png_maps()
    pics = get_base_images()

    # images is a dict of Image objects, same keys as above
    images = {}
    for k in maps.keys():
        images[k] = Image.open(maps[k])
    for k in pics.keys():
        images[k] = tile_pic(Image.open(pics[k]), images['el'].size)

    # initialise fantasy map image in black
    images['fantasy'] = Image.new('RGB', images['bm'].size)

    # generate ocean pattern from colors in bm, elw
    images['oceanMask'] = ocean_mask(images['elw'])
    images['ocean'] = ocean_layer(images['bm'], images['el'],
                                  images['oceanMask'],
                                  images['dirt'].convert('L'))
    images['fantasy'].paste(images['ocean'], (0, 0), images['oceanMask'])

    # fill land with dirt pattern
    images['fantasy'].paste(Image.blend(images['dirt'].convert('RGB'),
                                        images['bm'].convert('RGB'), 0.1),
                            (0, 0), ImageOps.invert(images['oceanMask']))

    # fill mountain biome with mountain pattern
    images['mtn_mask'] = mountain_mask(images['bm'])
    images['mtn_bm'] = mountain_layer(images['mountains'], images['el'],
                                      images['mtn_mask'])
    images['fantasy'].paste(images['mtn_bm'], (0, 0), images['mtn_mask'])

    # add tree layer, transparency depending on veg density
    images['fantasy'].paste(Image.blend(images['bm'].convert('RGB'),
                                        images['trees'].convert('RGB'), 0.4),
                            (0, 0), images['veg'].convert('L'))

    # Finally, save the completed map.
    images['fantasy'].save('-'.join(get_region_info()) + '-fantasy.png',
                           format='PNG', optimize=True)

make_fantasy_map()

