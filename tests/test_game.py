import random

import pygame
import pytest

from src.game import Game
from src.levels import LEVELS
from src.settings import *
from src.sprites import Block, Bonus, Bullet, EnemyTank


def add_enemy(game, kind="simple", x=240, y=240):
    enemy = EnemyTank(x, y, game.all_blocks, kind, "patrol")
    game.enemies.add(enemy)
    return enemy


def add_bullet(game, target, owner, bullet_type="normal"):
    bullet = Bullet(target.rect.centerx, target.rect.centery, "UP", bullet_type, owner,
                    game.all_blocks)
    game.bullets.add(bullet)
    return bullet


def test_game_starts_in_menu():
    g = Game()
    assert g.state == "menu"
    assert g.level_idx == 0
    assert g.player.rect.topleft == PLAYER_START_POS
    pygame.quit()


def test_enter_starts_game(game, send_events, keydown):
    game.state = "menu"
    send_events(keydown(pygame.K_RETURN))
    game.handle_events()
    assert game.state == "playing"

#
# def test_other_keys_do_not_start_game(game, send_events, keydown):
#     game.state = "menu"
#     send_events(keydown(pygame.K_2))
#     game.handle_events()
#     assert game.state == "menu"
#     assert game.level_idx == 0


@pytest.mark.parametrize("key, level", [
    (pygame.K_1, 0), (pygame.K_2, 1), (pygame.K_3, 2), (pygame.K_4, 3),
])
def test_number_keys_switch_level(key, level, game, send_events, keydown):
    send_events(keydown(key))
    game.handle_events()
    assert game.level_idx == level


def test_r_restarts_after_game_over(game, send_events, keydown):
    game.player.score = 500
    game.load_level(2)
    game.state = "game_over"
    send_events(keydown(pygame.K_r))
    game.handle_events()
    assert game.state == "playing"
    assert game.player.score == 0
    assert game.level_idx == 0


def test_r_does_nothing_while_playing(game, send_events, keydown):
    game.player.score = 500
    send_events(keydown(pygame.K_r))
    game.handle_events()
    assert game.player.score == 500


@pytest.mark.parametrize("idx", range(len(LEVELS)))
def test_load_level_builds_all_tiles(idx, game):
    game.load_level(idx)
    tiles = sum(1 for row in LEVELS[idx] for tile in row if tile != TILE_EMPTY)
    assert len(game.all_blocks) + len(game.bushes) == tiles


def test_load_level_clears_objects_and_moves_player(game):
    add_enemy(game)
    game.player.rect.x = 300
    game.enemies_killed = 5
    game.load_level(1)
    assert len(game.enemies) == len(game.bullets) == len(game.bonuses) == 0
    assert game.enemies_killed == 0
    assert game.player.rect.topleft == PLAYER_START_POS


def test_enemy_appears_after_delay(bare_game):
    old_choice = random.choice
    random.choice = lambda seq: seq[0]

    try:
        game = bare_game
        for _ in range(SPAWN_DELAY):
            game.spawn_enemy()
        assert len(game.enemies) == 0
        game.spawn_enemy()
        assert len(game.enemies) == 1
        assert game.spawn_timer == 0
    finally:
        random.choice = old_choice


def test_no_more_than_max_enemies(bare_game):
    for i in range(MAX_ENEMIES_ON_MAP):
        add_enemy(bare_game, x=60 + i * 100, y=300)
    bare_game.spawn_timer = SPAWN_DELAY
    bare_game.spawn_enemy()
    assert len(bare_game.enemies) == MAX_ENEMIES_ON_MAP


def test_no_spawn_when_level_quota_is_reached(bare_game):
    add_enemy(bare_game, x=300, y=300)
    bare_game.enemies_killed = ENEMIES_PER_LEVEL - 1
    bare_game.spawn_timer = SPAWN_DELAY
    bare_game.spawn_enemy()
    assert len(bare_game.enemies) == 1


def test_player_bullet_kills_enemy(bare_game):
    old_random = random.random
    random.random = lambda: 0.99

    try:
        enemy = add_enemy(bare_game)
        add_bullet(bare_game, enemy, "player")
        bare_game.update()
        assert len(bare_game.enemies) == 0
        assert bare_game.player.score == KILL_SCORE
        assert bare_game.enemies_killed == 1
        assert len(bare_game.bullets) == 0
        assert len(bare_game.bonuses) == 0
    finally:
        random.random = old_random


def test_bonus_drops_from_killed_enemy(bare_game):
    old_random = random.random
    random.random = lambda: 0.0

    try:
        enemy = add_enemy(bare_game)
        add_bullet(bare_game, enemy, "player")
        bare_game.update()
        assert len(bare_game.bonuses) == 1
    finally:
        random.random = old_random


