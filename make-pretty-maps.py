
import os, glob
from PIL import Image

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
    """Returns an oceanmask layer; black==land and white==ocean."""
    image_oceanMask = Image.new('L', image_elw.size, color=255)
    pixdata = image_elw.load()
    oceanMask = image_oceanMask.load()
    for y in range(image_elw.size[1]):
        for x in range(image_elw.size[0]):
            # if green channel is empty, pixel is ocean
            if not pixdata[x, y][1] > 0:
                oceanMask[x, y] = 0
    return image_oceanMask

def make_fantasy_map():
    """Makes the fantasy map - a work in progress."""
    maps = get_png_maps()
    pics = get_base_images()

    # images is a dict of Image objects, same keys as above
    images = {}
    for k in maps.keys():
        images[k] = Image.open(maps[k]).convert('RGBA')
    for k in pics.keys():
        images[k] = Image.open(pics[k]).convert('RGBA')

    # initialise fantasy map image
    images['fantasy'] = images['bm'].copy()

    # make ocean transparent in land images

    images['oceanMask'] = ocean_mask(images['elw'])
    for i in ('el', 'fantasy', 'tmp', 'veg', 'vol'):
        images[i].putalpha(images['oceanMask'])


    # generate ocean pattern from colors in bm, elw
    # fill land with dirt pattern
    # fill mountain biome with mountain pattern
    # add tree layer, transparency depending on veg density



    # Finally, save the completed map.
    images['fantasy'].save('-'.join(get_region_info()) + '-fantasy.png',
                           format='PNG', optimize=True)

make_fantasy_map()

