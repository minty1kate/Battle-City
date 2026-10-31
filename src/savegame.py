"""Сохранение и загрузка игры"""

import json
from pathlib import Path

from src.levels import LEVELS
from src.settings import (
    BonusType, BulletType, Direction, EnemyType, GameState, StrategyType, Team, TileType
)
from src.sprites import Block, Bonus, Bullet, EnemyTank, PlayerTank

SAVE_VERSION = 1
SAVE_PATH = Path(__file__).resolve().parent.parent / "save.json"


class SaveError(Exception):
    """Ошибка сохранения или загрузки"""

def snapshot(game):
    """Собирает состояние игры в словарь"""
    player = game.player
    return {
        "version": SAVE_VERSION,
        "level": game.level_idx,
        "enemies_killed": game.enemies_killed,
        "spawn_timer": game.spawn_timer,
        "player": {
            "x": player.rect.x,
            "y": player.rect.y,
            "direction": player.direction.name,
            "hp": player.hp,
            "lives": player.lives,
            "stars": player.stars,
            "score": player.score,
            "cooldown": player.cooldown,
            "burn_timer": player.burn_timer,
            "invulnerable_timer": player.invulnerable_timer,
        },
        "blocks": [
            [int(block.type), block.rect.x, block.rect.y, block.hp]
            for block in [*game.all_blocks, *game.bushes]
        ],
        "enemies": [
            {
                "type": enemy.enemy_type.name,
                "strategy": enemy.strategy.name,
                "x": enemy.rect.x,
                "y": enemy.rect.y,
                "direction": enemy.direction.name,
                "hp": enemy.hp,
                "ai_timer": enemy.ai_timer,
                "heal_timer": enemy.heal_timer,
                "cooldown": enemy.cooldown,
                "burn_timer": enemy.burn_timer,
            }
            for enemy in game.enemies
        ],
        "bullets": [
            {
                "x": bullet.rect.centerx,
                "y": bullet.rect.centery,
                "direction": bullet.direction.name,
                "type": bullet.type.name,
                "team": bullet.owner_team.name,
                "stars": bullet.owner_stats,
            }
            for bullet in game.bullets
        ],
        "bonuses": [
            {"type": bonus.type.name, "x": bonus.rect.centerx, "y": bonus.rect.centery}
            for bonus in game.bonuses
        ],
    }


def build_player(game, data):
    """Создаёт танк игрока по записи"""
    player = PlayerTank(data["x"], data["y"], game.all_blocks)
    player.direction = Direction[data["direction"]]
    player.hp = float(data["hp"])
    player.lives = int(data["lives"])
    player.stars = int(data["stars"])
    player.score = int(data["score"])
    player.cooldown = int(data["cooldown"])
    player.burn_timer = int(data["burn_timer"])
    player.invulnerable_timer = int(data["invulnerable_timer"])
    return player


def build_enemy(game, data):
    """Создаёт вражеские танки по записи"""
    enemy = EnemyTank(data["x"], data["y"], game.all_blocks,
                      EnemyType[data["type"]], StrategyType[data["strategy"]])
    enemy.direction = Direction[data["direction"]]
    enemy.hp = float(data["hp"])
    enemy.ai_timer = int(data["ai_timer"])
    enemy.heal_timer = int(data["heal_timer"])
    enemy.cooldown = int(data["cooldown"])
    enemy.burn_timer = int(data["burn_timer"])
    return enemy


def build_bullet(game, data):
    """Создаёт пулю по записи"""
    return Bullet(data["x"], data["y"], Direction[data["direction"]], BulletType[data["type"]],
                  Team[data["team"]], game.all_blocks, int(data["stars"]))


def build_block(item):
    """Создаёт блоки карты по записи"""
    tile_type, x, y, hp = item
    block = Block(x, y, TileType(tile_type))
    block.hp = float(hp)
    return block


def restore(game, data):
    """Восстанавливает игру из словаря"""
    try:
        level = int(data["level"])
        if data["version"] != SAVE_VERSION or not 0 <= level < len(LEVELS):
            raise ValueError("неподдерживаемое сохранение")
        parsed = {
            "player": build_player(game, data["player"]),
            "blocks": [build_block(item) for item in data["blocks"]],
            "enemies": [build_enemy(game, item) for item in data["enemies"]],
            "bullets": [build_bullet(game, item) for item in data["bullets"]],
            "bonuses": [Bonus(item["x"], item["y"], BonusType[item["type"]])
                        for item in data["bonuses"]],
        }
        enemies_killed = int(data["enemies_killed"])
        spawn_timer = int(data["spawn_timer"])
    except (KeyError, TypeError, ValueError, AttributeError) as err:
        raise SaveError("Файл сохранения повреждён") from err

    for group in (game.all_blocks, game.bushes, game.bullets, game.enemies, game.bonuses):
        group.empty()
    for block in parsed["blocks"]:
        target = game.bushes if block.type == TileType.BUSH else game.all_blocks
        target.add(block)
    game.enemies.add(*parsed["enemies"])
    game.bullets.add(*parsed["bullets"])
    game.bonuses.add(*parsed["bonuses"])

    game.player = parsed["player"]
    game.level_idx = level
    game.enemies_killed = enemies_killed
    game.spawn_timer = spawn_timer
    game.level_title_timer = 0
    game.state = GameState.PLAYING


def save_exists(path=None):
    """Есть ли файл сохранения"""
    return (path or SAVE_PATH).is_file()


def save_to_file(game, path=None):
    """Записывает состояние игры в файл"""
    path = path or SAVE_PATH
    try:
        path.write_text(json.dumps(snapshot(game)), encoding="utf-8")
    except OSError as err:
        raise SaveError(f"Не удалось сохранить игру: {err.strerror or err}") from err


def load_from_file(game, path=None):
    """Читает файл и восстанавливает игру"""
    path = path or SAVE_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as err:
        raise SaveError("Сохранение не найдено") from err
    except (OSError, ValueError) as err:
        raise SaveError("Файл сохранения повреждён") from err
    restore(game, data)