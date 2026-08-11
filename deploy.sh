#!/usr/bin/env bash
#
# Проверить карточки, пересобрать index.html, закоммитить и запушить.
#
#   ./deploy.sh                        коммит с датой в сообщении
#   ./deploy.sh "Добавил карточки"     коммит со своим сообщением
#
set -euo pipefail
cd "$(dirname "$0")"

say()  { printf '\n\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '\033[32m%s\033[0m\n' "$1"; }
warn() { printf '\033[33m%s\033[0m\n' "$1"; }
die()  { printf '\033[31m%s\033[0m\n' "$1" >&2; exit 1; }

# --- окружение ---------------------------------------------------------------
command -v python3 >/dev/null || die "Не найден python3. Установите Python и повторите."
command -v git     >/dev/null || die "Не найден git."
command -v node    >/dev/null || warn "Не найден node — проверка карточек будет пропущена."

# --- 1. проверка -------------------------------------------------------------
if command -v node >/dev/null; then
  say "1/4 Проверяю карточки"
  python3 check.py || die "Проверка не прошла. Исправьте карточки и запустите снова — ничего не закоммичено."
else
  say "1/4 Проверка пропущена (нет node)"
fi

# --- 2. сборка ---------------------------------------------------------------
say "2/4 Собираю index.html"
python3 build.py

# --- 3. коммит ---------------------------------------------------------------
say "3/4 Коммит"
if [ -z "$(git status --porcelain)" ]; then
  ok "Изменений нет — коммитить нечего."
  exit 0
fi

git status --short
MSG="${1:-Обновление тренажёра $(date '+%d.%m.%Y %H:%M')}"
git add -A
git commit -q -m "$MSG"
ok "Закоммичено: $MSG"

# --- 4. пуш ------------------------------------------------------------------
say "4/4 Отправляю на GitHub"
if ! git remote get-url origin >/dev/null 2>&1; then
  warn "Удалённый репозиторий ещё не подключён. Коммит сохранён локально."
  cat <<'EOF'

Создайте пустой публичный репозиторий на github.com (без README и лицензии),
затем выполните:

    git remote add origin https://github.com/kremlyov/rus.git
    git push -u origin main

После этого включите Pages: Settings → Pages → Source → GitHub Actions.
Дальше хватит ./deploy.sh
EOF
  exit 0
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if git rev-parse --abbrev-ref "@{upstream}" >/dev/null 2>&1; then
  git push
else
  git push -u origin "$BRANCH"
fi

ok "Готово."

URL="$(git remote get-url origin)"
case "$URL" in
  *github.com*)
    USER_REPO="$(printf '%s' "$URL" | sed -E 's#.*github\.com[:/]##; s#\.git$##')"
    OWNER="${USER_REPO%%/*}"
    REPO="${USER_REPO##*/}"
    echo
    echo "Сборка:  https://github.com/${USER_REPO}/actions"
    echo "Сайт:    https://${OWNER}.github.io/${REPO}/  (обновится через минуту-две)"
    ;;
esac
