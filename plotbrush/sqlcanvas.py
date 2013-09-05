"""canvas: Cartesian Coordinate Map System
Anthony Lemmer

Principles of set theory at play!

Don't worry, with detection systems/events and all that, this fill will get
large quickly enough, albiet rather empty now!

"""


import brush
import random
import math
from collections import OrderedDict
from itertools import product
from config import ini
import sqlite3 as sqlite


# CONSTANTS/CONFIG ############################################################


TILE_TYPES = ini('tiles')
TILE_TYPES[None] = TILE_TYPES['default']


DEFAULT_DATA = {'tile_type': None, 'objects': None}

SETTINGS = ini('settings')
DATABASE_FILE = SETTINGS['database']['file']
DATABASE_TABLE = SETTINGS['database']['map_table']


# sqlite auto #################################################################


def sql_equals_params(**kwargs):
    """Turn kwargs into sqlite key=? statement, also return params!"""

    fields = []
    fields_params = []

    for key, value in kwargs.items():
        fields.append('%s=?' % key)
        fields_params.append(value)

    fields = ' AND '.join(fields)
    return fields, fields_params


def dict_params(join, **kwargs):
    return join.join(['%s=:%s' % (k, k) for k in kwargs])


# Canvas SQLITE Abstraction ###################################################
# move sql into canvas init


