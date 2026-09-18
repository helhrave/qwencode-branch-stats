# Техническое задание

## 1. Формат финального отчёта

`qwencode-branch-stats` (краткое имя команды из консоли — `qbs`) формирует два отчёта:

```text
report.md
report.json
```

`report.md` предназначен для просмотра человеком.

`report.json` содержит машиночитаемое представление тех же метрик для дальнейшей обработки.

Отчёт строится для комбинации:

```text
repository + branch
```

В отчёт входят все завершённые Qwen Code sessions, привязанные к данной Git-ветке.

### 1.1. Markdown

Пример структуры `report.md`:

```markdown
# feature/PROJ-1234-add-cache

Repository: my-project
Branch: feature/PROJ-1234-add-cache
Sessions: 4
Observation span: 2026-09-17 10:20 — 2026-09-18 14:45

## Cost by model

| Model | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---:|---:|---:|---:|---:|---:|
| routerai/deepseek/deepseek-v4-flash | 42 | 1,200,000 | 800,000 | 15,000 | 3,000 | 7.38 |
| routerai/qwen/qwen3.8-flash | 15 | 450,000 | 300,000 | 8,000 | 1,200 | 7.61 |

Total cost: 14.99

## Cost by agent

| Agent | Runs | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---:|---:|---:|---:|---:|---:|
| main | — | 49 | ... | ... | ... | ... | ... |
| general-purpose | 3 | 8 | ... | ... | ... | ... | ... |

## Sessions

| Session | Title | Models | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 18697f75… | Подготовка технического задания | deepseek-v4-flash | ... | ... | ... | ... | ... | ... |
| a1b2c3d4… | Реализация API | qwen3.8-flash | ... | ... | ... | ... | ... | ... |
| f9e8d7c6… | Написание тестов | deepseek-v4-flash, qwen3.8-flash | ... | ... | ... | ... | ... | ... |

## Overall usage

Requests: ...
Input tokens: ...
Cached input tokens: ...
Output tokens: ...
Reasoning tokens: ...
Total tokens: ...
API duration: ...
Tool calls: ...
MCP calls: ...
Subagent runs: ...

## Session details

### Подготовка технического задания

Session: 18697f75-...
Started: ...
Ended: ...
Cost: ...

Models:
...

Agents:
...

Tools:
...

MCP:
...

Subagents:
...

### Реализация API

...

## Tools

| Tool | Calls | Success | Failed | Duration |
|---|---:|---:|---:|---:|
| run_shell_command | ... | ... | ... | ... |
| glob | ... | ... | ... | ... |

## MCP

| Server | Tool | Calls | Success | Failed | Duration |
|---|---|---:|---:|---:|---:|
| gitlab | get_mcp_server_version | ... | ... | ... | ... |

## Subagents

| Agent | Runs | Requests | Input | Cached | Output | Reasoning | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| general-purpose | ... | ... | ... | ... | ... | ... | ... |

## Data quality / warnings

...
```

Финансовая информация должна находиться в начале отчёта.

Секция `Sessions` должна позволять быстро определить, сколько ресурсов было потрачено на разные виды работы — например, подготовку ТЗ, исследование, реализацию и тестирование.

### 1.2. JSON

