@echo off
chcp 65001 >nul
rem Проверить карточки, пересобрать index.html, закоммитить и запушить (Windows).
rem
rem   deploy.bat                       коммит с датой в сообщении
rem   deploy.bat "Добавил карточки"    коммит со своим сообщением

setlocal
cd /d "%~dp0"

where python >nul 2>&1 || (echo Не найден python. Установите Python и повторите. & exit /b 1)
where git    >nul 2>&1 || (echo Не найден git. & exit /b 1)

echo.
echo [1/4] Проверяю карточки
python check.py
if errorlevel 1 (
  echo.
  echo Проверка не прошла. Исправьте карточки и запустите снова — ничего не закоммичено.
  exit /b 1
)

echo.
echo [2/4] Собираю index.html
python build.py
if errorlevel 1 exit /b 1

echo.
echo [3/4] Коммит
git diff --quiet && git diff --cached --quiet && (
  echo Изменений нет — коммитить нечего.
  exit /b 0
)

git status --short
set "MSG=%~1"
if "%MSG%"=="" set "MSG=Обновление тренажёра %date% %time:~0,5%"
git add -A
git commit -q -m "%MSG%"
echo Закоммичено: %MSG%

echo.
echo [4/4] Отправляю на GitHub
git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo.
  echo Удалённый репозиторий ещё не подключён. Коммит сохранён локально.
  echo.
  echo Создайте пустой публичный репозиторий на github.com, затем выполните:
  echo     git remote add origin https://github.com/ВАШ_ЛОГИН/russkiy-pitstop.git
  echo     git push -u origin main
  echo.
  echo После этого включите Pages: Settings ^> Pages ^> Source ^> GitHub Actions.
  exit /b 0
)

git rev-parse --abbrev-ref "@{upstream}" >nul 2>&1
if errorlevel 1 (git push -u origin main) else (git push)

echo.
echo Готово. Сайт обновится через минуту-две.
endlocal
