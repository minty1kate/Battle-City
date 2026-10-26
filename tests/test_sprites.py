import pygame
import pytest

from src.settings import (
    TILE_SIZE, WIDTH, GREEN, CYAN,
    TileType, Team, BulletType, EnemyType, StrategyType
)
from src.sprites import (Block, Bullet, DIRECTIONS, ENEMY_STATS, EnemyTank, PlayerTank,
                         Tank, align)


@pytest.mark.parametrize("value, expected", [(0, 0), (101, 96), (113, 120)])
def test_align_rounds_to_tile_grid(value, expected):
    assert align(value) == expected


@pytest.mark.parametrize("tile", range(TileType.BRICK, TileType.BORDER + 1))
def test_block_image_has_tile_size(tile):
    block = Block(48, 72, tile)
    assert block.image.get_width() == TILE_SIZE
    assert block.image.get_height() == TILE_SIZE
    assert block.rect.topleft == (48, 72)


@pytest.mark.parametrize("tile, bullet_type, stars, expected_hits", [
    (TileType.BRICK, BulletType.NORMAL, 0, 4),
    (TileType.BRICK, BulletType.NORMAL, 3, 2),
    (TileType.BRICK, BulletType.WEAK, 0, 8),
    (TileType.CONCRETE, BulletType.NORMAL, 0, None),
    (TileType.CONCRETE, BulletType.CONCRETE_BREAKER, 0, 1),
    (TileType.CONCRETE, BulletType.NORMAL, 3, 1),
    (TileType.BASE, BulletType.NORMAL, 0, 1),
    (TileType.BORDER, BulletType.NORMAL, 0, None),
    (TileType.WATER, BulletType.NORMAL, 0, None),
    (TileType.ICE, BulletType.NORMAL, 0, None),
    (TileType.BUSH, BulletType.NORMAL, 0, None),
])
def test_block_hits_to_destroy(tile, bullet_type, stars, expected_hits):
    block = Block(0, 0, tile)
    group = pygame.sprite.Group(block)
    hits = None
    for n in range(1, 21):
        block.take_damage(bullet_type, stars)
        if block not in group:
            hits = n
            break
    assert hits == expected_hits


@pytest.mark.parametrize("direction", list(DIRECTIONS))
def test_bullet_moves_in_every_direction(direction, blocks):
    dx, dy = DIRECTIONS[direction]
    bullet = Bullet(300, 300, direction, BulletType.NORMAL, Team.PLAYER, blocks)
    x, y = bullet.rect.x, bullet.rect.y
    bullet.update()
    assert (bullet.rect.x, bullet.rect.y) == (x + dx * 6, y + dy * 6)


@pytest.mark.parametrize("bullet_type, stars, speed", [
    (BulletType.NORMAL, 0, 6),
    (BulletType.WEAK, 0, 3),
    (BulletType.CONCRETE_BREAKER, 0, 9),
    (BulletType.NORMAL, 1, 9),
])
def test_bullet_speed(bullet_type, stars, speed, blocks):
    assert Bullet(0, 0, "UP", bullet_type, Team.PLAYER, blocks, stars).speed == speed


@pytest.mark.parametrize("bullet_type, damage", [
    (BulletType.NORMAL, 1.0),
    (BulletType.WEAK, 0.5),
    (BulletType.CONCRETE_BREAKER, 1.0),
    (BulletType.INCENDIARY, 1.0),
])
def test_bullet_damage(bullet_type, damage, blocks):
    assert Bullet(0, 0, "UP", bullet_type, Team.ENEMY, blocks).damage == damage


def test_bullet_damages_brick_and_disappears(blocks):
    brick = Block(240, 240, TileType.BRICK)
    blocks.add(brick)
    bullet = Bullet(250, 270, "UP", BulletType.NORMAL, Team.PLAYER, blocks)
    group = pygame.sprite.Group(bullet)
    bullet.update()
    assert bullet not in group
    assert brick.hp == 3.0


