import pytest

import main
import src.game as game_module


class FakeGame:
    started = False
    sound_enabled = None

    def __init__(self, sound=True):
        self.sound_enabled = sound

    def run(self):
        FakeGame.started = True


def make_failing_game(error):
    class FailingGame:
        def __init__(self, sound=True):
            self.sound = sound

        def run(self):
            raise error

    return FailingGame


def test_defaults():
    assert main.parse_args([]).debug is False


def test_debug_flag():
    assert main.parse_args(["--debug"]).debug is True


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help(flag, capsys):
    with pytest.raises(SystemExit) as exc:
        main.parse_args([flag])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower() or "справка" in captured.out.lower()


def test_main_runs_game(monkeypatch):
    FakeGame.started = False
    old_game_class = game_module.Game
    game_module.Game = FakeGame

    try:
        assert main.main([]) == 0
        assert FakeGame.started
    finally:
        game_module.Game = old_game_class


def test_unexpected_error_hides_traceback(monkeypatch, capsys):
    monkeypatch.setattr(game_module, "Game", make_failing_game(RuntimeError("boom")))
    assert main.main([]) == 1

    err = capsys.readouterr().err
    assert "Ошибка: boom" in err
    assert "Traceback" not in err


def test_debug_mode_shows_traceback(monkeypatch):
    monkeypatch.setattr(game_module, "Game", make_failing_game(RuntimeError("boom")))
    with pytest.raises(RuntimeError, match="boom"):
        main.main(["--debug"])


def test_passes_disabled_sound(monkeypatch):
    FakeGame.started = False
    FakeGame.sound_enabled = None
    monkeypatch.setattr("src.game.Game", FakeGame)

    assert main.main(["--no-sound"]) == 0
    assert FakeGame.started is True
    assert FakeGame.sound_enabled is None