Базовая структура `report.json`:

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-09-18T12:00:00Z",

  "task": {
    "repository": "my-project",
    "branch": "feature/PROJ-1234-add-cache",
    "session_count": 4,
    "observation_started_at": "...",
    "observation_ended_at": "..."
  },

  "totals": {
    "requests": 57,

    "tokens": {
      "input": 1650000,
      "cached_input": 1100000,
      "output": 23000,
      "reasoning": 4200,
      "total": 1673000
    },

    "cost": 14.99,
    "api_duration_ms": 180000,
    "tool_calls": 47,
    "mcp_calls": 8,
    "subagent_runs": 3
  },

  "models": [],
  "agents": [],
  "tools": [],
  "mcp": [],
  "sessions": [],
  "warnings": []
}
```

### 1.3. Представление session

Каждая session содержит человекочитаемый `title`.

```json
{
  "id": "18697f75-6ead-472a-b700-18afb74ab2a2",
  "title": "Подготовка технического задания",
  "started_at": "...",
  "ended_at": "...",

  "requests": 17,

  "tokens": {
    "input": 410000,
    "cached_input": 250000,
    "output": 6000,
    "reasoning": 1200,
    "total": 416000
  },

  "cost": 3.41,

  "models": [
    {
      "name": "routerai/deepseek/deepseek-v4-flash",
      "requests": 12,
      "tokens": {
        "input": 300000,
        "cached_input": 200000,
        "output": 4000,
        "reasoning": 900,
        "total": 304000
      },
      "cost": 2.11
    }
  ],

  "agents": [],
  "tools": {},
  "mcp": {},
  "subagents": []
}
```

### 1.4. Агрегация по моделям

```json
{
  "name": "routerai/deepseek/deepseek-v4-flash",
  "requests": 42,

  "tokens": {
    "input": 1000000,
    "cached_input": 600000,
    "output": 20000,
    "reasoning": 5000,
    "total": 1020000
  },

  "cost": 6.24
}
```

### 1.5. Агрегация по agents

```json
{
  "name": "general-purpose",
  "runs": 3,
  "requests": 8,

  "tokens": {
    "input": 100000,
    "cached_input": 70000,
    "output": 3000,
    "reasoning": 500,
    "total": 103000
  },

  "models": [
    {
      "name": "routerai/deepseek/deepseek-v4-flash",
      "requests": 8,
      "tokens": {
        "input": 100000,
        "cached_input": 70000,
        "output": 3000,
        "reasoning": 500,
        "total": 103000
      },
      "cost": 0.636
    }
  ],

  "cost": 0.636
}
```

---

# 2. Назначение

Разработать кроссплатформенный CLI-инструмент `qwencode-branch-stats` (краткое имя из консоли — `qbs`) на Python 3 для сбора и агрегации метрик использования Qwen Code.

Инструмент должен показывать:

- Qwen sessions, использованные при работе в Git branch;
    
- title каждой session;
    
- использованные модели;
    
- количество LLM requests;
    
- input tokens;
    
- cached tokens;
    
- output tokens;
    
- reasoning/thought tokens;
    
- стоимость;
    
- стоимость по моделям;
    
- стоимость по sessions;
    
- стоимость main agent;
    
- стоимость по именам subagents;
    
- tool calls;
    
- MCP calls;
    
- subagent runs;
    
- API/tool/subagent durations.
    

# 3. Целевая среда

Поддерживаемые ОС:

- Linux;
    
- Windows;
    
- macOS.
    

Реализация:

```text
Python 3
```

CLI:

```text
qwencode-branch-stats
```

Краткое имя команды для использования из консоли:

```text
qbs
```

Обе команды эквивалентны. Python package предоставляет entry points:

```toml
[project.scripts]
qwencode-branch-stats = "qwencode_branch_stats.cli:main"
qbs = "qwencode_branch_stats.cli:main"
```

## 3.1. Версионирование

Git tags в репозитории `qwencode-branch-stats` соответствуют версии Qwen Code,
для которой предназначен релиз. Например, tag `0.1.0` означает поддержку
Qwen Code 0.1.0.

Версии в `pyproject.toml` и `__version__` должны совпадать с текущим tag.
При изменении форматов Qwen Code в новой версии Qwen Code выпускается релиз
с tag, соответствующим этой версии.

# 4. Источники данных

`qwencode-branch-stats` работает непосредственно с локальными файлами Qwen Code и Git.

Основные источники:

```text
Qwen Code
│
├── token-usage-YYYY-MM.jsonl
│      models / tokens / API duration / source
│
├── chats/<session>.jsonl
│      session title / main tools / MCP
│
├── subagents/<session>/
│   ├── *.meta.json
│   │      subagent runs / hierarchy / status
│   └── *.jsonl
│          subagent tools
│
└── settings.json
       model pricing