@pytest.mark.parametrize("tile", [TileType.WATER, TileType.ICE, TileType.BUSH])
def test_bullet_flies_over_water_ice_and_bush(tile, blocks):
    blocks.add(Block(240, 240, tile))
    bullet = Bullet(250, 270, "UP", BulletType.NORMAL, Team.PLAYER, blocks)
    group = pygame.sprite.Group(bullet)
    bullet.update()
    assert bullet in group


def test_cooldown_counts_down(blocks):
    tank = Tank(0, 0, blocks)
    tank.cooldown = 2
    tank.handle_effects()
    assert tank.cooldown == 1


def test_invulnerability_blocks_burning(blocks):
    tank = Tank(0, 0, blocks)
    tank.hp = 3.0
    tank.burn_timer = 31
    tank.invulnerable_timer = 10
    tank.handle_effects()
    assert tank.hp == 3.0
    assert tank.invulnerable_timer == 9


def test_shoot_makes_bullet_and_starts_cooldown(blocks):
    tank = Tank(100, 100, blocks)
    tank.direction = "LEFT"
    bullets = pygame.sprite.Group()
    tank.shoot(bullets, BulletType.NORMAL, Team.ENEMY)
    bullet = bullets.sprites()[0]
    assert (bullet.direction, bullet.owner_team) == ("LEFT", Team.ENEMY)
    assert tank.cooldown == tank.shoot_delay


@pytest.mark.parametrize("tile", [TileType.BRICK, TileType.CONCRETE, TileType.WATER, TileType.BORDER])
def test_solid_tiles_push_tank_back(tile, blocks):
    blocks.add(Block(264, 240, tile))
    tank = Tank(244, 240, blocks)
    tank.rect.x = 247
    assert tank.check_tile_collisions(244, 240) is True
    assert tank.rect.x == 244


@pytest.mark.parametrize("tile", [TileType.ICE, TileType.BUSH])
def test_ice_and_bush_do_not_block(tile, blocks):
    blocks.add(Block(240, 240, tile))
    assert Tank(240, 240, blocks).check_tile_collisions(240, 240) is False


def test_ice_makes_tank_slide(blocks):
    blocks.add(Block(240, 240, TileType.ICE))
    tank = Tank(240, 240, blocks)
    tank.check_tile_collisions(240, 240)
    assert tank.is_sliding
    blocks.empty()
    tank.check_tile_collisions(240, 240)
    assert not tank.is_sliding


def test_other_tank_blocks_movement(blocks):
    a, b = Tank(100, 100, blocks), Tank(118, 100, blocks)
    assert a.check_tile_collisions(80, 100, [b]) is True
    assert a.rect.x == 80


def make_player(blocks, x=240, y=240):
    return PlayerTank(x, y, blocks), pygame.sprite.Group(), pygame.sprite.Group()


def test_player_defaults(blocks):
    p = PlayerTank(0, 0, blocks)
    assert (p.hp, p.lives, p.stars, p.score) == (3.0, 3, 0, 0)


@pytest.mark.parametrize("key, direction", [
    (pygame.K_UP, "UP"), (pygame.K_DOWN, "DOWN"), (pygame.K_LEFT, "LEFT"), (pygame.K_RIGHT, "RIGHT"),
    (pygame.K_w, "UP"), (pygame.K_s, "DOWN"), (pygame.K_a, "LEFT"), (pygame.K_d, "RIGHT"),
])
def test_player_moves(key, direction, blocks, make_keys):
    player, bullets, enemies = make_player(blocks)
    dx, dy = DIRECTIONS[direction]
    player.update(make_keys(key), bullets, enemies)
    assert (player.rect.x, player.rect.y) == (240 + dx * 3, 240 + dy * 3)
    assert player.direction == direction


def test_player_stays_when_nothing_pressed(blocks, make_keys):
    player, bullets, enemies = make_player(blocks)
    player.update(make_keys(), bullets, enemies)
    assert (player.rect.x, player.rect.y) == (240, 240)


