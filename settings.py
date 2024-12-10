import pygame as pg

DEBUG = False

WHITE = pg.Color(255,255,255)
BLACK = pg.Color(0,0,0)
GRAY = pg.Color(128,128,128)
RED = pg.Color(255,0,0)
ORANGE = pg.Color(255, 128, 0)
YELLOW = pg.Color(255,255,0)
GREEN = pg.Color(0,255,0)
BLUE = pg.Color(0,0,255)

COLORS = {
    "background": pg.Color(20,90,90),
    "player": GREEN,
    "brick": BLACK,
    "box": BLUE,
    "enemy": RED,
    "lava": ORANGE,
    "gold": YELLOW,
    "score": BLACK
}

SPRITES = {
    "player": "front.png",
    "brick": "block.png",
    "platform": "plank.png",
    "grass": "ground.png",
    "box": "crate.png",
    "enemy": "slime_normal.png",
    "lava": "lava.png",
    "gold": "coin_gold.png",
}
import sys
from pathlib import Path
dir = Path(sys.argv[0]).parent
for name in SPRITES:
    path = f"{dir}/sprites/{SPRITES[name]}"
    SPRITES[name] = pg.image.load(path)

WIDTH = 800
HEIGHT = 500

FPS = 60

GROUND_FRICT = 0.3
MOVING_FRICT = 0.07
GRAVITY = 3
GRAVITY_JUMPING = 2
TERMINAL_VEL = 30

BOX_W = 30

ENEMY_W = 20
ENEMY_H = 20
ENEMY_RAND = 1

GOLD_W = 20
GOLD_H = 20
GOLD_SCORE = 2

PLAYER_W = 30
PLAYER_H = 30
PLAYER_SPEED = 1
JUMP_STRENGTH = 15
COYOTE = 10
LONG_JUMP = 10

from levels import *

BRICK_W = WIDTH/len(LEVELS[0][0])
BRICK_H = HEIGHT/len(LEVELS[0])

from components import GrassBrick, Brick, Enemy, Box, Lava, Goal, SlidingBrick, SlidingBrickBouncer
LAYOUT_KEY = {
    "player": "@",
    "score": "S",
    "#": {
        "type": GrassBrick,
        "merge": True
    },
    "H": {
        "type": Brick,
        "merge": True
    },
    "*": {
        "type": Lava,
        "merge": True
    },
    "-": {
        "type": SlidingBrick,
        "merge": True
    },
    "|": {
        "type": SlidingBrickBouncer,
        "merge": False
    },
    "^": {
        "type": Enemy,
        "merge": False
    },
    "=": {
        "type": Box,
        "merge": False
    },
    "O": {
        "type": Goal,
        "merge": False
    }
}