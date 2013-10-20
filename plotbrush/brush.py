"""brushes: Brushes for painting cartesian coordinate canvas
Anthony Lemmer

Principles of set theory at play!

"""


import random
import math
from collections import OrderedDict
from itertools import product
from utils.config import ini


# CONSTANTS/CONFIG ############################################################


TILE_TYPES = ini('tiles')
TILE_TYPES[None] = TILE_TYPES['default']


DEFAULT_DATA = {'tile_type': None, 'objects': None}

SETTINGS = ini('settings')
DATABASE_FILE = SETTINGS['database']['file']
DATABASE_TABLE = SETTINGS['database']['map_table']


# CONSTRUCTORS ################################################################


def corners(area):
    """Returns corners of given area."""

    top_left = min(area)
    bottom_right = max(area)
    min_x, min_y = top_left
    max_x, max_y = bottom_right
    top_right = (max_x, min_y)
    bottom_left = (min_x, max_y)

    return set([top_left, bottom_right, top_right, bottom_left])


def xrange_corners(bottom_right, top_left=None):
    min_x, min_y = top_left or (1, 1)
    max_x, max_y = bottom_right

    x = xrange(min_x, max_x + 1)
    y = xrange(min_y, max_y + 1)

    return x, y


def iter_coords(bottom_right, top_left=None):
    """Iterator for Cartesian coordinates of a rectangle."""

    x, y = corners(bottom_right, top_left)

    for coord in product(x, y):
        yield coord


def rectangle(bottom_right, top_left=None):
    """Returns frozenset of cartesian coordinate product, thereof top left
    to bottom right.

    bottom_right -- (min_x, min_y) the bottom-right corner of the rectangle
    top_left (optional) -- (max_x, max_y) the top left of the rectangle
    
    >>> for x in rectangle((2, 2)): print x 
    (1, 2)
    (1, 1)
    (2, 1)
    (2, 2)

    >>> for x in rectangle((2, 4), (1, 2)): print x
    (1, 2)
    (1, 3)
    (1, 4)
    (2, 3)
    (2, 2)
    (2, 4)

    """

    x, y = xrange_corners(bottom_right, top_left)
    return frozenset(product(x, y)) 


def parameter(rectangle_area):
    """Return set of a rectangle's boundaries/parameter.

    top_left_bottom_right (bool) -- return only the top left corner and the
                                    bottom right corner.
    
    >>> parameter(cartcoords((3, 3)))
    set([(1, 2), (3, 2), (1, 3), (3, 3), (3, 1), (2, 1), (2, 3), (1, 1)])

    """

    min_x, min_y = min(rectangle_area)
    max_x, max_y = max(rectangle_area)
    boundaries = set()

    # first line of plots
    for x in xrange( min_x, max_x + 1 ):
        plot = (x, min_y)
        boundaries.add(plot)

    # iterate through each row, before the last
    # getting the first and last plot of the row
    for y in xrange( min_y + 1, max_y ):
        plot = (min_x, y)
        boundaries.add(plot)
        plot = (max_x, y)
        boundaries.add(plot)

    # now add the last line of plots...
    for x in xrange( min_x, max_x + 1 ):
        plot = (x, max_y)
        boundaries.add(plot)

    return boundaries


def omit_random( original_set, remove, not_corners=False ):
    """Remove x plots from original_set.
    
    Decides which plots to remove at random. Removes a max of "remove."

    >>> original_set = cartcoords((2,2))
    >>> len(original_set)
    4
    >>> len(omit_random(original_set, 2)[0])
    2

    """

    min_x, min_y = min(original_set)
    max_x, max_y = max(original_set)

    top_left = (min_x, min_y)
    top_right = (max_x, min_y)
    bottom_left = (min_x, max_y)
    bottom_right = (max_x, max_y)
    corners = (top_left, top_right, bottom_left, bottom_right)

    new_set = list(original_set)
    max_index = len(new_set) - 1

    while remove:
        selection = random.randint( 0, max_index )
        plot = new_set[selection]

        if not_corners and plot in corners:
            continue

        del new_set[selection]
        max_index -= 1
        remove -= 1

    new_set = set(new_set)
    return new_set, original_set.difference(new_set)


def random_rectangle( min_x, max_x, y_min, y_max ):
    """This is super sloppy and shitty."""

    random_x_one = random.randint( min_x, max_x )

    new_min_x = random_x_one + min_x
    new_max_x = random_x_one + max_x

    random_x_two = random.randint( new_min_x, new_max_x )

    x = [random_x_one, random_x_two]


def expand(area, padding=1, boundary_check=None):
    """Need to rename variables.
    
    padding -- # of coords from original area to expand
    boundary_check -- new coords must consist of these coords
    
    """

    dist_min = min(area)
    dist_max = max(area)

    try:
        dist_min_x, dist_min_y = dist_min
    except TypeError:
        raise Exception('AREA must be iterable sequence of coords')

    dist_max_x, dist_max_y = dist_max

    dist_min_x -= padding
    dist_max_x += padding
    dist_min_y -= padding
    dist_max_y += padding
    dist_min = (dist_min_x, dist_min_y)
    dist_max = (dist_max_x, dist_max_y)
    dist_area = rectangle(dist_max, dist_min)

    if boundary_check:
        dist_area = boundary_check & dist_area

    return dist_area

