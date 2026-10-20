"""
Модуль настроек игры. Содержит константы размеров игрового поля, цветовые палитры,
идентификаторы типов клеток и балансные параметры геймплея.
"""

TILE_SIZE = 24
GRID_SIZE = 26
WIDTH = TILE_SIZE * GRID_SIZE
HEIGHT = TILE_SIZE * GRID_SIZE
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREY = (128, 128, 128)
BROWN = (139, 69, 19)
CYAN = (0, 255, 255)

TILE_EMPTY = 0
TILE_BRICK = 1
TILE_CONCRETE = 2
TILE_WATER = 3
TILE_ICE = 4
TILE_BUSH = 5
TILE_BASE = 6
TILE_BORDER = 7

ENEMIES_PER_LEVEL = 10
MAX_ENEMIES_ON_MAP = 5
SPAWN_DELAY = 150
ENEMY_SPAWN_COLS = [2, 12, 22]
PLAYER_START_POS = (2 * TILE_SIZE, 24 * TILE_SIZE)
KILL_SCORE = 200
BONUS_DROP_CHANCE = 0.3
