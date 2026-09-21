# qwencode-branch-stats

`qwencode-branch-stats` (краткое имя команды из консоли — `qbs`) —
кроссплатформенный CLI-инструмент на Python для расчёта
стоимости и метрик использования Qwen Code в разрезе Git-ветки.

## Быстрый старт

1. Установите пакет из PyPI:

   ```bash
   pip install qwencode-branch-stats
   ```

2. Подключите `SessionEnd` hook — создайте файл `.qwen/settings.json` в корне
   вашего Git-репозитория со следующим содержимым:

   ```json
   {
     "$version": 4,
     "hooks": {
       "SessionEnd": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "qbs hook session-end",
               "name": "session-report",
               "description": "Записывает отчёт о завершённой сессии",
               "timeout": 1000000,
               "statusMessage": "Generating session report..."
             }
           ]
         }
       ]
     }
   }
   ```

   Если файл `.qwen/settings.json` уже существует, не перезаписывайте его
   целиком — добавьте в существующую конфигурацию блок `hooks.SessionEnd`.

3. После завершения Qwen session посмотрите отчёты в папке `.qbs/` в корне
   репозитория: `report.md` — для человека, `report.json` — машиночитаемый.
   Хук перестраивает оба файла автоматически при каждом завершении session.

## 1. Что делает приложение

Инструмент связывает завершённые Qwen Code sessions с текущими Git repository
и branch, читает локальную телеметрию Qwen, а затем создаёт два согласованных
отчёта:

- `report.md` — удобный отчёт для человека;
- `report.json` — те же данные в машиночитаемом виде.

В отчёте показываются:

- общая стоимость работы в ветке;
- стоимость, запросы и токены по моделям;
- стоимость по sessions, main agent и именам subagents;
- input, cached input, output и reasoning tokens;
- API duration, tool duration и subagent duration;
- вызовы обычных tools и MCP tools;
- количество и иерархия запусков subagents;
- предупреждения о неполных или повреждённых данных.

Одна ветка может включать несколько sessions, например «Исследование»,
«Реализация» и «Написание тестов». Одна session может использовать несколько
моделей.

Отчёты сохраняются в папку `.qbs/` в корне проекта и автоматически
обновляются при завершении каждой Qwen session (через `SessionEnd` hook).
Команду `qbs report` можно запускать в любой момент — она перестраивает те же
файлы заново из исходных данных.

### Пример отчёта

Фрагмент `report.md`:

```markdown
# feature/PROJ-1234-add-cache

Repository: my-project
Branch: feature/PROJ-1234-add-cache
Sessions: 3
Observation span: 2026-09-17T10:20:00Z — 2026-09-18T14:45:00Z

## Cost by model

| Model | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---:|---:|---:|---:|---:|---:|
| routerai/deepseek/deepseek-v4-flash | 42 | 1,200,000 | 800,000 | 15,000 | 3,000 | 7.38 |
| routerai/qwen/qwen3.8-flash | 15 | 450,000 | 300,000 | 8,000 | 1,200 | 7.61 |

Total cost: 14.99

## Sessions

| Session | Title | Models | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 18697f75… | Исследование архитектуры | deepseek-v4-flash | 17 | 410,000 | 250,000 | 6,000 | 1,200 | 3.41 |
| a1b2c3d4… | Реализация API | qwen3.8-flash | 28 | 870,000 | 590,000 | 12,000 | 2,000 | 8.17 |
| f9e8d7c6… | Написание тестов | deepseek-v4-flash, qwen3.8-flash | 12 | 370,000 | 260,000 | 5,000 | 1,000 | 3.41 |
```

Кроме показанных таблиц, полный Markdown-отчёт содержит секции `Cost by agent`,
`Overall usage`, `Session details`, `Tools`, `MCP`, `Subagents` и
`Data quality / warnings`.

## 2. Как начать пользоваться

### Требования

- Python 3.10 или новее;
- Git, доступный через команду `git`;
- установленный и используемый Qwen Code;
- запуск команд внутри Git working tree.

