"""
Модуль настроек игры. Содержит константы размеров игрового поля, цветовые палитры,
идентификаторы типов клеток и балансные параметры геймплея.
"""
from enum import Enum, IntEnum
import pygame


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
    SNIPER = "sniper"


class EnemyType(Enum):
    """Разновидности вражеских танков"""
    SIMPLE = "simple"
    FAST = "fast"
    SHOOTER = "shooter"
    ARMORED = "armored"
    SNIPER = "sniper"
    SCOUT = "scout"


class StrategyType(Enum):
    """Стратегии поведения врагов"""
    PATROL = "patrol"
    CHASE = "chase"
    BASE = "base"


class Direction(Enum):
    """Направления движения"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class BonusType(Enum):
    """Виды бонусов"""
    SCORE = "score"
    LIFE = "life"
    STAR = "star"
    INVULNERABLE = "invul"
    SPEED = "speed"
    BOMB = "bomb"
    FREEZE = "freeze"
    REPAIR = "repair"


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
    MUD = 8
    MINE = 9


class SoundEvent(Enum):
    """События, на которые игра отвечает звуком"""
    SHOT = "shot"
    ENEMY_SHOT = "enemy_shot"
    HIT = "hit"
    EXPLOSION = "explosion"
    PLAYER_HIT = "player_hit"
    MINE = "mine"
    BONUS = "bonus"
    LEVEL_START = "level_start"
    PAUSE = "pause"
    SAVE = "save"
    GAME_OVER = "game_over"
    WIN = "win"


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
ORANGE = (255, 140, 0)
PURPLE = (160, 32, 240)
LIME = (150, 255, 0)
LIGHT_BLUE = (135, 206, 250)
PINK = (255, 105, 180)

ENEMIES_PER_LEVEL = 10
MAX_ENEMIES_ON_MAP = 5
SPAWN_DELAY = 150
ENEMY_SPAWN_COLS = [2, 12, 22]
PLAYER_START_POS = (2 * TILE_SIZE, 24 * TILE_SIZE)
KILL_SCORE = 200
BONUS_DROP_CHANCE = 0.3
MINE_DAMAGE = 1.0
SPEED_BONUS_FRAMES = 300
FREEZE_FRAMES = 180
CHEAT_GOD_MODE_FRAMES = 999999
CHEAT_MAX_LIVES = 999
CHEAT_FAST_SHOOT_DELAY = 0

BONUS_COLORS = {
    BonusType.SCORE: YELLOW,
    BonusType.LIFE: RED,
    BonusType.STAR: WHITE,
    BonusType.INVULNERABLE: CYAN,
    BonusType.SPEED: LIME,
    BonusType.BOMB: ORANGE,
    BonusType.FREEZE: LIGHT_BLUE,
    BonusType.REPAIR: PINK,
}

SECRET_MENU_SEQUENCE = [pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN]
