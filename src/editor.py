import json
from pathlib import Path
import pygame
from src.levels import get_empty_matrix, add_base, add_border
from src.settings import (
    BLACK, ENEMY_SPAWN_COLS, GREEN, HEIGHT, TILE_SIZE, WHITE, WIDTH, YELLOW,
    TileType,
)
from src.sprites import Block

class LevelEditor:
    """Простой редактор уровней"""
    TILES = (
        TileType.BRICK, TileType.CONCRETE, TileType.WATER, TileType.ICE,
        TileType.BUSH, TileType.MUD, TileType.MINE,
    )

    def __init__(self, screen, font_ui, path=Path("custom_level.json")):
        self.screen = screen
        self.font_ui = font_ui
        self.path = Path(path)
        self.tiles = []
        self.selected = TileType.BRICK
        self.reset()

    @property
    def has_saved_level(self):
        return self.path.is_file()

    def reset(self):
        """Создает пустую карту с базой и границей"""
        self.tiles = get_empty_matrix()
        add_base(self.tiles)
        add_border(self.tiles)
        self.selected = TileType.BRICK

    def open(self):
        """Открывает редактор и загружает карту, если она есть"""
        self.reset()
        if self.has_saved_level:
            try:
                self.tiles = self.load_saved_level()
            except (OSError, ValueError, TypeError, KeyError):
                pass

    def handle_key(self, key):
        """Обрабатывает клавиши"""
        if key == pygame.K_ESCAPE:
            return "menu"
        if key == pygame.K_s:
            return "saved" if self.save() else "save_error"
        if key == pygame.K_RETURN:
            return "play" if self.save() else "save_error"
        if pygame.K_1 <= key <= pygame.K_7:
                self.selected = self.TILES[key - pygame.K_1]
        return None

    def handle_click(self, position, button):
        """Ставит выбранную клетку или стирает её"""
        col, row = position[0] // TILE_SIZE, position[1] // TILE_SIZE
        if not (1 <= row < len(self.tiles) - 1 and
                1 <= col < len(self.tiles[row]) - 1):
            return
        if self.tiles[row][col] == TileType.BASE:
            return
        if (row, col) == (24, 2) or (row == 1 and col in ENEMY_SPAWN_COLS):
            return
        if button == 1:
            self.tiles[row][col] = self.selected
        elif button == 3:
            self.tiles[row][col] = TileType.EMPTY

    def save(self):
        """Сохраняет карту"""
        try:
            data = {"tiles": [[int(tile) for tile in row] for row in self.tiles]}
            self.path.write_text(json.dumps(data), encoding="utf-8")
            return True
        except OSError:
            return False

    def load_saved_level(self):
        """Загружает сохранённую карту"""
        data = json.loads(self.path.read_text(encoding="utf-8"))
        rows = data["tiles"]
        if len(rows) != 26 or any(len(row) != 26 for row in rows):
            raise ValueError("Неверный размер карты")
        return [[TileType(value) for value in row] for row in rows]

    def draw(self, neon_active=False):
        """Отрисовывает поле редактора"""
        self.screen.fill(BLACK)
        for row_idx, row in enumerate(self.tiles):
            for col_idx, tile in enumerate(row):
                if tile != TileType.EMPTY:
                    block = Block(col_idx * TILE_SIZE, row_idx * TILE_SIZE, tile)
                    block.update_appearance(neon_active=neon_active)
                    self.screen.blit(block.image, block.rect)
                else:
                    pygame.draw.rect(
                        self.screen, (35, 35, 35),
                        (col_idx * TILE_SIZE, row_idx * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1
                    )

        panel = pygame.Surface((WIDTH, 92), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 220))
        self.screen.blit(panel, (0, 0))
        labels = [
            f"Выбрано: {self.selected.name} | 1 Кирпич  2 Бетон  3 Вода  4 Лёд",
            "5 Кусты   6 Грязь  7 Мины",
            "ЛКМ: поставить | ПКМ: стереть",
            "S: сохранить | ENTER: сохранить и играть | ESC: меню",
        ]
        for index, label in enumerate(labels):
            color = YELLOW if index == 0 else WHITE
            self.screen.blit(self.font_ui.render(label, True, color), (8, 5 + index * 21))
