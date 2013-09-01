import sqlcanvas
from display import fuck
import mapgen
import database
import brush
from timeout import timeout
from config import ini


SETTINGS = ini('settings')


# Debug Examples ##############################################################


def new_map_test(scene):
    # draw map floor, rubble
    bottom_right = (int(SETTINGS['display']['width']), int(SETTINGS['display']['height']))
    canvas = {
              'bottom_right': bottom_right
             }
    canvas = sqlcanvas.Canvas(**canvas)
    coords = canvas.cache['coords']
    canvas.update(coords, tile_type='floor')

    # generate village
    mapgen.generate_scene(canvas, scene)

    # display the actual map
    fuck.test_draw(canvas)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    scene = raw_input('SCENE> ')

    while True:
        timeout(new_map_test, (scene,), timeout=int(SETTINGS['generate']['timeout']))

