"""FUCK module, because that's what I often say when using the Curses module.

The display module interface for curses.

"""


import curses
from utils.config import ini
import sqlcanvas


# cONFIG ######################################################################


# reprocess tile types...
# should we grab from table?
TILES = ini('tiles')
DEFAULT_TILE = TILES['default']

# text effects
EFFECTS = {
           'blink': curses.A_BLINK,
           'standout': curses.A_STANDOUT,
           'bold': curses.A_BOLD,
           'dim': curses.A_BOLD,
           'reverse': curses.A_REVERSE,
           'underline': curses.A_UNDERLINE
          }

COLORS = {
          'black': curses.COLOR_BLACK,
          'blue': curses.COLOR_BLUE,
          'cyan': curses.COLOR_CYAN,
          'green': curses.COLOR_GREEN,
          'magenta': curses.COLOR_MAGENTA,
          'red': curses.COLOR_RED,
          'white': curses.COLOR_WHITE,
          'yellow': curses.COLOR_YELLOW,
         }


# draw utils ##################################################################


def draw_map(screen, canvas, scene):
    default_tile = DEFAULT_TILE.copy()
    default_tile.update(TILES[scene['general']['default_tile']])
    existing_pairs = {}  # (foreground, background)
    pair_index = 1

    for coord_def in canvas.iter_defs():
        tile_type = coord_def['tile_type']

        if tile_type is None:
            tile_data = default_tile
        else:
            tile_data = default_tile.copy()
            tile_data.update(TILES[tile_type])

        subset_key = coord_def['subset_key']
        x, y = coord_def['x'], coord_def['y']

        character = tile_data['character']
        foreground = COLORS[tile_data['foreground']]
        background = COLORS[tile_data['background']]
        special = tile_data.get('special', None)

        if special:
            effects = [EFFECTS[e] for e in special.split(',')]
        else:
            effects = []

        color_key = (foreground, background)

        if color_key in existing_pairs:
            color_pair = existing_pairs[color_key]
        else:
            curses.init_pair(pair_index, foreground, background)
            existing_pairs[color_key] = pair_index
            color_pair = pair_index
            pair_index += 1

        x -= 1
        y -= 1

        color_pair = curses.color_pair(color_pair)

        if special:

            for effect in effects:
                color_pair += effect

        try:
            screen.addstr(y, x, character, color_pair)
        except:
            # out of viewport; who cares~
            pass

    screen.refresh()
    return screen


def init_screen():
    screen = curses.initscr()
    y, x = screen.getmaxyx()

    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.start_color()
    curses.curs_set(0)
    
    return screen, (x, y)


# it'd be real easy to add color now!
# start index at 7, I think
# colors.ini


def top_panel(screen, *args, **kwargs):
    """
    curses.newwin(begin_y, begin_x)
    curses.newwin(nlines, ncols, begin_y, begin_x)
    """

    curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_WHITE)
    color_pair = curses.color_pair(99)
    lines = len(args) + 3  # for padding!
    y, x = screen.getmaxyx()

    # blank space
    blank_line = ' ' * (len(max(args, key=len)) + 2)

    for i in xrange(1, lines):
        screen.addstr(i, 2, blank_line, color_pair)

    # write one arg per line
    for i, line in enumerate(args, start=2):
        screen.addstr(i, 3, line, color_pair)

    return screen


def test_draw(screen, canvas, scene):
    # first get scene data
    author = scene['meta']['author']
    title = scene['meta']['title']

    # draw!
    screen = draw_map(screen, canvas, scene)
    screen = top_panel(screen, author, title)
    screen.refresh()
    curses.endwin()


def auto_scene(scene):
    """Chiefly for debugging purposes."""
    from plotbrush import mapgen
    from plotbrush import sqlcanvas
    screen, bottom_right = init_screen()
    canvas = sqlcanvas.Canvas(bottom_right=bottom_right)
    scene = mapgen.generate_scene(canvas, scene)
    test_draw(screen, canvas, scene)

