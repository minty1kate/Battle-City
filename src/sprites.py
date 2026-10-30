import math
import random
from typing import NamedTuple

import pygame
from src.settings import (
    TILE_SIZE, WIDTH, HEIGHT, BLACK, WHITE, RED, GREEN, BLUE, YELLOW, GREY, BROWN, CYAN,
    BONUS_COLORS, TileType, Team, BulletType, EnemyType, StrategyType, Direction, BonusType
)

SCREEN_RECT = pygame.Rect(0, 0, WIDTH, HEIGHT)

ROTATION = {Direction.UP: 0, Direction.LEFT: 90, Direction.DOWN: 180, Direction.RIGHT: 270}

MOVE_KEYS = {
    Direction.UP: (pygame.K_UP, pygame.K_w),
    Direction.DOWN: (pygame.K_DOWN, pygame.K_s),
    Direction.LEFT: (pygame.K_LEFT, pygame.K_a),
    Direction.RIGHT: (pygame.K_RIGHT, pygame.K_d),
}

BULLET_STOPPERS = [TileType.BRICK, TileType.CONCRETE, TileType.BASE]

BULLET_SIZE = 4
BULLET_SPEED = {
    BulletType.NORMAL: 6,
    BulletType.WEAK: 3,
    BulletType.CONCRETE_BREAKER: 9,
    BulletType.INCENDIARY: 6,
}
BULLET_COLOR = {
    BulletType.NORMAL: WHITE,
    BulletType.WEAK: WHITE,
    BulletType.CONCRETE_BREAKER: RED,
    BulletType.INCENDIARY: YELLOW,
}
BULLET_DAMAGE = {
    BulletType.NORMAL: 1.0,
    BulletType.WEAK: 0.5,
    BulletType.CONCRETE_BREAKER: 1.0,
    BulletType.INCENDIARY: 1.0,
}


class EnemyStats(NamedTuple):
    """Характеристики вражеского танка"""
    speed: int
    hp: float
    bullet: BulletType
    color: tuple
    shoot_delay: int


ENEMY_STATS = {
    EnemyType.SIMPLE: EnemyStats(2, 1.0, BulletType.WEAK, RED, 40),
    EnemyType.FAST: EnemyStats(4, 1.0, BulletType.NORMAL, YELLOW, 40),
    EnemyType.SHOOTER: EnemyStats(2, 2.0, BulletType.CONCRETE_BREAKER, CYAN, 20),
    EnemyType.ARMORED: EnemyStats(1, 4.0, BulletType.INCENDIARY, BROWN, 40),
}


def align(value):
    """Выравнивает координату по сетке клеток"""
    return round(value / TILE_SIZE) * TILE_SIZE