def test_player_cannot_leave_the_map(blocks, make_keys):
    player, bullets, enemies = make_player(blocks, 0, 240)
    player.update(make_keys(pygame.K_LEFT), bullets, enemies)
    assert player.rect.x == 0
    player, bullets, enemies = make_player(blocks, WIDTH - 20, 240)
    player.update(make_keys(pygame.K_RIGHT), bullets, enemies)
    assert player.rect.x == WIDTH - 20


def test_wall_stops_player(blocks, make_keys):
    blocks.add(Block(264, 240, TileType.BRICK))
    player, bullets, enemies = make_player(blocks, 244, 240)
    player.update(make_keys(pygame.K_RIGHT), bullets, enemies)
    assert player.rect.x == 244


def test_enemy_tank_stops_player(blocks, make_keys):
    player, bullets, enemies = make_player(blocks, 100, 240)
    enemies.add(EnemyTank(121, 240, blocks, EnemyType.SIMPLE, StrategyType.PATROL))
    player.update(make_keys(pygame.K_RIGHT), bullets, enemies)
    assert player.rect.x == 100


def test_shooting_and_cooldown(blocks, make_keys):
    player, bullets, enemies = make_player(blocks)
    player.update(make_keys(pygame.K_SPACE), bullets, enemies)
    assert len(bullets) == 1
    assert bullets.sprites()[0].owner_team == Team.PLAYER
    assert player.cooldown == 40
    player.update(make_keys(pygame.K_SPACE), bullets, enemies)
    assert len(bullets) == 1 and player.cooldown == 39


def test_no_bullet_without_space(blocks, make_keys):
    player, bullets, enemies = make_player(blocks)
    player.update(make_keys(), bullets, enemies)
    assert len(bullets) == 0


def test_two_stars_speed_up_shooting(blocks, make_keys):
    player, bullets, enemies = make_player(blocks)
    player.stars = 2
    player.update(make_keys(pygame.K_SPACE), bullets, enemies)
    assert player.cooldown == 25


def test_stars_are_passed_to_bullet(blocks, make_keys):
    player, bullets, enemies = make_player(blocks)
    player.stars = 1
    player.update(make_keys(pygame.K_SPACE), bullets, enemies)
    assert bullets.sprites()[0].speed == 9


def test_shield_changes_player_color(blocks, make_keys):
    player, bullets, enemies = make_player(blocks)
    player.update(make_keys(), bullets, enemies)
    assert player.last_look == ("UP", GREEN)
    player.invulnerable_timer = 50
    player.update(make_keys(), bullets, enemies)
    assert player.last_look == ("UP", CYAN)


def make_enemy(blocks, kind=EnemyType.SIMPLE, strategy=StrategyType.PATROL, x=240, y=240):
    return EnemyTank(x, y, blocks, kind, strategy)


@pytest.mark.parametrize("kind", list(ENEMY_STATS))
def test_enemy_stats_match_type(kind, blocks):
    enemy, stats = make_enemy(blocks, kind), ENEMY_STATS[kind]
    assert enemy.speed == stats["speed"]
    assert enemy.hp == enemy.max_hp == stats["hp"]
    assert enemy.bullet_type == stats["bullet"]
    assert enemy.shoot_delay == stats["shoot_delay"]


def test_four_enemy_types_with_four_bullet_kinds():
    assert len(ENEMY_STATS) == 4
    assert {s["bullet"] for s in ENEMY_STATS.values()} == {
        BulletType.WEAK,
        BulletType.NORMAL,
        BulletType.CONCRETE_BREAKER,
        BulletType.INCENDIARY
    }


def test_sliding_adds_speed(blocks):
    enemy = make_enemy(blocks)
    enemy.is_sliding = True
    assert enemy.get_speed([enemy]) == 3


def test_enemy_update_moves_enemy(blocks):
    enemy, bullets = make_enemy(blocks), pygame.sprite.Group()
    enemy.update(PlayerTank(0, 0, blocks), bullets, pygame.sprite.Group(enemy))
    assert enemy.rect.y == 238
    assert len(bullets) == 0