```

Дополнительно `SessionEnd` hook сохраняет:

```text
session ID → repository → branch
```

Команда `qwen sessions list` для сбора метрик не используется.

# 5. Привязка session к Git branch

При завершении Qwen session выполняется hook:

```text
qbs hook session-end
```

Hook получает session ID и определяет Git repository и branch в момент завершения session.

Сохраняемая запись:

```json
{
  "schema_version": 1,
  "session_id": "18697f75-6ead-472a-b700-18afb74ab2a2",
  "repo": "/work/project",
  "branch": "feature/PROJ-1234-add-cache",
  "captured_at": "2026-09-18T00:01:23Z"
}
```

Git repository определяется через:

```text
git rev-parse --show-toplevel
```

Branch:

```text
git branch --show-current
```

Имя branch сохраняется как есть.

Hook занимается только фиксацией связи session с Git context. Парсинг Qwen telemetry и расчёт метрик выполняются при построении отчёта.

# 6. Session mappings

Необходимо локальное хранилище mappings:

```text
session_id
repository
branch
captured_at
```

Хранилище должно поддерживать несколько одновременно работающих Qwen sessions.

Формат persistence является внутренней деталью реализации. Может использоваться JSONL или SQLite.

# 7. Идентификация repository

Отчёт строится для:

```text
repository + branch
```

Repository определяется из текущего Git working tree.

Внутренний идентификатор repository — нормализованный полный путь из
`git rev-parse --show-toplevel`. Он сохраняется в session mappings и должен
позволять различать разные repositories с одинаковым именем branch.

В финальном отчёте (`report.md` и `report.json`) в качестве repository
отображается только название папки проекта — папки, в которой находится
`.git`. Полный путь repository в отчёт не попадает.

# 8. Session metadata и title

Основной transcript session находится в файле вида:

```text
~/.qwen/projects/<project>/chats/<session-id>.jsonl
```

Из session необходимо получить:

```text
session ID
title
started_at
ended_at
```

## 8.1. Title

Человекочитаемое название Qwen session берётся из сохранённого Qwen custom title.

В transcript необходимо искать записи:

```text
type = system
subtype = custom_title
```

Если session переименовывалась несколько раз, используется последнее сохранённое название.

Результат нормализуется:

```json
{
  "title": "Подготовка технического задания"
}
```

Если custom title отсутствует:

```json
{
  "title": null
}
```

`qwencode-branch-stats` не генерирует название session самостоятельно.

Title используется в Markdown и JSON для различения назначения sessions.

# 9. Token usage

Основной источник:

```text
~/.qwen/usage/token-usage-YYYY-MM.jsonl
```

Пример:

```json
{
  "schemaVersion": 1,
  "id": "a687e101-09cb-4fd4-a47c-a7102fed95d6",
  "timestamp": "2026-09-17T23:33:03.728Z",
  "sessionId": "18697f75-6ead-472a-b700-18afb74ab2a2",
  "model": "routerai/deepseek/deepseek-v4-flash",
  "authType": "openai",
  "source": "general-purpose",
  "inputTokens": 23984,
  "outputTokens": 235,
  "cachedTokens": 0,
  "thoughtsTokens": 71,
  "totalTokens": 24219,
  "apiDurationMs": 8208
}
```

Из записи используются:

```text
id
timestamp
sessionId
model
source
inputTokens
outputTokens
cachedTokens
thoughtsTokens
totalTokens
apiDurationMs
```

Каждая запись соответствует одному LLM request.

# 10. Модели

Модель определяется для каждого LLM request отдельно.

Одна session может использовать несколько моделей.

Основной ключ агрегации:

```text
sessionId + source + model
```

На уровне session необходимо получить:

```text
models[]
```

На уровне всего отчёта необходимо получить общую агрегацию:

```text
models[]
```

# 11. Agents и subagents

В `token-usage` поле:

```text
source
```

используется для определения источника LLM request.

Например:

```text
main
general-purpose
```

Расходы subagents агрегируются по имени `source`.

Не требуется определять, какой конкретный экземпляр subagent с одинаковым именем выполнил конкретный LLM request.

## 11.1. Subagent runs

Qwen хранит subagent metadata в каталоге:

```text
~/.qwen/projects/<project>/subagents/<parent-session-id>/
```

Для каждого запуска доступны:

```text
<agent>.meta.json
<agent>.jsonl
```

Из `.meta.json` используются необходимые структурные поля:

```text
agentId
agentType
parentSessionId
parentAgentId
createdAt
lastUpdatedAt
status
subagentName
resumeCount
depth
```

Количество subagent runs определяется по metadata.

## 11.2. Subagent hierarchy

Связи subagents строятся из:

```text
parentSessionId
parentAgentId
depth
```

## 11.3. Subagent tools

Subagent transcript используется для подсчёта вызовов tools.

Из function calls требуется извлекать:

```text
call ID
tool name
```

# 12. Main tools

Main session transcript используется для получения Qwen tool telemetry.

Основное событие:

```text
qwen-code.tool_call
```

Из события нужны:

```text
call_id
function_name
duration_ms
status
execution_status
success
error_type
tool_type
```

На уровне session и всего отчёта строится статистика:

```json
{
  "run_shell_command": {
    "calls": 12,
    "success": 10,
    "failed": 2,
    "duration_ms": 15342
  }
}
```

# 13. MCP

MCP calls определяются по:

```text
tool_type = mcp
```

Например:

```text
mcp__gitlab__get_mcp_server_version
```

нормализуется:

```json
{
  "server": "gitlab",
  "tool": "get_mcp_server_version"
}
```

Необходима агрегация по:

```text
MCP server
MCP tool
```

MCP calls также входят в общее количество tool calls.

# 14. Pricing

Pricing читается непосредственно из Qwen `settings.json`.

Пример:

```json
{
  "modelPricing": {
    "routerai/deepseek/deepseek-v4-flash": {
      "inputPerMillionTokens": 6,
      "outputPerMillionTokens": 12
    },
    "routerai/qwen/qwen3.8-flash": {
      "inputPerMillionTokens": 16,
      "outputPerMillionTokens": 51
    }
  }
}
```

Стоимость usage record:

```text
input_cost =
    inputTokens
    / 1_000_000
    * inputPerMillionTokens