def test_one_bullet_hits_only_one_enemy(bare_game):
    old_random = random.random
    random.random = lambda: 0.99

    try:
        first = add_enemy(bare_game, x=240)
        add_enemy(bare_game, x=244)
        add_bullet(bare_game, first, "player")
        bare_game.update()
        assert bare_game.enemies_killed == 1
    finally:
        random.random = old_random


def test_enemy_bullets_do_not_hurt_enemies(bare_game):
    enemy = add_enemy(bare_game)
    add_bullet(bare_game, enemy, "enemy")
    bare_game.update()
    assert enemy.hp == 1.0
    assert len(bare_game.bullets) == 1


@pytest.mark.parametrize("bullet_type, hp_after", [("normal", 2.0), ("weak", 2.5)])
def test_enemy_bullet_hurts_player(bullet_type, hp_after, bare_game):
    add_bullet(bare_game, bare_game.player, "enemy", bullet_type)
    bare_game.update()
    assert bare_game.player.hp == hp_after
    assert len(bare_game.bullets) == 0


def test_incendiary_bullet_sets_player_on_fire(bare_game):
    add_bullet(bare_game, bare_game.player, "enemy", "incendiary")
    bare_game.update()
    assert bare_game.player.burn_timer == 90


def test_shield_protects_player(bare_game):
    bare_game.player.invulnerable_timer = 100
    add_bullet(bare_game, bare_game.player, "enemy", "incendiary")
    bare_game.update()
    assert bare_game.player.hp == 3.0
    assert bare_game.player.burn_timer == 0
    assert len(bare_game.bullets) == 0


def test_player_bullet_does_not_hurt_player(bare_game):
    add_bullet(bare_game, bare_game.player, "player")
    bare_game.update()
    assert bare_game.player.hp == 3.0


def kill_with_bullet(game):
    game.player.hp = 1.0
    add_bullet(game, game.player, "enemy")
    game.update()


def test_death_costs_life_and_star_and_respawns(bare_game):
    p = bare_game.player
    p.stars = 2
    p.rect.x = 48
    kill_with_bullet(bare_game)
    assert (p.lives, p.hp, p.stars) == (2, p.max_hp, 1)
    assert p.rect.topleft == PLAYER_START_POS
    assert bare_game.state == "playing"


def test_stars_do_not_go_negative(bare_game):
    kill_with_bullet(bare_game)
    assert bare_game.player.stars == 0


def test_game_over_when_lives_run_out(bare_game):
    bare_game.player.lives = 0
    kill_with_bullet(bare_game)
    assert bare_game.state == "game_over"


def test_bonus_is_picked_up(bare_game):
    p = bare_game.player
    bonus = Bonus(p.rect.centerx, p.rect.centery)
    bonus.type = "life"
    bare_game.bonuses.add(bonus)
    bare_game.update()
    assert p.lives == 4
    assert len(bare_game.bonuses) == 0


def test_destroyed_blocks_disappear(bare_game):
    brick = Block(240, 240, TILE_BRICK)
    brick.hp = 1.0
    bare_game.all_blocks.add(brick)
    bare_game.bullets.add(Bullet(250, 260, "UP", "normal", "player", bare_game.all_blocks))
    bare_game.update()
    assert brick not in bare_game.all_blocks


def test_base_destroyed_means_game_over(game):
    for block in list(game.all_blocks):
        if block.type == TILE_BASE:
            block.kill()
    game.update()
    assert game.state == "game_over"


def test_next_level_after_all_enemies_killed(game):
    game.enemies_killed = ENEMIES_PER_LEVEL
    game.update()
    assert game.level_idx == 1


def test_level_does_not_end_while_enemies_alive(bare_game):
    bare_game.enemies_killed = ENEMIES_PER_LEVEL
    add_enemy(bare_game, x=300, y=300)
    bare_game.update()
    assert bare_game.level_idx == 0


def test_win_after_last_level(game):
    game.load_level(len(LEVELS) - 1)
    game.level_title_timer = 0
    game.enemies_killed = ENEMIES_PER_LEVEL
    game.update()
    assert game.state == "win"


def test_level_title_is_shown_after_loading_level(game):
    game.load_level(1)
    assert game.level_title_timer == 60


def test_update_does_nothing_while_title_is_shown(game):
    game.level_title_timer = 2
    game.update()
    game.update()
    assert game.level_title_timer == 0
    assert game.spawn_timer == 0
    game.update()
    assert game.spawn_timer == 1