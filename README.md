# Soccer Pinball '98 — в браузере

Запуск классической игры **Dynamite Soccer Pinball '98** (Pin-Ball Games Ltd., 1998,
Windows 95/98) прямо в браузере — без установки, целиком на стороне клиента.

### ▶ Играть онлайн: **https://vasia123.github.io/pinball-soccer-98/**

Оригинал распространялся как единый Windows‑исполняемый файл (DirectDraw‑игра).
Здесь он запускается через [**BoxedWine**](https://github.com/danoon2/Boxedwine) —
Wine, скомпилированный в WebAssembly (Emscripten). Это **эмуляция**, а не
декомпиляция/переписывание: движок игры (`winpin.exe`) исполняется как есть.

## Играть

Открой `docs/index.html` через любой статический веб‑сервер (или задеплой на GitHub Pages)
и нажми **ИГРАТЬ**. Локально:

```bash
cd docs && python3 -m http.server 8000
# затем открой http://localhost:8000/
```

> ⚠️ Нельзя открывать `index.html` как `file://` — нужен HTTP‑сервер
> (BoxedWine грузит `.wasm`/`.zip` по сети).

### Управление
| Клавиша | Действие |
|---|---|
| **Левый Shift** | левый флиппер |
| **Правый Shift** | правый флиппер |
| **Space** | запуск мяча (плунжер) |
| **Enter** | подтвердить в меню |
| **Esc** | назад / выход из стола |

Кнопки в меню нажимай с чуть удержанным кликом (эмулятор опрашивает мышь по кадрам).
Первая загрузка стола идёт медленно (интерпретация x86 без JIT) — это разово.

## Что внутри (`docs/`)
| Файл | Назначение |
|---|---|
| `index.html` | лендинг с кнопкой запуска |
| `boxedwine.html/.js/.wasm/.css/-shell.js` | рантайм BoxedWine (**multi‑threaded**, 26R1) |
| `boxedwine.zip` | минимальная файловая система Wine с DirectDraw (~35 МБ) |
| `pinball.zip` | файлы игры (~32 МБ) |
| `coi-serviceworker.js` | включает COOP/COEP (SharedArrayBuffer) на GitHub Pages |
| `.nojekyll` | отключает Jekyll на GitHub Pages |

Запуск конфигурируется через query‑параметры к `boxedwine.html`:
`?app=pinball&p=winpin.bat&resolution=800x600&sound=true`.

Используется **многопоточная** сборка BoxedWine (эмуляция CPU идёт параллельно
отрисовке/звуку — загрузка стола примерно в 1.8× быстрее single‑threaded). Ей нужны
COOP/COEP‑заголовки (SharedArrayBuffer), которых GitHub Pages не задаёт, поэтому
подключён [`coi-serviceworker`](https://github.com/gzuidhof/coi-serviceworker): он
включает изоляцию через service worker прямо на статике. Требуется современный
браузер с поддержкой SharedArrayBuffer.

## Деплой на GitHub Pages
1. Запушь репозиторий на GitHub.
2. Settings → Pages → Source: **Deploy from a branch**, ветка `main`, папка **`/docs`**.
3. Через минуту сайт будет доступен по адресу `https://<user>.github.io/<repo>/`.

Ограничения Pages соблюдены: макс. файл ~35 МБ (< 100 МБ), весь сайт ~70 МБ (< 1 ГБ).

## Как это собрано (воспроизводимость)
См. [`docs-build/HOWITWASMADE.md`](docs-build/HOWITWASMADE.md) — полный разбор:
распаковка Gentee‑инсталлятора через Wine, определение графического стека
(DirectDraw/DirectSound/DirectInput, без 3D), упаковка в app‑zip, удаление
интро‑видео `soccer98.avi` (DirectShow/quartz.dll отсутствует в minimal‑Wine и вешал игру).

Пересобрать `pinball.zip` из установленной игры:
```bash
./docs-build/build-pinball-zip.sh
```

## Известные ограничения
- **Первая загрузка стола не мгновенна** — BoxedWine исполняет x86 интерпретатором
  (в web‑сборке нет JIT). Многопоточная сборка ускоряет это ~в 1.8×, но полностью
  «нативной» скорости нет. Загрузка разовая, дальше игра идёт из памяти.
- **Нужен современный браузер** с SharedArrayBuffer (для многопоточной сборки).
- **Интро‑ролик отключён** — использовал DirectShow, недоступный в minimal‑Wine.
- **Звук** — работает, но в web‑сборке BoxedWine местами несовершенен.

## Права
Оригинальная игра © 1998 Pin‑Ball Games Ltd. Проект — для сохранения и ностальгии.
Если вы правообладатель и против размещения — материал будет удалён.