output_cost =
    outputTokens
    / 1_000_000
    * outputPerMillionTokens

cost =
    input_cost + output_cost
```

После расчёта стоимости каждого request выполняется агрегация:

```text
request
  ↓
session + model + agent
  ↓
session
  ↓
branch
```

Если pricing модели отсутствует, стоимость соответствующего usage должна быть отмечена как неизвестная.

# 15. Cached и reasoning tokens

`cachedTokens` сохраняются как отдельная метрика.

При текущей структуре `modelPricing` отдельная цена cached tokens отсутствует, поэтому стоимость рассчитывается на основе `inputTokens`.

`thoughtsTokens` сохраняются в отчёте как:

```text
reasoning
```

Они не прибавляются второй раз к `outputTokens` при расчёте стоимости.

# 16. Privacy

`qwencode-branch-stats` собирает метрики, а не содержимое Qwen conversations.

В финальные отчёты не должны попадать:

- prompts;
    
- assistant response text;
    
- reasoning text;
    
- tool arguments;
    
- tool results;
    
- содержимое файлов;
    
- shell commands/output;
    
- MCP payloads;

- API keys;

- credentials;

- полные пути repository на диске.


Допускаются необходимые metadata:

- session title;

- model names;

- agent names;

- tool names;

- MCP server/tool names;

- Git repository в виде названия папки проекта и branch;
    
- timestamps;
    
- statuses;
    
- числовые метрики.
    

Парсеры должны создавать нормализованные структуры из нужных полей исходных записей, а не сохранять исходные Qwen events целиком.

# 17. CLI

Основная команда:

```text
qbs report
```

По умолчанию отчёты сохраняются в папку `.qbs/` в текущем каталоге
(переопределяется параметром `--output-dir`).

Алгоритм:

```text
current repository + branch
             │
             ▼
      session mappings
             │
             ▼
         session IDs
             │
     ┌───────┼─────────┐
     ▼       ▼         ▼
   usage   chats    subagents
     │       │         │
     └───────┼─────────┘
             │
        modelPricing
             │
             ▼
        aggregation
             │
       ┌─────┴─────┐
       ▼           ▼
  report.json  report.md