class Block(pygame.sprite.Sprite):
    """Класс блоков"""
    def __init__(self, x, y, tile_type):
        super().__init__()
        self.type = tile_type
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hp = 4.0 if tile_type == TileType.BRICK else 1.0
        self.update_appearance()

    def update_appearance(self):
        """Создает внешний вид блока"""
        sz = TILE_SIZE

        match self.type:
            case TileType.BRICK:
                self.image.fill(BROWN)
                for y in range(0, sz, 6):
                    pygame.draw.line(self.image, BLACK, (0, y), (sz, y), 1)
                    offset = 4 if (y // 6) % 2 == 0 else 0
                    for x in range(offset, sz, 8):
                        pygame.draw.line(self.image, BLACK, (x, y), (x, y + 6), 1)
                pygame.draw.rect(self.image, BLACK, (0, 0, sz, sz), 1)
            case TileType.CONCRETE:
                self.image.fill(GREY)
                pygame.draw.rect(self.image, WHITE, (0, 0, sz, sz), 1)
            case TileType.WATER:
                self.image.fill(BLUE)
                for y in range(4, sz, 8):
                    pygame.draw.arc(self.image, (100, 150, 255), (2, y, sz // 2, 6), 0, math.pi, 1)
                    pygame.draw.arc(self.image, (100, 150, 255),
                                    (sz // 2, y + 2, sz // 2, 6), 0, math.pi, 1)
            case TileType.ICE:
                self.image.fill(CYAN)
                pygame.draw.line(self.image, WHITE, (2, 2), (sz - 4, sz - 4), 1)
                pygame.draw.line(self.image, WHITE, (sz - 6, 4), (sz - 12, 10), 1)
                pygame.draw.line(self.image, WHITE, (4, sz - 8), (10, sz - 14), 1)
                pygame.draw.rect(self.image, (100, 240, 240), (0, 0, sz, sz), 1)
            case TileType.BUSH:
                self.image.fill((10, 80, 10))
                light_green = (110, 210, 10)
                half = sz // 2
                pygame.draw.rect(self.image, light_green, (2, 2, half - 4, half - 4))
                pygame.draw.rect(self.image, light_green, (half + 2, half + 2, half - 4, half - 4))
                pygame.draw.rect(self.image, BLACK, (half // 2, half // 2, 3, 3))
                pygame.draw.rect(self.image, BLACK, (half + half // 2, half + half // 2, 3, 3))
                pygame.draw.rect(self.image, light_green, (half + 4, 4, 3, 3))
                pygame.draw.rect(self.image, light_green, (4, half + 4, 3, 3))
            case TileType.BASE:
                self.image.fill(YELLOW)
                pygame.draw.circle(self.image, RED, (sz // 2, sz // 2), sz // 3)
            case TileType.BORDER:
                self.image.fill(BLACK)

    def take_damage(self, bullet_type, owner_stats=0):
        """Получение урона"""
        match self.type:
            case TileType.BRICK:
                damage = 2.0 if owner_stats >= 3 else 1.0
                if bullet_type == BulletType.WEAK:
                    damage = 0.5
                self.hp -= damage
                if self.hp <= 0:
                    self.kill()
            case TileType.CONCRETE:
                if owner_stats >= 3 or bullet_type == BulletType.CONCRETE_BREAKER:
                    self.kill()
            case TileType.BASE:
                self.kill()


class Bullet(pygame.sprite.Sprite):
    """Класс пуль"""
    def __init__(self, x, y, direction, bullet_type, owner_team, all_blocks, owner_stats=0):
        super().__init__()
        self.direction = direction
        self.type = bullet_type
        self.owner_team = owner_team
        self.all_blocks = all_blocks
        self.owner_stats = owner_stats
        self.speed = BULLET_SPEED[bullet_type]
        if owner_stats >= 1:
            self.speed += 3
        self.damage = BULLET_DAMAGE[bullet_type]

        self.image = pygame.Surface((BULLET_SIZE, BULLET_SIZE))
        self.image.fill(BULLET_COLOR[bullet_type])
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        """Поведение пули на карте"""
        dx, dy = self.direction.value
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed

        if not SCREEN_RECT.colliderect(self.rect):
            self.kill()
            return

        for block in pygame.sprite.spritecollide(self, self.all_blocks, False):
            if block.type in BULLET_STOPPERS:
                block.take_damage(self.type, self.owner_stats)
                self.kill()
                return


class Tank(pygame.sprite.Sprite):
    """Класс танков"""
    def __init__(self, x, y, all_blocks):
        super().__init__()
        self.all_blocks = all_blocks
        self.image = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.last_look = None

        self.direction = Direction.UP
        self.speed = 2
        self.hp = 1.0
        self.max_hp = 1.0
        self.cooldown = 0
        self.shoot_delay = 40

        self.is_sliding = False
        self.burn_timer = 0
        self.invulnerable_timer = 0

    def handle_effects(self):
        """Влияние эффектов"""
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.burn_timer > 0:
            self.burn_timer -= 1
            if self.burn_timer % 30 == 0 and self.invulnerable_timer == 0:
                self.hp -= 0.25
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

    def check_tile_collisions(self, old_x, old_y, other_tanks=()):
        """Возвращает True, если танк упёрся в стену"""
        self.is_sliding = False
        for block in pygame.sprite.spritecollide(self, self.all_blocks, False):
            match block.type:
                case TileType.ICE:
                    self.is_sliding = True
                case TileType.BRICK | TileType.CONCRETE | TileType.WATER | TileType.BORDER:
                    self.rect.x = old_x
                    self.rect.y = old_y
                    return True

        old_rect = pygame.Rect(old_x, old_y, self.rect.width, self.rect.height)
        for tank in other_tanks:
            if tank is self:
                continue

            if self.rect.colliderect(tank.rect) and not old_rect.colliderect(tank.rect):
                self.rect.x = old_x
                self.rect.y = old_y
                return True

        return False

    def shoot(self, bullet_group, bullet_type, team, stars=0):
        """Стрельба"""
        bullet = Bullet(self.rect.centerx, self.rect.centery, self.direction,
                        bullet_type, team, self.all_blocks, stars)
        bullet_group.add(bullet)
        self.cooldown = self.shoot_delay

    def update_image(self, color):
        """Рисует танк"""
        if self.last_look == (self.direction, color):
            return
        self.last_look = (self.direction, color)

        w, h = self.rect.size
        track_w = 6
        track_color = (60, 80, 90)
        hatch_color = tuple(min(255, c + 40) for c in color)

        base = pygame.Surface((w, h))
        base.fill(BLACK)

        pygame.draw.rect(base, track_color, (0, 0, track_w, h))
        pygame.draw.rect(base, track_color, (w - track_w, 0, track_w, h))
        for y in range(0, h, 4):
            pygame.draw.rect(base, BLACK, (0, y, track_w, 2))
            pygame.draw.rect(base, BLACK, (w - track_w, y, track_w, 2))

        pygame.draw.rect(base, color, (track_w, 2, w - track_w * 2, h - 4))
        pygame.draw.rect(base, hatch_color, (track_w + 2, h // 2 - 4, w - track_w * 2 - 4, 8))
        pygame.draw.rect(base, WHITE, (w // 2 - 2, 0, 4, h // 2))

        self.image = pygame.transform.rotate(base, ROTATION[self.direction])


class PlayerTank(Tank):
    """Класс танка игрока"""
    def __init__(self, x, y, all_blocks):
        super().__init__(x, y, all_blocks)
        self.hp = 3.0
        self.max_hp = 3.0
        self.lives = 3
        self.speed = 3
        self.bullet_type = BulletType.NORMAL
        self.score = 0
        self.stars = 0

    def update(self, keys, bullet_group, enemy_group):
        """Поведение танка на карте, движение, стрельба"""
        self.handle_effects()
        old_x, old_y = self.rect.x, self.rect.y
        moved = False

        pressed = None
        for direction, (key1, key2) in MOVE_KEYS.items():
            if keys[key1] or keys[key2]:
                pressed = direction
                break

        if pressed:
            speed = self.speed + 2 if self.is_sliding else self.speed
            match (pressed, self.direction):
                case (Direction.UP | Direction.DOWN, Direction.LEFT | Direction.RIGHT):
                    self.rect.x = align(self.rect.x)
                case (Direction.LEFT | Direction.RIGHT, Direction.UP | Direction.DOWN):
                    self.rect.y = align(self.rect.y)
            self.direction = pressed
            dx, dy = pressed.value
            self.rect.x += dx * speed
            self.rect.y += dy * speed
            moved = True
        elif self.is_sliding:
            dx, dy = self.direction.value
            self.rect.x += dx
            self.rect.y += dy
            moved = True

        if moved:
            self.rect.clamp_ip(SCREEN_RECT)
            self.check_tile_collisions(old_x, old_y, enemy_group)

        self.shoot_delay = 25 if self.stars >= 2 else 40

        if keys[pygame.K_SPACE] and self.cooldown == 0:
            self.shoot(bullet_group, self.bullet_type, Team.PLAYER, self.stars)

        self.update_image(GREEN if self.invulnerable_timer == 0 else CYAN)


class EnemyTank(Tank):
    """Вражеские танки со стратегией"""
    def __init__(self, x, y, all_blocks, enemy_type, strategy_type):
        super().__init__(x, y, all_blocks)
        self.enemy_type = enemy_type
        self.strategy = strategy_type
        self.ai_timer = 0
        self.heal_timer = 0

        stats = ENEMY_STATS[enemy_type]
        self.speed = stats.speed
        self.hp = stats.hp
        self.max_hp = stats.hp
        self.bullet_type = stats.bullet
        self.color = stats.color
        self.shoot_delay = stats.shoot_delay

    def heal(self):
        """Самолечение танка"""
        if self.enemy_type != EnemyType.ARMORED:
            return
        self.heal_timer += 1
        if self.heal_timer >= 180:
            self.heal_timer = 0
            self.hp = min(self.hp + 1.0, self.max_hp)

    def get_speed(self, enemy_group):
        """Ускорение танка"""
        speed = self.speed
        if self.enemy_type == EnemyType.SHOOTER:
            shooters = sum(1 for e in enemy_group if e.enemy_type == EnemyType.SHOOTER)
            if shooters >= 2:
                speed += 1
        if self.is_sliding:
            speed += 1
        return speed

    def choose_direction(self, player):
        """Выбор нового направления с учётом стратегии"""
        self.ai_timer += 1
        if self.ai_timer <= 90:
            return
        self.ai_timer = 0

        match self.strategy:
            case StrategyType.CHASE:
                if abs(player.rect.x - self.rect.x) > abs(player.rect.y - self.rect.y):
                    right = player.rect.x > self.rect.x
                    self.direction = Direction.RIGHT if right else Direction.LEFT
                else:
                    down = player.rect.y > self.rect.y
                    self.direction = Direction.DOWN if down else Direction.UP
            case StrategyType.PATROL:
                self.direction = random.choice(list(Direction))
            case StrategyType.BASE:
                if random.random() < 0.6:
                    self.direction = Direction.DOWN
                else:
                    to_center = (WIDTH // 2) > self.rect.x
                    self.direction = Direction.RIGHT if to_center else Direction.LEFT

    def sees_player(self, player):
        """Поведение вражеского танка, когда он видит игрока"""
        dx, dy = self.direction.value
        if dx == 0:
            same_line = abs(player.rect.centerx - self.rect.centerx) < TILE_SIZE // 2
            in_front = (player.rect.centery - self.rect.centery) * dy > 0
        else:
            same_line = abs(player.rect.centery - self.rect.centery) < TILE_SIZE // 2
            in_front = (player.rect.centerx - self.rect.centerx) * dx > 0
        return same_line and in_front

    def update(self, player, bullet_group, enemy_group):
        """Получение состояния танка"""
        self.handle_effects()
        self.heal()
        speed = self.get_speed(enemy_group)
        self.choose_direction(player)

        old_x, old_y = self.rect.x, self.rect.y
        dx, dy = self.direction.value
        self.rect.x += dx * speed
        self.rect.y += dy * speed
        self.rect.clamp_ip(SCREEN_RECT)

        other_tanks = list(enemy_group) + [player]
        if self.check_tile_collisions(old_x, old_y, other_tanks):
            self.direction = random.choice(list(Direction))
            self.ai_timer = 0

        if self.cooldown == 0 and self.sees_player(player):
            self.shoot(bullet_group, self.bullet_type, Team.ENEMY)

        self.update_image(self.color)


class Bonus(pygame.sprite.Sprite):
    """Класс бонусов"""
    def __init__(self, x, y):
        super().__init__()
        self.type = random.choice(list(BONUS_COLORS))
        self.image = pygame.Surface((16, 16))
        self.image.fill(BONUS_COLORS[self.type])
        self.rect = self.image.get_rect(center=(x, y))

    def apply(self, player):
        """Применение бонуса"""
        match self.type:
            case BonusType.SCORE:
                player.score += 500
            case BonusType.LIFE:
                player.lives += 1
            case BonusType.STAR:
                if player.stars < 3:
                    player.stars += 1
            case BonusType.INVULNERABLE:
                player.invulnerable_timer = 300
        self.kill()
