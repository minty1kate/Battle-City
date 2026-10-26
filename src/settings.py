"""
Модуль настроек игры. Содержит константы размеров игрового поля, цветовые палитры,
идентификаторы типов клеток и балансные параметры геймплея.
"""
from enum import Enum, IntEnum

class GameState(Enum):
    """Состояние игрового процесса"""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    WIN = "win"

class Team(Enum):
    """Принадлежность  командам"""
    PLAYER = "player"
    ENEMY = "enemy"

class BulletType(Enum):
    """Типы вооружения"""
    NORMAL = "normal"
    WEAK = "weak"
    CONCRETE_BREAKER = "concrete_breaker"
    INCENDIARY = "incendiary"

class EnemyType(Enum):
    """Разновидности вражеских танков"""
    SIMPLE = "simple"
    FAST = "fast"
    SHOOTER = "shooter"
    ARMORED = "armored"

class StrategyType(Enum):
    """Стратегии поведения врагов"""
    PATROL = "patrol"
    CHASE = "chase"
    BASE = "base"

class TileType(IntEnum):
    """Типы блоков на карте"""
    EMPTY = 0
    BRICK = 1
    CONCRETE = 2
    WATER = 3
    ICE = 4
    BUSH = 5
    BASE = 6
    BORDER = 7

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

ENEMIES_PER_LEVEL = 10
MAX_ENEMIES_ON_MAP = 5
SPAWN_DELAY = 150
ENEMY_SPAWN_COLS = [2, 12, 22]
PLAYER_START_POS = (2 * TILE_SIZE, 24 * TILE_SIZE)
KILL_SCORE = 200
BONUS_DROP_CHANCE = 0.3

BONUS_COLORS = {
    'score': YELLOW,
    'life': RED,
    'star': WHITE,
    'invul': CYAN
}
