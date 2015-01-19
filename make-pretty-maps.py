
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
    maps = ('elw', 'el', 'veg', 'vol', 'tmp', 'bm')
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
    return {'dirt'='f_dirt.png',
            'mountains'='f_mountains.png',
            'trees'='f_trees.png'}

def make_fantasy_map():
    """Makes the fantasy map - a work in progress."""
    maps = get_png_maps()
    pics = get_base_images()

    # images will be a dict of Image objects, same keys as the above
    images = {}
    for k in maps.keys():
        images[k] = Image.open(maps[k])
    for k in pics.keys():
        images[k] = Image.open(pics[k])

    # TODO:  process images

    # set up layers in order
    # remove land from ocean layers, ocean from land layers
    #    by color-select and transparency
    # fill land with dirt pattern
    # fill mountain biome with mountain pattern
    # add tree layer, transparency dependin on veg density