```

Также необходима команда, используемая Qwen hook:

```text
qbs hook session-end
```

Рекомендуется диагностическая команда:

```text
qbs doctor
```

# 18. Идемпотентность

`report` строит snapshot из исходных данных.

Повторный запуск:

```text
qbs report
```

при неизменных source data должен давать те же totals.

Для deduplication token usage используется:

```text
usage.id
```

Для tool calls при наличии используется:

```text
call_id
```

# 19. Работа с JSONL

JSONL должен обрабатываться потоково.

В первую очередь выполняется фильтрация по нужным:

```text
sessionId
```

Парсер должен корректно работать с большими usage/transcript файлами.

# 20. Internal domain model

Рекомендуемые внутренние структуры:

```text
SessionMapping
SessionInfo
UsageRecord
TokenMetrics
ModelMetrics
AgentMetrics
ToolMetrics
McpMetrics
SubagentRun
ModelPricing
SessionMetrics
TaskMetrics
Warning
```

Пример:

```text
SessionInfo
├── id
├── title
├── started_at
└── ended_at
```

```text
TaskMetrics
├── repository
├── branch
├── totals
├── models[]
├── agents[]
├── tools[]
├── mcp[]
└── sessions[]
```

Report generators получают уже агрегированный `TaskMetrics`.

# 21. Qwen adapters

Qwen-specific parsing необходимо отделить от aggregation logic.

Рекомендуемая структура:

```text
src/qwencode_branch_stats/
│
├── cli.py
├── git.py
├── mappings.py
├── pricing.py
├── aggregation.py
├── models.py
│
├── qwen/
│   ├── paths.py
│   ├── usage.py
│   ├── sessions.py
│   ├── tools.py
│   ├── subagents.py
│   └── settings.py
│
├── hooks/
│   └── session_end.py
│
└── reports/
    ├── json_report.py
    └── markdown_report.py
```

# 22. Канонические источники метрик

Использовать следующую схему:

```text
Session → repository/branch
    SessionEnd hook

Session title/time
    chat JSONL

Models/tokens/API duration
    token-usage-YYYY-MM.jsonl

Pricing
    settings.json → modelPricing

Main tools/MCP
    chat JSONL

Subagent runs/hierarchy
    subagent *.meta.json

Subagent tools
    subagent *.jsonl
```

# 23. Data quality

При невозможности получить часть данных отчёт должен содержать warning.

Примеры:

```text
pricing_missing
session_mapping_missing
transcript_missing
subagent_metadata_missing
malformed_jsonl
unknown_qwen_schema
```

Warning должен присутствовать в `report.json` и иметь человекочитаемое представление в `report.md`.

# 24. Timing

В отчёте учитываются:

```text
session start/end
API duration
tool duration
subagent duration
```

Для всего набора sessions можно вычислять:

```text
observation_started_at =
    min(session.started_at)

observation_ended_at =
    max(session.ended_at)