### Версии

Версия инструмента имеет формат
`<версия Qwen Code, на которой код проверен>.<версия приложения>` —
например, `0.24.0.0`. Версия приложения начинается с `0` на каждой версии
Qwen Code. Подробности — в разделах [Версионирование](#4-версионирование) и
[Как обновить](#5-как-обновить).

### Установка и хук

Пакет устанавливается из PyPI, а `SessionEnd` hook подключается так, как
описано в [Быстром старте](#быстрый-старт). Вместо установки из PyPI пакет
можно поставить из исходного кода — см. раздел [5. Как обновить](#5-как-обновить).
Проверка установки:

```bash
qbs --version
```

### Проверка хука

Hook должен получать JSON-событие Qwen через standard input; инструмент
распознаёт идентификатор session в полях `sessionId`, `session_id` или
`session.id`. Рабочий каталог hook менять не нужно: repository и branch
определяются именно в момент завершения session.

Для ручной проверки из нужного Git-репозитория можно выполнить:

```bash
echo '{"sessionId":"18697f75-6ead-472a-b700-18afb74ab2a2"}' \
  | qbs hook session-end
```

Также идентификатор можно передать явно:

```bash
qbs hook session-end \
  --session-id 18697f75-6ead-472a-b700-18afb74ab2a2
```

### Шаг 1. Работать с Qwen Code

Работайте в Git-ветке как обычно. Для удобства последующего анализа задавайте
sessions понятные custom titles средствами Qwen Code, например:

- `Исследование архитектуры`;
- `Реализация API`;
- `Написание тестов`.

Если session переименовывалась несколько раз, в отчёт попадёт последнее
сохранённое custom title. Если title не задан, значение останется пустым —
`qwencode-branch-stats` не генерирует названия самостоятельно.

### Шаг 2. Проверить окружение

Из рабочей директории проекта:

```bash
qbs doctor
```

Для машиночитаемого результата:

```bash
qbs doctor --json
```

Команда проверяет Git-контекст, наличие каталога Qwen, `settings.json`, usage
files и число sessions, связанных с текущей веткой.

### Шаг 3. Построить отчёт

Из нужной Git-ветки выполните:

```bash
qbs report
```

По умолчанию отчёты сохраняются в папку `.qbs/` в текущем каталоге.
После подключения hook из [Быстрого старта](#быстрый-старт) эти файлы также
автоматически пересоздаются при каждом завершении Qwen session — отдельный
запуск команды для этого не требуется:

```text
.qbs/
├── report.json
└── report.md
```

Каталог вывода можно изменить параметром `--output-dir`:

```bash
qbs report --output-dir /path/to/reports
```

Повторный запуск безопасен: отчёт заново строится из исходных данных Qwen.
Записи usage дедуплицируются по `usage.id`, а tool calls — по `call_id`, если
он присутствует.

### Нестандартное расположение данных

По умолчанию Qwen-артефакты читаются из `~/.qwen`. Путь можно изменить:

```bash
export QBS_QWEN_HOME=/path/to/qwen-data
```

Также поддерживается переменная `QWEN_HOME`.

Расположение внутреннего хранилища связей session с Git можно изменить:

```bash
export QBS_DATA_DIR=/path/to/qbs-data
```

Для разового запуска доступны параметры `--qwen-home` и `--data-dir`:

```bash
qbs report \
  --qwen-home /path/to/qwen-data \
  --data-dir /path/to/qbs-data
```

В Windows используйте синтаксис переменных окружения и путей, соответствующий
PowerShell или `cmd.exe`.

## 3. Как работает

### Общая схема

```text
Qwen Code session
       │
       │ SessionEnd
       ▼
session ID → repository → branch
       │
       │ qbs report или SessionEnd hook
       ▼
┌─────────────────────────────────────────┐
│ token usage + chats + subagents         │
│                  + model pricing        │
└───────────────────┬─────────────────────┘
                    ▼
          нормализация и агрегация
                    │
             ┌──────┴──────┐
             ▼             ▼
        report.json    report.md
```

### 3.1. Привязка session к Git-ветке

Команда `qbs hook session-end` получает session ID и запускает:

```bash
git rev-parse --show-toplevel
git branch --show-current
```

Полученная связь сохраняется локально:

```text
session ID + абсолютный путь repository + branch + captured_at
```

Абсолютный нормализованный путь позволяет различать репозитории с одинаковыми
названиями веток. Каждая session хранится в отдельном атомарно заменяемом файле,
поэтому несколько Qwen-процессов могут завершаться параллельно.

В сами отчёты в качестве repository попадает только название папки проекта —
папки, в которой находится `.git`. Полный путь используется лишь как внутренний
идентификатор в хранилище связей и в отчёт не записывается.

После сохранения связи хук автоматически перестраивает `report.json` и
`report.md` в папку `.qbs/` этого repository, поэтому отчёты актуальны сразу
после завершения session. Если построение отчёта не удалось, сохранённый
mapping не откатывается — текст ошибки выводится в stderr хука.

### 3.2. Поиск sessions для отчёта

При запуске `qbs report` инструмент снова определяет текущие repository
и branch, после чего выбирает только связанные с этой комбинацией завершённые
sessions.

Команда `qwen sessions list` не используется: все данные читаются напрямую из
локальных артефактов Qwen Code.

### 3.3. Источники данных

| Метрика | Источник |
|---|---|
| Repository и branch | SessionEnd hook + Git |
| Title и время session | `~/.qwen/projects/.../chats/<session-id>.jsonl` |
| Модели, токены и API duration | `~/.qwen/usage/token-usage-YYYY-MM.jsonl` |
| Цена моделей | `~/.qwen/settings.json` → `modelPricing` |
| Main tools и MCP | transcript основной session |
| Запуски и иерархия subagents | `subagents/<session-id>/*.meta.json` |
| Tools subagents | `subagents/<session-id>/*.jsonl` |

JSONL-файлы обрабатываются построчно. Сначала выполняется фильтрация по нужным
session IDs, поэтому большие usage и transcript files не загружаются целиком в
память.

### 3.4. Расчёт стоимости

Для каждого LLM request цена берётся из `settings.json` и рассчитывается так:

```text
input cost  = inputTokens  / 1 000 000 × inputPerMillionTokens
output cost = outputTokens / 1 000 000 × outputPerMillionTokens
cost        = input cost + output cost
```

`cachedTokens` показываются отдельно, но при текущей структуре Qwen pricing не
имеют отдельного тарифа и уже входят в расчёт через `inputTokens`.

`thoughtsTokens` выводятся как reasoning tokens и не прибавляются повторно к
`outputTokens`.

Далее каждый request агрегируется по:

```text
session + model + agent → session → repository + branch
```

Если для хотя бы одной использованной модели нет pricing, её стоимость и
зависящие от неё общие суммы получают значение `null` в JSON и `unknown` в
Markdown. В отчёт также добавляется warning `pricing_missing` — частичная сумма
не выдаётся за полную.

### 3.5. Tools, MCP и subagents

Tool calls группируются по имени инструмента. Для каждого имени считаются:

- общее число вызовов;
- успешные и неуспешные вызовы;
- суммарная длительность.

Имена вида:

```text
mcp__gitlab__get_mcp_server_version
```

нормализуются в MCP server `gitlab` и tool `get_mcp_server_version`. MCP-вызовы
одновременно входят в общее число tool calls.

Запуски subagents считаются по metadata files. Поля `parentSessionId`,
`parentAgentId` и `depth` сохраняют иерархию вложенных агентов. Расходы LLM
агрегируются по значению `source`, например `main` или `general-purpose`.

### 3.6. Предупреждения и частичные данные

Отсутствие части данных не останавливает построение отчёта. Вместо этого в
`report.json` и `report.md` добавляются warnings, например:

- `pricing_missing`;
- `session_mapping_missing`;
- `transcript_missing`;
- `subagent_metadata_missing`;
- `malformed_jsonl`;
- `unknown_qwen_schema`.

Так можно получить доступные метрики и одновременно увидеть, какие значения
нельзя считать полными.

### 3.7. Приватность

В отчёты попадают только необходимые metadata и числовые метрики. Инструмент не
копирует исходные Qwen events целиком и не записывает в отчёты:

- prompts и ответы assistant;
- reasoning text;
- аргументы и результаты tools;
- shell-команды и их вывод;
- MCP payloads;
- содержимое файлов;
- API keys и credentials;
- полные пути repository на диске.

Разрешены session titles, названия моделей, agents и tools, MCP server/tool,
название папки проекта и Git branch, timestamps, statuses и числовые показатели.

## 4. Версионирование

Формат версии `qwencode-branch-stats`:
`<версия Qwen Code, на которой код проверен>.<версия приложения>`.
Например, версия `0.24.0.1` означает, что код протестирован с Qwen Code
`0.24.0` (`qwen --version`) и это второй релиз приложения на ней. Версия
приложения начинается с `0` на каждой версии Qwen Code и увеличивается на 1
при каждом следующем релизе на той же версии Qwen Code.

Совпадать должны три значения; четвёртое выводится из них:

| Место                                                    | Пример значения                     |
|----------------------------------------------------------|-------------------------------------|
| git tag репозитория                                       | `0.24.0.0`                          |
| `version` в `[project]` внутри `pyproject.toml`          | `0.24.0.0`                          |
| `__version__` в `src/qwencode_branch_stats/__init__.py` | `0.24.0.0`                          |
| вывод `qbs --version`                                    | `qwencode-branch-stats 0.24.0.0`    |

Версией Qwen Code, на которой проверен инструмент, является всё, кроме
последнего сегмента; последний сегмент — номер релиза приложения на ней.
`qbs doctor` помогает быстро проверить совместимость с окружением.

## 5. Как обновить

### После обновления Qwen Code

1. Узнайте версию Qwen Code:

   ```bash
   qwen --version
   ```

2. Проверьте код на этой версии. Тесты:

   ```bash
   python -m unittest discover -s tests -v
   ```

   Затем прогоните одну реальную Qwen session и убедитесь, что SessionEnd
   hook сохранил mapping и обновил `.qbs/report.md` и `.qbs/report.json`
   с корректными метриками. Диагностика — `qbs doctor`.

3. Если проверка прошла, поднимите версию до `<версия Qwen Code>.0` в трёх
   местах (git tag, `pyproject.toml`, `__version__`) — для Qwen Code
   `0.25.0` это `0.25.0.0` — и переустановите пакет:

   ```bash
   pip install --force-reinstall --no-deps .
   qbs --version
   ```

4. Если parsers не разбирают артефакты новой версии Qwen Code (изменились
   форматы usage, chats, subagents или `settings.json`), версию не
   поднимайте: сначала почините разбор (`qwen/` и `aggregation.py`),
   затем повторите проверку.

### Релиз приложения на той же версии Qwen Code

Если код меняется, а версия проверенного Qwen Code та же (`X`), растёт
только версия приложения: `X.N` → `X.N+1`. Например, второй релиз на
Qwen Code `0.24.0` — это `0.24.0.1`.

### Установка версии под конкретный Qwen Code

Релизы соответствуют git tag:

```bash
git checkout 0.24.0.0
pip install .
```

## Основные команды

```bash
# Зафиксировать Git-контекст завершённой session и обновить отчёты в .qbs/
qbs hook session-end

# Проверить окружение
qbs doctor

# Построить report.json и report.md (по умолчанию в .qbs/)
qbs report

# Показать версию
qbs --version
```

## Запуск тестов

Проект использует стандартный `unittest`, дополнительные test dependencies не
требуются:

```bash
python -m unittest discover -s tests -v
```
