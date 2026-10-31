import random
import sys

import pygame
from src import savegame
from src.audio import AudioManager, configure_mixer

from src.settings import (
    BonusType, BulletType, SoundEvent, StrategyType, GameState, Team, TileType,
    BLACK, BONUS_DROP_CHANCE, ENEMIES_PER_LEVEL, ENEMY_SPAWN_COLS,
    FPS, GREEN, HEIGHT, KILL_SCORE, MAX_ENEMIES_ON_MAP, PLAYER_START_POS,
    RED, SPAWN_DELAY, TILE_SIZE, WHITE, WIDTH, YELLOW, FREEZE_FRAMES,
    SECRET_MENU_SEQUENCE, CHEAT_GOD_MODE_FRAMES, CHEAT_MAX_LIVES, CHEAT_FAST_SHOOT_DELAY
)

from src.levels import LEVELS
from src.sprites import Block, PlayerTank, EnemyTank, Bonus, ENEMY_STATS

ENEMY_TYPES = list(ENEMY_STATS.keys())
ENEMY_STRATEGIES = list(StrategyType)

LEVEL_KEYS = {pygame.K_1 + i: i for i in range(len(LEVELS))}
MESSAGE_FRAMES = 120


class Game:
    """Класс, реализующий игровой движок"""
    def __init__(self, sound=True):
        configure_mixer()
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Battle City")
        self.clock = pygame.time.Clock()
        self.font_ui = pygame.font.SysFont("Courier New", 18, bold=True)
        self.font_big = pygame.font.SysFont("Courier New", 44, bold=True)
        self.is_neon_active = False
        self.menu_keys_pressed = []

        self.all_blocks = pygame.sprite.Group()
        self.bushes = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bonuses = pygame.sprite.Group()

        self.state = GameState.MENU
        self.level_title_timer = 0
        self.message = ""
        self.message_timer = 0
        self.freeze_timer = 0
        self.audio = AudioManager(enabled=sound)
        self.start_new_game()

    def make_neon_color(self, color, activate=False):
        """Пасхалка"""
        if not activate:
            return color
        r, g, b = color
        return (r, b, g) if r > 0 else (g, r, 255)

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
        self.freeze_timer = 0

        for group in (self.all_blocks, self.bushes, self.bullets, self.enemies, self.bonuses):
            group.empty()

        for row_idx, row in enumerate(LEVELS[level_idx]):
            for col_idx, tile in enumerate(row):
                if tile == TileType.EMPTY:
                    continue
                block = Block(col_idx * TILE_SIZE, row_idx * TILE_SIZE, tile)
                block.update_appearance(neon_active=self.is_neon_active)

                if tile == TileType.BUSH:
                    self.bushes.add(block)
                else:
                    self.all_blocks.add(block)

        self.player.rect.topleft = PLAYER_START_POS
        if self.state == GameState.PLAYING:
            self.audio.play(SoundEvent.LEVEL_START)


    def set_state(self, state):
        """Меняет состояние игры и включает, ставит на паузу или останавливает музыку"""
        previous = self.state
        self.state = state
        match state:
            case GameState.PLAYING if previous == GameState.PAUSED:
                self.audio.resume_music()
            case GameState.PLAYING:
                self.audio.start_music()
                self.audio.play(SoundEvent.LEVEL_START)
            case GameState.PAUSED:
                self.audio.pause_music()
                self.audio.play(SoundEvent.PAUSE)
            case GameState.GAME_OVER:
                self.audio.stop_music()
                self.audio.play(SoundEvent.GAME_OVER)
            case GameState.WIN:
                self.audio.stop_music()
                self.audio.play(SoundEvent.WIN)
            case GameState.MENU:
                self.audio.stop_music()


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
            case(_, pygame.K_m):
                self.toggle_mute()
            case (GameState.MENU, pygame.K_RETURN):
                self.load_level(0)
                self.state = GameState.PLAYING
            case (GameState.MENU, pygame.K_F9):
                self.load_game()
            case (GameState.MENU, _):
                self.menu_keys_pressed.append(key)
                if len(self.menu_keys_pressed) > len(SECRET_MENU_SEQUENCE):
                    self.menu_keys_pressed.pop(0)
                if self.menu_keys_pressed == SECRET_MENU_SEQUENCE:
                    self.is_neon_active = True
                    self.player.is_neon = True
                    print("[Пасхалка]: Время неона!")
            case (GameState.PLAYING, pygame.K_p):
                self.state = GameState.PAUSED
            case (GameState.PAUSED, pygame.K_p):
                self.state = GameState.PLAYING
            case (GameState.PLAYING | GameState.PAUSED, pygame.K_F5):
                self.save_game()
            case (GameState.PLAYING | GameState.PAUSED, pygame.K_F9):
                self.load_game()
            case (GameState.PLAYING, pygame.K_k):
                for enemy in list(self.enemies):
                    enemy.hp = 0.0
                print("[Чит] Все вражеские танки на карте уничтожены!")
            case (GameState.PLAYING, pygame.K_g):
                self.player.invulnerable_timer = CHEAT_GOD_MODE_FRAMES
                print("[Чит] Игрок получил абсолютную неуязвимость!")
            case (GameState.PLAYING, pygame.K_l):
                self.player.lives = CHEAT_MAX_LIVES
                print(f"[Чит] Счетчик жизней установлен на {CHEAT_MAX_LIVES}!")
            case (GameState.PLAYING, pygame.K_f):
                self.player.shoot_delay = CHEAT_FAST_SHOOT_DELAY
                self.player.bullet_type = BulletType.SNIPER
                print("[Чит] Активирован режим пулемета!")
            case (GameState.PLAYING, _) if key in LEVEL_KEYS:
                self.load_level(LEVEL_KEYS[key])
            case (GameState.GAME_OVER | GameState.WIN, pygame.K_r):
                self.start_new_game()
                self.state = GameState.PLAYING

    def toggle_mute(self):
        """Включает или выключает звук"""
        if not self.audio.available:
            self.show_message("Звук недоступен")
        elif self.audio.toggle_mute():
            self.show_message("Звук выключен")
        else:
            self.show_message("Звук включён")


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
                            self.kill_enemy(enemy)
                case Team.ENEMY if bullet.rect.colliderect(self.player.rect):
                    bullet.kill()
                    if self.player.invulnerable_timer == 0:
                        self.player.hp -= bullet.damage
                        self.audio.play(SoundEvent.PLAYER_HIT)
                        if bullet.type == BulletType.INCENDIARY:
                            self.player.burn_timer = 90


    def kill_enemy(self, enemy, drop_bonus=True):
        """Уничтожение врага"""
        enemy.kill()
        self.player.score += KILL_SCORE
        self.enemies_killed += 1
        self.audio.play(SoundEvent.EXPLOSION)
        if drop_bonus and random.random() < BONUS_DROP_CHANCE:
            self.bonuses.add(Bonus(enemy.rect.centerx, enemy.rect.centery))


    def kill_player(self):
        """Обработка смерти игрока"""
        p = self.player
        p.lives -= 1
        p.hp = p.max_hp
        p.stars = max(0, p.stars - 1)
        p.burn_timer = 0
        p.rect.topleft = PLAYER_START_POS
        self.audio.play(SoundEvent.PLAYER_HIT)
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
        shots = len(self.bullets)
        self.player.update(keys, self.bullets, self.enemies)
        if len(self.bullets) > shots:
            self.audio.play(SoundEvent.SHOT)
        self.update_enemies()

        bullets_before = len(self.bullets)
        self.bullets.update()
        if len(self.bullets) < bullets_before:
            self.audio.play(SoundEvent.HIT)
        self.check_bullets()
        self.check_mines()

        for bonus in pygame.sprite.spritecollide(self.player, self.bonuses, True):
            bonus.apply(self.player)
            self.apply_world_bonus(bonus.type)
            self.audio.play(SoundEvent.BONUS)

        if self.player.hp <= 0:
            self.kill_player()

        self.check_win_lose()

    def update_enemies(self):
        """Враги двигаются и стреляют, если их не заморозили"""
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            return
        shots = len(self.bullets)
        self.enemies.update(self.player, self.bullets, self.enemies)
        if len(self.bullets) > shots:
            self.audio.play(SoundEvent.ENEMY_SHOT)

    def check_mines(self):
        """Звук взрыва мины и гибель врагов, подорвавшихся на мине"""
        for tank in (self.player, *self.enemies):
            if tank.mine_hit:
                tank.mine_hit = False
                self.audio.play(SoundEvent.MINE)
        for enemy in list(self.enemies):
            if enemy.hp <= 0:
                self.kill_enemy(enemy)

    def apply_world_bonus(self, bonus_type):
        """Бонусы, которые действуют на всех врагов сразу"""
        match bonus_type:
            case BonusType.BOMB:
                for enemy in list(self.enemies):
                    self.kill_enemy(enemy, drop_bonus=False)
            case BonusType.FREEZE:
                self.freeze_timer = FREEZE_FRAMES

    def draw_text_center(self, font, text, color, y):
        """Отрисовка текста с центрированием"""
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, y))
        self.screen.blit(surf, rect)
        return rect

    def draw_menu(self):
        """Отрисовка главного меню"""
        title_color = self.make_neon_color(YELLOW, self.is_neon_active)
        text_color = self.make_neon_color(WHITE, self.is_neon_active)
        self.draw_text_center(self.font_big, "BATTLE CITY", title_color, HEIGHT // 3)
        self.draw_text_center(self.font_ui, "Нажмите ENTER для старта", text_color, HEIGHT // 2 + 40)
        if savegame.save_exists():
            self.draw_text_center(self.font_ui, "F9 - продолжить сохранённую игру", text_color,
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
            self.audio.play(SoundEvent.SAVE)
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