class Canvas(object):
    def __init__(self, **kwargs):
        load = kwargs.get('load', None)

        if load:
            conn = sqlite.connect(load)
            conn.text_factory = sqlite.OptimizedUnicode
            cursor = conn.cursor()
            self.conn = conn
            self.cursor = cursor
            # load into memory!
            return

        # we have to setup the memory db!
        self.conn = sqlite.connect(':memory:')
        self.conn.text_factory = sqlite.OptimizedUnicode
        self.cursor = self.conn.cursor()
        conn, cursor = self.conn, self.cursor

        # coordinate definitions table
        sql = '''
              CREATE TABLE coord_defs
              (
               x INTEGER,
               y INTEGER,

               tile_type TEXT,
               subset_key TEXT,

               PRIMARY KEY (x, y)
              )
              '''
        cursor.execute(sql)

        # canvas meta-data
        sql = '''
              CREATE TABLE canvas_meta
              (
               min_x INTEGER,
               min_y INTEGER,

               max_x INTEGER,
               max_y INTEGER,

               width INTEGER,
               height INTEGER,
               area INTEGER,

               default_Data TEXT
              )
              '''
        cursor.execute(sql)
        conn.commit()

        # setup data!
        bottom_right = kwargs['bottom_right']
        max_x, max_y = bottom_right

        top_left = kwargs.get('top_left', (1, 1))
        min_x, min_y = top_left

        sql = '''
              INSERT INTO coord_defs (x, y)
              VALUES (?, ?)
              '''
        coords = brush.rectangle(bottom_right, top_left)

        for coord in coords:
            cursor.execute(sql, coord)

        # parameter table
        sql = '''
              CREATE TABLE parameter
              (
               x INTEGER,
               y INTEGER,

               PRIMARY KEY (x, y)
              )
              '''
        cursor.execute(sql)
        sql = 'INSERT INTO parameter (x, y) VALUES (?, ?)'

        for coord in brush.parameter(coords):
            cursor.execute(sql, coord)

        # append meta
        width = (max_x - min_x) + 1
        height = (max_y - min_y) + 1

        canvas_meta = (
                       min_x,
                       min_y,

                       max_x,
                       max_y,

                       width,
                       height,
                       width * height,  # area

                       None,  # default data
                      )
        sql = '''
              INSERT INTO canvas_meta
              (
               min_x,
               min_y,

               max_x,
               max_y,

               width,
               height,
               area,

               default_data
              )

              VALUES (?, ?, ?, ?, ?, ?, ?, ?)
              '''
        cursor.execute(sql, canvas_meta)

        # subsets...
        sql = '''
              CREATE TABLE subset_keys
              (
               key TEXT PRIMARY KEY
              )
              '''
        cursor.execute(sql)

        # apply changes and set cache
        conn.commit()
        self.refresh_cache()

    def save(self, to_file=False):
        self.conn.commit()

    def iter_defs(self):
        self.cursor.execute('SELECT * FROM coord_defs')

        for row in self.cursor:
            yield {
                   'x': row[0],
                   'y': row[1],

                   'tile_type': row[2],
                   'subset_key': row[3],
                  }

    def iter_coords(self):
        sql = 'SELECT DISTINCT x, y FROM coord_defs'
        self.cursor.execute(sql)

        for plot in self.cursor:
            yield plot

    def get_parameter(self):
        self.cursor.execute('SELECT x, y FROM parameter')
        return frozenset(self.cursor.fetchall())

    def get_coords(self):
        """Returns all possible coordinates as frozenset, also sets
        self.coords!

        """

        return frozenset([coord for coord in self.iter_coords()])
 
    def new_subset(self, key):
        sql = 'INSERT INTO subset_keys (key) VALUES (?)'
        self.cursor.execute(key, (key,))

    def get_subset_keys(self):
        self.cursor.execute('SELECT * FROM subset_keys')
        return frozenset([key[0] for key in self.cursor])

    def get_subset_coords(self, *args, **kwargs):
        """Returns the coords belonging to subsets specified."""

        get_all = kwargs.pop('get_all', None)
        ignore = kwargs.pop('ignore', None)  # ignore keys starting with...

        if get_all:
            keys = self.get_subset_keys()

            if ignore:
                for s in ignore:
                    keys = [k for k in keys if not k.startswith(s)]
                
        else:
            keys = args

        if not keys: return frozenset()

        where = []
        params = []

        for key in keys:
            where.append('subset_key=?')
            params.append(key)

        sql = '''
              SELECT x, y FROM coord_defs
              WHERE %s
              ''' % ' OR '.join(where)
        self.cursor.execute(sql, params)
        return frozenset([(x, y) for x, y in self.cursor])

    def meta(self, key):
        """Get metadata!"""

        sql = 'SELECT %s FROM canvas_meta' % key
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    def top_left(self):
        x = self.meta('min_x')
        y = self.meta('min_y')
        return x, y

    def bottom_right(self):
        x = self.meta('max_x')
        y = self.meta('max_y')
        return x, y

    def get_area(self):
        """Get canvas area via meta table!"""

        return self.meta('area')

    def update(self, coords, **kwargs):
        for coord in coords:
            x, y = coord
            set_fields = dict_params(',', **kwargs)
            params = kwargs.copy()
            params['x'] = x
            params['y'] = y
            sql = '''
                  UPDATE coord_defs SET %s 
                  WHERE x=:x and y=:y
                  ''' % set_fields
            self.cursor.execute(sql, params)
            sql = '''select * from coord_defs where x=? and y=?'''
            self.cursor.execute(sql, coord)

    def subset(self, subset_key, coords, **kwargs):
        sql = '''
              INSERT OR IGNORE INTO subset_keys (key) 
              VALUES (?)
              '''
        self.cursor.execute(sql, (subset_key,))
        kwargs['subset_key'] = subset_key
        self.update(coords, **kwargs)

    def belongs(self, coords):
        sql = '''
              SELECT subset_key FROM coord_defs
              WHERE x=? AND y=? AND subset_key NOTNULL
              '''

        for coord in coords:
            self.cursor.execute(sql, coord)
            subset = self.cursor.fetchone()

            if subset: return subset

        return None

    def match(self, **kwargs):
        ignore = kwargs.pop('ignore', None)
        where, where_params = sql_equals_params(**kwargs)
        sql = '''
              SELECT x, y FROM coord_defs
              WHERE %s
              '''

        if ignore:
            for subset_key in ignore:
                where += ' AND subset_key!=?'
                where_params.append(subset_key)

        self.cursor.execute(sql % where, where_params)
        return self.cursor.fetchall()  # should really be a frozenset!!!!!

    def refresh_cache(self):
        """Produce a processor-cache equiv. of the database."""

        min_x = self.meta('min_x')
        min_y = self.meta('min_y')
        max_x = self.meta('max_x')
        max_y = self.meta('max_y')
        area = self.meta('area')

        self.cache = {
                      'parameter': self.get_parameter(),
                      'coords': self.get_coords(),
                      'top_left': (min_x, min_y),
                      'bottom_right': (max_x, max_y),
                      'min_x': min_x,
                      'min_y': min_y,
                      'max_x': max_x,
                      'max_y': max_y,
                      'area': area
                     }
        return self.cache

    def __getitem__(self, key):
        """Return coord definition as a dictionary."""

        sql = 'SELECT *  FROM coord_defs WHERE x=? AND y=?'
        self.cursor.execute(sql, key)
        coord_def = self.cursor.fetchone()

        try:
            return {
                    'x': coord_def[0],
                    'y': coord_def[1],

                    'tile_type': coord_def[2],
                    'subset_key': coord_def[3],
                   }
        except TypeError:
            return None


