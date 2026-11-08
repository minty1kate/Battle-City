import json

import pygame
import pytest

from src.editor import LevelEditor
from src.settings import ENEMY_SPAWN_COLS, TILE_SIZE, TileType


@pytest.fixture
def editor(tmp_path):
    pygame.init()
    screen = pygame.Surface((624, 624))
    font = pygame.font.Font(None, 18)
    result = LevelEditor(screen, font, tmp_path / "level.json")
    yield result
    pygame.quit()


def test_reset_creates_closed_map_with_base(editor):
    assert len(editor.tiles) == 26
    assert all(len(row) == 26 for row in editor.tiles)
    assert sum(row.count(TileType.BASE) for row in editor.tiles) == 2
    assert editor.selected == TileType.BRICK


def test_select_tile_by_number(editor):
    for key, tile in enumerate(editor.TILES, start=pygame.K_1):
        assert editor.handle_key(key) is None
        assert editor.selected == tile


@pytest.mark.parametrize("key, expected", [
    (pygame.K_ESCAPE, "menu"), (pygame.K_s, "saved"), (pygame.K_RETURN, "play")
])
def test_editor_keyboard_actions(editor, key, expected, monkeypatch):
    monkeypatch.setattr(editor, "save", lambda: True)
    assert editor.handle_key(key) == expected


@pytest.mark.parametrize("key", [pygame.K_s, pygame.K_RETURN])
def test_editor_keyboard_reports_save_error(editor, key, monkeypatch):
    monkeypatch.setattr(editor, "save", lambda: False)
    assert editor.handle_key(key) == "save_error"


def test_unknown_key_does_nothing(editor):
    before = editor.selected
    assert editor.handle_key(pygame.K_z) is None
    assert editor.selected == before


def test_left_click_places_selected_tile(editor):
    editor.selected = TileType.MUD
    editor.handle_click((5 * TILE_SIZE + 1, 5 * TILE_SIZE + 1), 1)
    assert editor.tiles[5][5] == TileType.MUD


def test_right_click_erases_tile(editor):
    editor.tiles[5][5] = TileType.BRICK
    editor.handle_click((5 * TILE_SIZE, 5 * TILE_SIZE), 3)
    assert editor.tiles[5][5] == TileType.EMPTY


@pytest.mark.parametrize("position", [
    (0, 5 * TILE_SIZE), (25 * TILE_SIZE, 5 * TILE_SIZE),
    (5 * TILE_SIZE, 0), (5 * TILE_SIZE, 25 * TILE_SIZE),
])
def test_click_does_not_modify_border(editor, position):
    before = [row[:] for row in editor.tiles]
    editor.handle_click(position, 1)
    assert editor.tiles == before


def test_click_cannot_replace_base_or_player_spawn(editor):
    editor.handle_click((12 * TILE_SIZE, 24 * TILE_SIZE), 1)
    editor.handle_click((2 * TILE_SIZE, 24 * TILE_SIZE), 1)
    assert editor.tiles[24][12] == TileType.BASE
    assert editor.tiles[24][2] == TileType.EMPTY


@pytest.mark.parametrize("col", ENEMY_SPAWN_COLS)
def test_click_cannot_block_enemy_spawn(editor, col):
    editor.handle_click((col * TILE_SIZE, TILE_SIZE), 1)
    assert editor.tiles[1][col] == TileType.EMPTY


def test_save_and_load_round_trip(editor):
    editor.tiles[8][8] = TileType.ICE
    assert editor.save()
    assert editor.has_saved_level
    assert editor.load_saved_level() == editor.tiles


def test_load_rejects_wrong_matrix_size(editor):
    editor.path.write_text(json.dumps({"tiles": [[0]]}), encoding="utf-8")
    with pytest.raises(ValueError, match="размер"):
        editor.load_saved_level()


def test_load_rejects_unknown_tile(editor):
    matrix = [[0] * 26 for _ in range(26)]
    matrix[4][4] = 100
    editor.path.write_text(json.dumps({"tiles": matrix}), encoding="utf-8")
    with pytest.raises(ValueError):
        editor.load_saved_level()


def test_open_resets_when_saved_file_is_invalid(editor):
    editor.tiles[5][5] = TileType.MUD
    editor.path.write_text("{broken", encoding="utf-8")
    editor.open()
    assert editor.tiles[5][5] == TileType.EMPTY


def test_draw_renders_map(editor):
    editor.draw(neon_active=True)
    assert editor.screen.get_at((0, 0))[:3] == (0, 0, 0)
