import pytest

from src import savegame
from src.settings import Direction, EnemyType, GameState, StrategyType, Team, TileType
from src.sprites import Block, Bullet, EnemyTank


def test_snapshot_contains_game_state(bare_game):
    game = bare_game
    game.player.score = 1234
    game.player.direction = Direction.LEFT
    game.enemies_killed = 3
    data = savegame.snapshot(game)
    assert data["version"] == savegame.SAVE_VERSION
    assert data["player"]["score"] == 1234
    assert data["player"]["direction"] == "LEFT"
    assert data["enemies_killed"] == 3


def test_snapshot_serializes_enemies_bullets_and_bushes(bare_game):
    game = bare_game
    enemy = EnemyTank(300, 200, game.all_blocks, EnemyType.FAST, StrategyType.CHASE)
    enemy.direction = Direction.RIGHT
    game.enemies.add(enemy)
    bullet = Bullet(100, 120, Direction.DOWN, savegame.BulletType.NORMAL,
                    Team.PLAYER, game.all_blocks, 2)
    game.bullets.add(bullet)
    bush = Block(120, 120, TileType.BUSH)
    game.bushes.add(bush)
    data = savegame.snapshot(game)
    assert data["enemies"][0]["strategy"] == "CHASE"
    assert data["bullets"][0]["stars"] == 2
    assert [int(TileType.BUSH), 120, 120, 1.0] in data["blocks"]


def test_save_and_load_round_trip(bare_game, tmp_path):
    game = bare_game
    game.player.score = 900
    game.player.lives = 2
    game.player.direction = Direction.RIGHT
    enemy = EnemyTank(360, 240, game.all_blocks, EnemyType.ARMORED, StrategyType.BASE)
    enemy.hp = 2.5
    game.enemies.add(enemy)
    path = tmp_path / "save.json"
    savegame.save_to_file(game, path)
    assert savegame.save_exists(path)

    game.player.score = 0
    game.enemies.empty()
    savegame.load_from_file(game, path)
    assert game.player.score == 900
    assert game.player.lives == 2
    assert game.player.direction == Direction.RIGHT
    restored = game.enemies.sprites()[0]
    assert restored.enemy_type == EnemyType.ARMORED
    assert restored.hp == 2.5
    assert restored.strategy == StrategyType.BASE
    assert game.state == GameState.PLAYING


def test_restore_rejects_wrong_version(bare_game):
    data = savegame.snapshot(bare_game)
    data["version"] = 999
    with pytest.raises(savegame.SaveError, match="повреждён"):
        savegame.restore(bare_game, data)


def test_restore_rejects_missing_fields(bare_game):
    with pytest.raises(savegame.SaveError):
        savegame.restore(bare_game, {"version": savegame.SAVE_VERSION})


def test_load_missing_file_raises_save_error(bare_game, tmp_path):
    with pytest.raises(savegame.SaveError, match="не найдено"):
        savegame.load_from_file(bare_game, tmp_path / "missing.json")


def test_load_invalid_json_raises_save_error(bare_game, tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{invalid", encoding="utf-8")
    with pytest.raises(savegame.SaveError, match="повреждён"):
        savegame.load_from_file(bare_game, path)


def test_build_helpers_restore_enum_values(bare_game):
    player = savegame.build_player(bare_game, {
        "x": 100, "y": 120, "direction": "DOWN", "hp": 2.5, "lives": 2,
        "stars": 1, "score": 50, "cooldown": 4, "burn_timer": 8,
        "invulnerable_timer": 10,
    })
    assert player.direction == Direction.DOWN
    assert player.hp == 2.5
    assert player.score == 50

    enemy = savegame.build_enemy(bare_game, {
        "x": 200, "y": 220, "type": "SCOUT", "strategy": "PATROL",
        "direction": "LEFT", "hp": 0.5, "ai_timer": 9, "heal_timer": 2,
        "cooldown": 3, "burn_timer": 4,
    })
    assert enemy.enemy_type == EnemyType.SCOUT
    assert enemy.direction == Direction.LEFT
    assert enemy.hp == 0.5

    bullet = savegame.build_bullet(bare_game, {
        "x": 50, "y": 60, "direction": "UP", "type": "WEAK",
        "team": "ENEMY", "stars": 0,
    })
    assert bullet.owner_team == Team.ENEMY


def test_build_block_restores_type_and_hit_points():
    block = savegame.build_block([int(TileType.BRICK), 48, 72, 2.5])
    assert block.type == TileType.BRICK
    assert block.rect.topleft == (48, 72)
    assert block.hp == 2.5