# CONSTRUCTORS ################################################################

    def _subset( self, name, iterable, **kwargs ):
        """Define a named subset, as the coordinates therein iterable.
        
        Optional kwargs updates the data for coordinates therein iterable.
        
        """

        self.subsets[name] = frozenset(iterable)
        self.update_subset(name, **kwargs)

    def _update_subset( self, subset_name, **kwargs ):
        """Update the data for each coordinate in subset, with kwargs as data.

        I'm not using slicing here because that would technically be slower due
        to more calculations required for this particular operation.

        """
        
        for coordinate in self.subsets[subset_name]:
            self.data[coordinate].update(kwargs)

    def _update( self, coordinates, **data ):
        """Update a set of coordinates with data."""

        for coordinate in coordinates:
            self.data[coordinate].update(**data)

    def ___getitem__( self, coordinate ):
        if type(coordinate) == type(slice(1)):
            start = coordinate.start
            stop = coordinate.stop
            return {c: self.data[c] for c in brush.iter_coords( stop, start )}

        return self.data[coordinate]

    def ___setitem__( self, coordinate, data ):
        """Update data for coordinate. Can update a slice of coordinates.
        
        >>> map_data = CartesianSet((3,3))
        >>> map_data[(1,1):(3,1)] = {'tile_type': 'wall'}
        >>> print map_data[(1,1):(3,3)]
        
        """

        if type(coordinate) == type(slice(1)):
            start = coordinate.start
            stop = coordinate.stop

            for coord in itercoords( stop, start ):
                self.data[coord].update(data)

            return

        self.data[coordinate].update(data)

    def ___delitem__( self, coordinate ):
        if type(coordinate) == type(slice(1)):
            start = coordinate.start
            stop = coordinate.stop

            for coord in brush.iter_coords( stop, start ):
                self.data[coord] = self.default_data

            return
        
        self.data[coordinate] = self.default_data

    def ___iter__(self):
        for coordinate, data in self.data.items():
            yield coordinate, data

    def ___contains__( self, coordinate ):
        return coordinate in self.coordinates

    def _belongs( self, plots, map_subsets=None ):
        """map_subsets runs every subset through a function."""

        for subset_name, subset in self.subsets.items():
            if map_subsets:
                subset = map_subsets(subset)

            if subset.intersection(plots):
                return subset_name

        return None


def adjacent(plot, viable_plots=None):
    """Return the supposed neighbors of cartesian plot.

    TOTALLY BELONGS IN BRUSH MODULE

    >>> adjacent((2,2))
    ... # doctest: +NORMALIZE_WHITESPACE
    {'diagonal': frozenset([(1, 3), (3, 1), (1, 1), (3, 3)]),
    'adjacent': frozenset([(1, 2), (3, 2), (2, 3), (2, 1)])}

    """

    x, y = plot

    # North, East, West, and South
    #  1 2 3 4 5
    # 1
    # 2
    # 3
    # 4
    # 5
    n = y - 1
    e = x + 1
    s = y + 1
    w = x - 1

    north = (x, n)
    north_east = (e, n)
    north_west = (w, n)

    south = (x, s)
    south_east = (e, s)
    south_west = (w, s)

    east = (e, y)
    west = (w, y)

    adj = set([north, east, south, west])
    diag = set([north_east, north_west, south_east, south_west])

    if viable_plots:
        adj = set([neighbor for neighbor in adj if neighbor in viable_plots])
        diag = set([neighbor for neighbor in diag if neighbor in viable_plots])

    return {'adjacent': adj, 'diagonal': diag}

