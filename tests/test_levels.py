from src.levels import LEVELS
from src.settings import (
    PLAYER_START_POS,  TILE_SIZE, TileType, GRID_SIZE
)


def test_at_least_four_levels():
    assert len(LEVELS) >= 4


def test_matrix_size():
    for matrix in LEVELS:
        assert len(matrix) == GRID_SIZE
        for row in matrix:
            assert len(row) == GRID_SIZE


def test_only_known_tiles():
    for matrix in LEVELS:
        for row in matrix:
            assert all(TileType.EMPTY <= tile <= TileType.BORDER for tile in row)


def test_border_is_closed():
    last = GRID_SIZE - 1
    for matrix in LEVELS:
        for i in range(GRID_SIZE):
            assert matrix[0][i] == TileType.BORDER
            assert matrix[last][i] == TileType.BORDER
            assert matrix[i][0] == TileType.BORDER
            assert matrix[i][last] == TileType.BORDER


def test_every_level_has_two_base_blocks():
    for matrix in LEVELS:
        base_count = 0
        for row in matrix:
            base_count += row.count(TileType.BASE)
        assert base_count == 2


def test_player_start_is_free():
    col = PLAYER_START_POS[0] // TILE_SIZE
    row = PLAYER_START_POS[1] // TILE_SIZE
    for matrix in LEVELS:
        assert matrix[row][col] == TileType.EMPTY
