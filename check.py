#!/usr/bin/env python3
"""
Проверка банка карточек. Запускать после любой правки src/*.js:

    python3 check.py

Требует node (входит в большинство систем; проверить: node --version).
Скрипт не проверяет орфографию — только структуру: битые ссылки на правила,
пропущенные поля, выход индексов за границы, дубли, одинаковые варианты ответа.
"""

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"

JS = r"""
const fs = require('fs');
const files = process.argv.slice(1);
const src = files.map(f => fs.readFileSync(f, 'utf8')).join('\n');
const m = {};
new Function('m', src + '; m.RULES = RULES; m.CARDS = CARDS;')(m);
const { RULES, CARDS } = m;

const problems = [];
const seen = new Map();
const add = (i, msg) => problems.push({ i, msg, q: (CARDS[i].q || (CARDS[i].w || []).join(' ')).slice(0, 60) });

CARDS.forEach((c, i) => {
  if (!RULES[c.r]) add(i, 'нет такого правила: ' + c.r);
  if (!c.e) add(i, 'нет объяснения (поле e)');

  if (c.t === 'choice' || c.t === 'theory') {
    if (!Array.isArray(c.o) || c.o.length < 2) add(i, 'нужно минимум два варианта');
    else {
      if (!(c.a >= 0 && c.a < c.o.length)) add(i, 'поле a вне диапазона вариантов');
      if (new Set(c.o).size !== c.o.length) add(i, 'варианты повторяются');
    }
    if (c.t === 'choice' && !(c.q || '').includes('___')) add(i, 'в вопросе нет пропуска ___');
  } else if (c.t === 'comma') {
    if (!Array.isArray(c.w) || c.w.length < 2) add(i, 'нужен массив слов w');
    if (!Array.isArray(c.a)) add(i, 'поле a должно быть массивом');
    else c.a.forEach(x => { if (!(x >= 0 && x < c.w.length - 1)) add(i, 'позиция запятой вне текста: ' + x); });
  } else if (c.t === 'find') {
    if (!(c.a >= 0 && c.a < (c.w || []).length)) add(i, 'поле a вне массива слов');
    if (!c.fix) add(i, 'нет поля fix с верным написанием');
  } else {
    add(i, 'неизвестный тип карточки: ' + c.t);
  }

  const key = (c.q || '') + '|' + (c.w || []).join(' ');
  if (seen.has(key)) add(i, 'дубль карточки №' + seen.get(key));
  else seen.set(key, i);
});

const byRule = {};
CARDS.forEach(c => { byRule[c.r] = (byRule[c.r] || 0) + 1; });
Object.keys(RULES).forEach(r => { if (!byRule[r]) problems.push({ i: -1, msg: 'правило без карточек: ' + RULES[r].name, q: '' }); });

const byType = {};
CARDS.forEach(c => { byType[c.t] = (byType[c.t] || 0) + 1; });

console.log(JSON.stringify({
  cards: CARDS.length,
  rules: Object.keys(RULES).length,
  byRule, byType, problems,
}));
"""


def main() -> int:
    packs = sorted(SRC.glob("*.js"))
    if not packs:
        print("В src/ нет файлов с карточками", file=sys.stderr)
        return 1

    try:
        out = subprocess.run(
            ["node", "-e", JS, "--", *[str(p) for p in packs]],
            capture_output=True, text=True, check=True,
        ).stdout
    except FileNotFoundError:
        print("Не найден node. Установите Node.js и повторите.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print("JavaScript не выполнился — скорее всего, синтаксическая ошибка в src/*.js:\n", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return 1

    r = json.loads(out)
    print(f"Карточек: {r['cards']} · правил: {r['rules']}")
    print("По типам: " + ", ".join(f"{k} — {v}" for k, v in sorted(r["byType"].items())))
    print("По правилам: " + ", ".join(f"{k}={v}" for k, v in sorted(r["byRule"].items())))

    if not r["problems"]:
        print("\nПроблем не найдено.")
        return 0

    print(f"\nНайдено проблем: {len(r['problems'])}")
    for p in r["problems"]:
        where = f"карточка №{p['i']}" if p["i"] >= 0 else "общее"
        tail = f" — «{p['q']}…»" if p["q"] else ""
        print(f"  {where}: {p['msg']}{tail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
