#!/usr/bin/env python
"""A pure-python (and PIL) version of the DF Map Maker scripts.

The current scripts require Photoshop, or GIMP, to be installed, and are a
pain to configure properly.  This module aims to process maps the same way,
with minimal dependancies.  The ultimate goal is to include this in PyLNP.
"""

class Log(object):
    """A placeholder for the PyLNP logging system."""
    @staticmethod
    def v(s):
        print('Verbose:  ' + str(s))
    @staticmethod
    def d(s):
        print('Debug:  ' + str(s))
    @staticmethod
    def i(s):
        print('Info:  ' + str(s))
    @staticmethod
    def w(s):
        print('Warning:  ' + str(s))
    @staticmethod
    def e(s):
        print('Error:  ' + str(s))
log = Log()

import os, glob
try:
    from PIL import Image
except ImportError:
    log.e('could not import PIL')
    raise

def get_region_info():
    """Returns a tuple of strings for an available region and date.
    Eg: ('region1', '00250-01-01')
    """
    globbed = glob.glob('region*-*.png') + glob.glob('region*-*.bmp')
    if globbed:
        fname = os.path.basename(globbed[0])
        idx = fname.index('-')
        return (fname[:idx], fname[idx+1:idx+12])
    log.e('No maps available.')

def tile_pic(pic, size):
    """Repeat an image to the requested size (tile pics across map)."""
    # TODO:  there must be a native way to do this.  Use it.
    result_image = Image.new('RGBA', size)
    x = 0
    while x < size[0]:
        y = 0
        while y < size[1]:
            result_image.paste(pic, (x, y))
            y += pic.size[1]
        x += pic.size[0]
    return result_image

def get_layers(style):
    """Return a dictionary of name fragments to Image objects.

    Images are the maps 'bm', 'el', 'elw', 'tmp', 'veg', 'vol'; images
    of the same size tiled from 'dirt', 'mtns', 'trees' for the style.
    """
    img = {}
    maps = ('bm', 'el', 'elw', 'tmp', 'veg', 'vol')
    for k in maps:
        m = glob.glob('-'.join(get_region_info()) + '-' + k + '.???')
        if m: img[k] = Image.open(m[0])
    pics = {'dirt': style+'_dirt.png',
            'mtns': style+'_mountains.png',
            'trees': style+'_trees.png'}
    for name, fname in pics.items():
        img[name] = tile_pic(Image.open(fname), img['el'].size)
    return img

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

def make_map(style):
    """Make a map in 'style' from dict of Image objects 'img', and return
    the resulting Image object."""
    img = get_layers(style)
    # Initialise the output map
    img[style] = Image.new('RGB', img['el'].size)

    # Get masks for various regions of interest
    oceanMask = ocean_mask(img['elw'])
    mtnsMask = mountain_mask(img['bm'])

    # generate ocean layer from colors in bm, elw
    # fill land with dirt pattern
    # fill mountain biome with mountain pattern
    # add tree layer, transparency depending on veg density

    # Return output map
    return img[style]

def make_fantasy_map():
    """Makes the fantasy map - a work in progress."""
    output = make_map('fantasy')
    fname = '-'.join(get_region_info()) + '-fantasy.png'
    output.save(fname, format='PNG', optimize=True)

#make_fantasy_map()

