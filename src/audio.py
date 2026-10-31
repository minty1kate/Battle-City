import math
import random
from array import array
from functools import lru_cache

import pygame

from src.settings import SoundEvent

SAMPLE_RATE = 22050
SAMPLE_FORMAT = -16
MIXER_CHANNELS = 1
MIXER_BUFFER = 512
MAX_AMPLITUDE = 32767
SFX_VOLUME = 0.6
MUSIC_VOLUME = 0.35
NOTE_STEP = 0.25

CHORDS = ((57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62))
ARPEGGIO = (0, 1, 2, 1, 2, 1, 0, 1)


def midi_to_freq(note):
    """Частота ноты MIDI в герцах (69 = ля первой октавы = 440 Гц)"""
    return 440.0 * 2 ** ((note - 69) / 12)


def square(phase):
    """Прямоугольная волна (фаза в периодах)"""
    return 1.0 if phase % 1.0 < 0.5 else -1.0


def triangle(phase):
    """Треугольная волна"""
    return 4.0 * abs(phase % 1.0 - 0.5) - 1.0


def sawtooth(phase):
    """Пилообразная волна"""
    return 2.0 * (phase % 1.0) - 1.0


def sine(phase):
    """Синусоида"""
    return math.sin(2.0 * math.pi * phase)


def tone(rate, duration, freq_start, freq_end=None, shape=square, volume=0.5, decay=True):
    """Один тон: частота плавно меняется от freq_start до freq_end, громкость затухает"""
    freq_end = freq_start if freq_end is None else freq_end
    count = int(rate * duration)
    samples = []
    phase = 0.0
    for i in range(count):
        progress = i / count
        phase += (freq_start + (freq_end - freq_start) * progress) / rate
        envelope = 1.0 - progress if decay else 1.0
        samples.append(shape(phase) * volume * envelope)
    return samples


def noise_burst(rate, duration, volume=0.5, seed=1):
    """Шум, быстро затихающий (выстрелы, взрывы)"""
    rng = random.Random(seed)
    count = int(rate * duration)
    return [rng.uniform(-1.0, 1.0) * volume * (1.0 - i / count) ** 2 for i in range(count)]


def melody(rate, notes, note_length, shape=square, volume=0.4):
    """Последовательность нот MIDI, одна за другой"""
    samples = []
    for note in notes:
        samples += tone(rate, note_length, midi_to_freq(note), shape=shape, volume=volume)
    return samples


def mix(*tracks):
    """Складывает дорожки (короткие дополняются тишиной)"""
    length = max(len(track) for track in tracks)
    result = [0.0] * length
    for track in tracks:
        for i, value in enumerate(track):
            result[i] += value
    return result


def to_pcm(samples, channels):
    """Переводит дорожку из чисел от -1 до 1 в байты 16-битного звука"""
    data = array('h')
    for value in samples:
        clipped = max(-1.0, min(1.0, value))
        data.extend([int(clipped * MAX_AMPLITUDE)] * channels)
    return data.tobytes()


def build_effects(rate):
    """Дорожки всех звуковых эффектов: словарь {событие: список отсчётов}"""
    return {
        SoundEvent.SHOT: tone(rate, 0.12, 900, 300, square, 0.35),
        SoundEvent.ENEMY_SHOT: tone(rate, 0.10, 500, 200, square, 0.2),
        SoundEvent.HIT: noise_burst(rate, 0.06, 0.3),
        SoundEvent.EXPLOSION: noise_burst(rate, 0.4, 0.6, seed=2),
        SoundEvent.PLAYER_HIT: tone(rate, 0.3, 400, 80, sawtooth, 0.5),
        SoundEvent.MINE: mix(noise_burst(rate, 0.5, 0.6, seed=3),
                             tone(rate, 0.5, 90, 40, sine, 0.6)),
        SoundEvent.BONUS: melody(rate, (72, 76, 79, 84), 0.07),
        SoundEvent.LEVEL_START: melody(rate, (60, 64, 67, 72), 0.1),
        SoundEvent.PAUSE: melody(rate, (69, 62), 0.08, volume=0.3),
        SoundEvent.SAVE: melody(rate, (76, 83), 0.06, volume=0.3),
        SoundEvent.GAME_OVER: melody(rate, (67, 64, 60, 55), 0.3, triangle, 0.5),
        SoundEvent.WIN: melody(rate, (60, 64, 67, 72, 67, 72), 0.15, square, 0.4),
    }


def build_music(rate):
    """Фоновая мелодия на 8 секунд (зацикливается): арпеджио и бас на четырёх аккордах"""
    lead, bass = [], []
    for chord in CHORDS:
        for index in ARPEGGIO:
            lead += tone(rate, NOTE_STEP, midi_to_freq(chord[index] + 12), volume=0.18)
        for _ in range(4):
            bass += tone(rate, NOTE_STEP * 2, midi_to_freq(chord[0] - 12), shape=triangle,
                         volume=0.3)
    return mix(lead, bass)


@lru_cache(maxsize=None)
def build_buffers(rate, channels):
    """Готовые байты всех звуков и музыки. Считаются один раз и запоминаются"""
    effects = {event: to_pcm(track, channels) for event, track in build_effects(rate).items()}
    return effects, to_pcm(build_music(rate), channels)


def configure_mixer():
    """Задаёт параметры звука. Нужно вызвать до pygame.init()"""
    pygame.mixer.pre_init(SAMPLE_RATE, SAMPLE_FORMAT, MIXER_CHANNELS, MIXER_BUFFER)


class AudioManager:
    """Проигрывает звуки и музыку. Без звукового устройства все методы ничего не делают"""

    def __init__(self, enabled=True):
        self.available = False
        self.muted = False
        self.sounds = {}
        self.music = None
        self.music_channel = None
        if enabled:
            self.available = self._init_mixer()

    def _init_mixer(self):
        """Готовит звуки. Возвращает False, если звук запустить не удалось"""
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            settings = pygame.mixer.get_init()
            if settings is None or settings[1] != SAMPLE_FORMAT:
                return False
            rate, _, channels = settings
            effects, music = build_buffers(rate, channels)
            self.sounds = {event: pygame.mixer.Sound(buffer=data)
                           for event, data in effects.items()}
            for sound in self.sounds.values():
                sound.set_volume(SFX_VOLUME)
            self.music = pygame.mixer.Sound(buffer=music)
            self.music.set_volume(MUSIC_VOLUME)
        except (pygame.error, NotImplementedError):
            return False
        return True

    def play(self, event):
        """Проигрывает звук события"""
        if self.available and not self.muted:
            self.sounds[event].play()

    def start_music(self):
        """Запускает музыку с начала (зацикленно)"""
        if not self.available:
            return
        self.stop_music()
        self.music_channel = self.music.play(loops=-1)
        self._apply_music_volume()

    def pause_music(self):
        """Ставит музыку на паузу"""
        if self.music_channel is not None:
            self.music_channel.pause()

    def resume_music(self):
        """Продолжает музыку после паузы"""
        if self.music_channel is not None:
            self.music_channel.unpause()

    def stop_music(self):
        """Останавливает музыку"""
        if self.music is not None:
            self.music.stop()
        self.music_channel = None

    def toggle_mute(self):
        """Включает или выключает весь звук. Возвращает True, если звук теперь выключен"""
        self.muted = not self.muted
        self._apply_music_volume()
        return self.muted

    def _apply_music_volume(self):
        if self.music_channel is not None:
            self.music_channel.set_volume(0.0 if self.muted else 1.0)