```

и показывать:

```text
observation_span
```

# 25. Кроссплатформенность

Поддерживаются:

```text
Linux
Windows
macOS
```

Необходимо учитывать:

- различия пользовательских home/data directories;
    
- Windows paths;
    
- Unicode paths;
    
- запуск Git через Python subprocess;
    
- корректную работу с UTF-8 JSON/JSONL;
    
- несколько параллельных Qwen processes.
    

Пути Qwen должны определяться централизованно в `qwen/paths.py`.

# 26. Тестирование

Минимальные сценарии:

1. одна session с одной моделью;
    
2. одна session с несколькими моделями;
    
3. несколько sessions одной branch;
    
4. несколько sessions с разными titles;
    
5. переименование session несколько раз — используется последний `custom_title`;
    
6. session без custom title;
    
7. main + subagent;
    
8. несколько subagents одного имени;
    
9. nested subagents;
    
10. subagent tools;
    
11. native tools;
    
12. MCP tools;
    
13. failed tool call;
    
14. cached tokens;
    
15. reasoning tokens;
    
16. missing model pricing;
    
17. malformed JSONL;
    
18. параллельные Qwen sessions;
    
19. Unicode paths;
    
20. Windows paths;
    
21. повторная генерация report.
    

# 27. Privacy tests

Тестовые Qwen fixtures должны содержать специальные значения:

```text
SECRET_PROMPT_123
SECRET_RESPONSE_123
SECRET_REASONING_123
SECRET_TOOL_ARGUMENT_123
SECRET_TOOL_RESULT_123
SECRET_API_KEY_123
```

После генерации отчёта ни одно из этих значений не должно присутствовать в:

```text
report.json
report.md
```

При этом тестовый:

```text
SESSION_TITLE_123
```

должен присутствовать, если он сохранён как Qwen custom title.

# 28. Acceptance criteria

Пользователь работает в одной Git branch и проводит несколько Qwen sessions, например:

```text
Подготовка технического задания
Исследование архитектуры
Реализация
Написание тестов
```

Sessions именуются средствами Qwen.

При завершении каждой session hook фиксирует:

```text
sessionId → repository → branch
```

После выполнения:

```text
qbs report
```

пользователь получает общую стоимость branch:

```text
Branch
│
├── total cost
│
├── models
│   ├── model A → tokens / requests / cost
│   └── model B → tokens / requests / cost
│
├── agents
│   ├── main → tokens / requests / cost
│   └── general-purpose → runs / tokens / requests / cost
│
└── sessions
    ├── Подготовка технического задания
    │      models / tokens / cost
    │
    ├── Исследование архитектуры
    │      models / tokens / cost
    │
    ├── Реализация
    │      models / tokens / cost
    │
    └── Написание тестов
           models / tokens / cost
```

Отчёт также содержит статистику tools, MCP и subagents.

Значения в `report.json` и `report.md` должны быть согласованы.

# 29. MVP

В MVP входят:

```text
SessionEnd hook
session → repository/branch mapping
Qwen custom title parsing
token-usage parser
modelPricing parser
multi-model sessions
main/subagent usage aggregation
per-session cost
per-model cost
per-agent cost
native tool statistics
MCP statistics
subagent run statistics
subagent tool statistics
report.json
report.md
privacy filtering
data-quality warnings
cross-platform support
automated tests
```

# 30. Итоговая архитектура

```text
                       Qwen Code
                           │
                     SessionEnd
                           │
                           ▼
                 session/repo/branch
                           │
                           │
        ┌──────────────────┼───────────────────┐
        │                  │                   │
        ▼                  ▼                   ▼
 token-usage JSONL    session JSONL       subagents/
        │             title/tools/MCP     meta + JSONL
        │                  │                   │
        └──────────────────┼───────────────────┘
                           │
                     settings.json
                      modelPricing
                           │
                           ▼
                    ┌─────────────┐
                    │     qbs     │
                    │ aggregation │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
               report.json    report.md
```

Основной принцип реализации:

**Qwen Code уже хранит необходимые usage и session artifacts. `qwencode-branch-stats` не создаёт собственную telemetry-систему, а связывает Qwen sessions с Git branch в момент SessionEnd и затем агрегирует локальные данные Qwen в отчёт по стоимости, моделям, sessions, agents, tools и MCP.**
