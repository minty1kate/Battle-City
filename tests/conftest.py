"""Общие настройки и фикстуры для тестов"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


import pygame
import pytest

from src.game import Game
from src.settings import TILE_BASE


class FakeKeys:
    """Замена pygame.key.get_pressed()"""
    def __init__(self, pressed=()):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed

class FakeEvent:
    """Имитация событий клавиатуры"""
    def __init__(self, event_type, key):
        self.type = event_type
        self.key = key

@pytest.fixture
def make_keys():
    """Создаёт набор нажатых клавиш"""
    def _make(*pressed):
        return FakeKeys(pressed)
    return _make


@pytest.fixture
def blocks():
    """Пустая группа блоков карты"""
    return pygame.sprite.Group()


@pytest.fixture
def keydown():
    """Создаёт событие нажатия клавиши"""
    def _keydown(key):
        return FakeEvent(pygame.KEYDOWN, key)
    return _keydown


@pytest.fixture
def send_events(monkeypatch):
    """Подменяет pygame.event.get"""
    old_get = pygame.event.get

    def _send(*events):
        pygame.event.get = lambda: list(events)

    yield _send
    pygame.event.get = old_get


@pytest.fixture
def game(monkeypatch):
    """Игра в состоянии "playing" без нажатых клавиш"""
    old_pressed = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: FakeKeys()

    g = Game()
    g.state = "playing"
    g.level_title_timer = 0

    yield g

    pygame.quit()
    pygame.key.get_pressed = old_pressed


@pytest.fixture
def bare_game(game):
    """Игра на карте только с базой"""
    for block in list(game.all_blocks):
        if block.type != TILE_BASE:
            block.kill()

    return game