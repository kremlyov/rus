#!/usr/bin/env python3
"""
Сборка тренажёра в один самодостаточный HTML-файл.

Берёт src/app.html (оболочка: вёрстка + движок) и вставляет вместо
маркера /*DATA*/ все файлы src/*.js в алфавитном порядке имён.

    python3 build.py

На выходе — index.html в корне репозитория.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
SHELL = SRC / "app.html"
OUT = ROOT / "index.html"
MARKER = "/*DATA*/"


def main() -> int:
    if not SHELL.exists():
        print(f"Не найден {SHELL}", file=sys.stderr)
        return 1

    packs = sorted(SRC.glob("*.js"))
    if not packs:
        print("В src/ нет ни одного .js с карточками", file=sys.stderr)
        return 1

    shell = SHELL.read_text(encoding="utf-8")
    if MARKER not in shell:
        print(f"В {SHELL.name} нет маркера {MARKER}", file=sys.stderr)
        return 1

    data = "\n\n".join(p.read_text(encoding="utf-8") for p in packs)
    html = shell.replace(MARKER, data)
    OUT.write_text(html, encoding="utf-8")

    cards = len(re.findall(r"\{\s*t:\s*'", data))
    print(f"Собран {OUT.name}: {OUT.stat().st_size // 1024} КБ, карточек: {cards}")
    print("Пакеты: " + ", ".join(p.name for p in packs))
    print("Подробная сводка и проверка структуры: python3 check.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
