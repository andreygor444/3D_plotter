from math import pi
from enum import Enum


class Signals(Enum):
    show_chart = 0
    remove_chart = 1
    stop_execution = 2


INF = 10**5
DISPLAY_SIZE = WIDTH, HEIGHT = (800, 800)
CIRCLE_LENGTH = 2 * pi
MOVING_SPEED = 10
ROTATION_COEF = 200
MOVING_COEF = 1
ZOOM_CHANGE_SPEED = 0.05
BG_COLOR = 'black'
FPS = 60

PLOTTER_WINDOW_POS = (950, 140)
GUI_WINDOW_POS = (100, 150)

LEFT_MOUSE_BUTTON = 1
RIGHT_MOUSE_BUTTON = 3
MOUSEWHEELUP = 5
MOUSEWHEELDOWN = 4

DEFAULT_CHARTS = [
    ('x+y', -100, 100, -100, 100, 10, 10, 1),
    ('x-y', -100, 100, -100, 100, 10, 10, 1),
    ('x*y/10', -100, 100, -100, 100, 5, 5, 1),
    ('x/y', -1, 1, -1, 1, 0.1, 0.1, 100),
    ('(sin(x/50+y/50)+1)*50', -300, 300, -300, 300, 20, 20, 1),
    ('(-sin((x/50)^2+(y/50)^2)+1)*50', -250, 250, -250, 250, 7, 7, 1),
    ('(1/(1+(x/100)^2)+1/(1+(y/100)^2))*1000', -1000, 1000, -1000, 1000, 50, 50, 1),
    ('(x^2+y^2)/5', -10, 10, -10, 10, 2, 2, 1),
    ('(x^2+y^2)^0.5*10-140', -100, 100, -100, 100, 10, 10, 1)
]
