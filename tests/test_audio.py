import pytest

from src.audio import (
    AudioManager, build_effects, build_music, melody,
    mix, noise_burst, sawtooth, sine, square, tone, triangle,
)
from src.settings import SoundEvent


@pytest.mark.parametrize("wave, expected", [
    (square, 1.0), (triangle, 1.0), (sawtooth, -1.0),
])
def test_waveforms_at_known_phase(wave, expected):
    assert wave(0.0) == expected


def test_sine_wave_at_quarter_period():
    assert sine(0.25) == pytest.approx(1.0)


def test_waveforms_repeat_each_period():
    for wave in (square, triangle, sawtooth, sine):
        assert wave(0.125) == pytest.approx(wave(1.125))


def test_tone_has_expected_length_and_constant_envelope():
    samples = tone(100, 0.1, 10, shape=lambda phase: 1, volume=0.5, decay=False)
    assert len(samples) == 10
    assert samples == [0.5] * 10


def test_tone_decay_reaches_zero_at_last_sample():
    samples = tone(100, 0.1, 10, shape=lambda phase: 1, volume=1)
    assert samples[0] == 1
    assert samples[-1] == pytest.approx(0.1)


def test_noise_burst_is_repeatable_and_fades():
    first = noise_burst(100, 0.1, seed=42)
    assert first == noise_burst(100, 0.1, seed=42)
    assert len(first) == 10
    assert first[-1] == pytest.approx(first[0] * 0, abs=1)


def test_melody_concatenates_notes():
    result = melody(100, (60, 62, 64), 0.1)
    assert len(result) == 30


def test_mix_rejects_no_tracks():
    with pytest.raises(ValueError):
        mix()


def test_builders_create_all_sound_events():
    effects = build_effects(100)
    assert set(effects) == set(SoundEvent)
    assert all(effects.values())
    assert build_music(100)


def test_disabled_audio_manager():
    audio = AudioManager(enabled=False)
    assert not audio.available
    audio.play(SoundEvent.SHOT)
    audio.start_music()
    audio.pause_music()
    audio.resume_music()
    audio.stop_music()
    assert audio.toggle_mute() is True
    assert audio.toggle_mute() is False


def test_audio_manager_mute():
    class Sound:
        def __init__(self):
            self.calls = 0

        def play(self):
            self.calls += 1

    audio = AudioManager(enabled=False)
    sound = Sound()
    audio.available = True
    audio.sounds[SoundEvent.SHOT] = sound
    audio.play(SoundEvent.SHOT)
    audio.muted = True
    audio.play(SoundEvent.SHOT)
    assert sound.calls == 1
