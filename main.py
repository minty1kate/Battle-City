"""Точка входа: py main.py [--help] [--debug]"""
import argparse
import sys

EPILOG = """\
управление в игре:
  стрелки или WASD - движение
  пробел           - выстрел
  ENTER            - старт в меню
  1, 2, 3, 4       - перейти на уровень (отладка)
  P                - пауза
  F5               - сохранить игру
  F9               - загрузить сохранение
  R                - начать заново после победы или поражения
"""


def parse_args(argv=None):
    """Разбирает аргументы командной строки"""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Battle City",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="показать эту справку и выйти")
    parser.add_argument("--debug", action="store_true",
                        help="режим отладки: при ошибке показывать Traceback")
    return parser.parse_args(argv)


def main(argv=None):
    """Запускает игру. Возвращает код выхода"""
    args = parse_args(argv)
    try:
        from src.game import Game
        Game().run()
    except KeyboardInterrupt:
        print("\nПрервано пользователем", file=sys.stderr)
        return 130
    except ImportError as err:
        if args.debug:
            raise
        if err.name == "pygame":
            print("Ошибка: не установлен pygame", file=sys.stderr)
        else:
            print(f"Ошибка: не удалось загрузить модуль ({err})", file=sys.stderr)
        return 1
    except Exception as err:
        if args.debug:
            raise
        print(f"Ошибка: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
