import random
import sys

import pygame
from src import savegame

from src.settings import (
    BulletType, StrategyType, GameState, Team, TileType,
    BLACK, BONUS_DROP_CHANCE, ENEMIES_PER_LEVEL, ENEMY_SPAWN_COLS,
    FPS, GREEN, HEIGHT, KILL_SCORE, MAX_ENEMIES_ON_MAP, PLAYER_START_POS,
    RED, SPAWN_DELAY, TILE_SIZE, WHITE, WIDTH, YELLOW
)

from src.levels import LEVELS
from src.sprites import Block, PlayerTank, EnemyTank, Bonus, ENEMY_STATS

ENEMY_TYPES = list(ENEMY_STATS.keys())
ENEMY_STRATEGIES = list(StrategyType)

LEVEL_KEYS = {pygame.K_1 + i: i for i in range(len(LEVELS))}
MESSAGE_FRAMES = 120


class Game:
    """Класс, реализующий игровой движок"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Battle City")
        self.clock = pygame.time.Clock()
        self.font_ui = pygame.font.SysFont("Courier New", 18, bold=True)
        self.font_big = pygame.font.SysFont("Courier New", 44, bold=True)

        self.all_blocks = pygame.sprite.Group()
        self.bushes = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bonuses = pygame.sprite.Group()

        self.state = GameState.MENU
        self.level_title_timer = 0
        self.message = ""
        self.message_timer = 0
        self.start_new_game()

    def start_new_game(self):
        """Сброс прогресса и начало новой игры"""
        self.player = PlayerTank(*PLAYER_START_POS, self.all_blocks)
        self.load_level(0)

    def load_level(self, level_idx):
        """Очищает карту и строит уровень"""
        self.level_idx = level_idx
        self.enemies_killed = 0
        self.spawn_timer = 0
        self.level_title_timer = 60

        for group in (self.all_blocks, self.bushes, self.bullets, self.enemies, self.bonuses):
            group.empty()

        for row_idx, row in enumerate(LEVELS[level_idx]):
            for col_idx, tile in enumerate(row):
                if tile == TileType.EMPTY:
                    continue
                block = Block(col_idx * TILE_SIZE, row_idx * TILE_SIZE, tile)
                if tile == TileType.BUSH:
                    self.bushes.add(block)
                else:
                    self.all_blocks.add(block)

        self.player.rect.topleft = PLAYER_START_POS

    def handle_events(self):
        """Считывание системных событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)

    def handle_keydown(self, key):
        """Реакция на нажатие клавиши зависит от состояния игры"""
        match (self.state, key):
            case (GameState.MENU, pygame.K_RETURN):
                self.state = GameState.PLAYING
            case (GameState.MENU, pygame.K_F9):
                self.load_game()
            case (GameState.PLAYING, pygame.K_p):
                self.state = GameState.PAUSED
            case (GameState.PAUSED, pygame.K_p):
                self.state = GameState.PLAYING
            case (GameState.PLAYING | GameState.PAUSED, pygame.K_F5):
                self.save_game()
            case (GameState.PLAYING | GameState.PAUSED, pygame.K_F9):
                self.load_game()
            case (GameState.PLAYING, _) if key in LEVEL_KEYS:
                self.load_level(LEVEL_KEYS[key])
            case (GameState.GAME_OVER | GameState.WIN, pygame.K_r):
                self.start_new_game()
                self.state = GameState.PLAYING


    def spawn_enemy(self):
        """Создаёт врага, если на карте есть место"""
        self.spawn_timer += 1
        total = self.enemies_killed + len(self.enemies)
        if (self.spawn_timer <= SPAWN_DELAY
                or len(self.enemies) >= MAX_ENEMIES_ON_MAP
                or total >= ENEMIES_PER_LEVEL):
            return
        self.spawn_timer = 0

        x = random.choice(ENEMY_SPAWN_COLS) * TILE_SIZE
        enemy = EnemyTank(x, TILE_SIZE, self.all_blocks,
                          random.choice(ENEMY_TYPES), random.choice(ENEMY_STRATEGIES))

        if (not pygame.sprite.spritecollideany(enemy, self.enemies)
                and not enemy.rect.colliderect(self.player.rect)):
            self.enemies.add(enemy)

    def check_bullets(self):
        """Расчет коллизий пуль, триггер выпадения бонусов"""
        for bullet in list(self.bullets):
            match bullet.owner_team:
                case Team.PLAYER:
                    enemy = pygame.sprite.spritecollideany(bullet, self.enemies)
                    if enemy:
                        bullet.kill()
                        enemy.hp -= bullet.damage
                        if enemy.hp <= 0:
                            enemy.kill()
                            self.player.score += KILL_SCORE
                            self.enemies_killed += 1
                            if random.random() < BONUS_DROP_CHANCE:
                                self.bonuses.add(Bonus(enemy.rect.centerx, enemy.rect.centery))
                case Team.ENEMY if bullet.rect.colliderect(self.player.rect):
                    bullet.kill()
                    if self.player.invulnerable_timer == 0:
                        self.player.hp -= bullet.damage
                        if bullet.type == BulletType.INCENDIARY:
                            self.player.burn_timer = 90

    def kill_player(self):
        """Обработка смерти игрока"""
        p = self.player
        p.lives -= 1
        p.hp = p.max_hp
        p.stars = max(0, p.stars - 1)
        p.burn_timer = 0
        p.rect.topleft = PLAYER_START_POS
        if p.lives < 0:
            self.state = GameState.GAME_OVER

    def check_win_lose(self):
        """Проверка на поражение или победу"""
        if self.state != GameState.PLAYING:
            return
        base_alive = any(b.type == TileType.BASE for b in self.all_blocks)
        if not base_alive:
            self.state = GameState.GAME_OVER
        elif self.enemies_killed >= ENEMIES_PER_LEVEL and len(self.enemies) == 0:
            if self.level_idx + 1 < len(LEVELS):
                self.load_level(self.level_idx + 1)
            else:
                self.state = GameState.WIN

    def update(self):
        """Обновление состояния всех сущностей"""
        if self.level_title_timer > 0:
            self.level_title_timer -= 1
            return

        keys = pygame.key.get_pressed()

        self.spawn_enemy()
        self.player.update(keys, self.bullets, self.enemies)
        self.enemies.update(self.player, self.bullets, self.enemies)
        self.bullets.update()
        self.check_bullets()

        for bonus in pygame.sprite.spritecollide(self.player, self.bonuses, True):
            bonus.apply(self.player)

        if self.player.hp <= 0:
            self.kill_player()

        self.check_win_lose()

    def draw_text_center(self, font, text, color, y):
        """Отрисовка текста с центрированием"""
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, y))
        self.screen.blit(surf, rect)
        return rect

    def draw_menu(self):
        """Отрисовка главного меню"""
        self.draw_text_center(self.font_big, "BATTLE CITY", YELLOW, HEIGHT // 3)
        self.draw_text_center(self.font_ui, "Нажмите ENTER для старта", WHITE, HEIGHT // 2 + 40)
        if savegame.save_exists():
            self.draw_text_center(self.font_ui, "F9 - продолжить сохранённую игру", WHITE,
                                  HEIGHT // 2 + 70)

    def draw_game(self):
        """Отрисовка игровых объектов"""
        if self.level_title_timer > 0:
            title = f"УРОВЕНЬ {self.level_idx + 1}"
            self.draw_text_center(self.font_big, title, WHITE, HEIGHT // 2)
            return

        self.all_blocks.draw(self.screen)
        self.bonuses.draw(self.screen)
        if self.state != GameState.GAME_OVER:
            self.screen.blit(self.player.image, self.player.rect)
        self.enemies.draw(self.screen)
        self.bullets.draw(self.screen)
        self.bushes.draw(self.screen)

        enemies_left = max(0, ENEMIES_PER_LEVEL - self.enemies_killed)
        info = (f"Счёт: {self.player.score} | Жизни: {max(0, self.player.lives)} | "
                f"Звёзды: {self.player.stars} | Враги: {enemies_left} | Лвл: {self.level_idx + 1}")
        self.screen.blit(self.font_ui.render(info, True, WHITE), (10, 5))

        match self.state:
            case GameState.GAME_OVER:
                self.draw_banner("ИГРА ОКОНЧЕНА", RED, "R - играть заново")
            case GameState.WIN:
                self.draw_banner("ПОБЕДА!", GREEN, "R - играть заново")
            case GameState.PAUSED:
                self.draw_banner("ПАУЗА", WHITE, "P - продолжить, F5 - сохранить, F9 - загрузить")

    def draw_banner(self, text, color, hint):
        """Надпись по центру и подсказка под ней"""
        box = self.font_big.render(text, True, color).get_rect(center=(WIDTH // 2, HEIGHT // 2))
        pygame.draw.rect(self.screen, BLACK, box.inflate(24, 12))
        self.draw_text_center(self.font_big, text, color, HEIGHT // 2)
        self.draw_text_center(self.font_ui, hint, WHITE, HEIGHT // 2 + 50)

    def show_message(self, text):
        """Сообщение внизу экрана"""
        self.message = text
        self.message_timer = MESSAGE_FRAMES


    def save_game(self):
        """Сохранение прогресса"""
        try:
            savegame.save_to_file(self)
            self.show_message("Игра сохранена")
        except savegame.SaveError as err:
            self.show_message(str(err))

    def load_game(self):
        """Загрузка прогресса"""
        try:
            savegame.load_from_file(self)
            self.show_message("Игра загружена")
        except savegame.SaveError as err:
            self.show_message(str(err))

    def draw(self):
        """Очитска экрана и вызов рендеров"""
        self.screen.fill(BLACK)
        if self.state == GameState.MENU:
            self.draw_menu()
        else:
            self.draw_game()
        if self.message_timer > 0:
            self.draw_text_center(self.font_ui, self.message, YELLOW, HEIGHT - 20)
        pygame.display.flip()

    def run(self):
        """Запуск игры"""
        while True:
            self.clock.tick(FPS)
            self.handle_events()
            if self.state == GameState.PLAYING:
                self.update()
            if self.message_timer > 0:
                self.message_timer -= 1
            self.draw()