"""FUCK module, because that's what I often say when using the Curses module.

The display module interface for curses.

"""


import curses
from config import ini


# cONFIG ######################################################################


# reprocess tile types...
# should we grab from table?
TILE_TYPES = ini('tiles')
TILE_TYPES[None] = TILE_TYPES['default']


# text effects
EFFECTS = {
           'blink': curses.A_BLINK,
           'standout': curses.A_STANDOUT,
           'bold': curses.A_BOLD,
           'dim': curses.A_BOLD,
           'reverse': curses.A_REVERSE,
           'underline': curses.A_UNDERLINE
          }


# color definitions
COLORS = {
          'black': curses.COLOR_BLACK,
          'red': curses.COLOR_RED,
          'green': curses.COLOR_GREEN,
          'yellow': curses.COLOR_YELLOW,
          'blue': curses.COLOR_BLUE,
          'magenta': curses.COLOR_MAGENTA,
          'cyan': curses.COLOR_CYAN,
          'white': curses.COLOR_WHITE,
          'green': curses.COLOR_GREEN
         }


# tile themes
# for table in db?
THEMES = ini('themes')
THEMES[None] = THEMES['default']


# draw utils ##################################################################


def probe():
    """Probe various settings/terminal configuraiton."""

    screen = curses.initscr()
    y, x  = screen.getmaxyx()
    curses.endwin()
    return x, y


def draw_map(screen, canvas):
    existing_pairs = {}  # (foreground, background)
    pair_index = 1

    for coord_def in canvas.iter_defs():
        subset_key = coord_def['subset_key']
        x, y = coord_def['x'], coord_def['y']
        tile_type = coord_def['tile_type']
        tile_data = TILE_TYPES[tile_type]
        character = tile_data['character']
        theme = THEMES[tile_data['theme']]
        foreground = COLORS[theme['foreground']]
        background = COLORS[theme['background']]
        special = theme.get('special', None)

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


def key_map( screen, key_mapping ):
    pass


def test_draw(canvas):
    screen = curses.initscr()

    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.start_color()

    screen = draw_map(screen, canvas)
    screen.refresh()
    curses.endwin()

