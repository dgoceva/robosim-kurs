"""Копира примерните програми и сцените на симулатора в папка, където могат да се отварят и променят.

    python -m robosim.examples              # в папка robosim_primeri
    python -m robosim.examples моя_папка
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def copy_examples(target="robosim_primeri"):
    target = Path(target)
    (target / "scenes").mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in sorted((HERE / "_examples").glob("*.py")) + sorted((HERE / "scenes").glob("*.json")):
        dst = target / ("scenes" if src.suffix == ".json" else "") / src.name
        if dst.exists():
            print(f"  пропуснат (вече съществува): {dst}")
            continue
        shutil.copy(src, dst)
        copied += 1
    print(f"Копирани файлове: {copied} в папка {target.resolve()}")
    print("Отворете папката във VS Code и изпълнете primer_01_dvizhenia.py.")
    return target


def main():
    copy_examples(sys.argv[1] if len(sys.argv) > 1 else "robosim_primeri")


if __name__ == "__main__":
    main()
