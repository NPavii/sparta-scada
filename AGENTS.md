# Sparta SCADA — инструкция для AI-агентов

> Статус: выполнены **Этап 0**, **Этап 1** и **Этап 2**. Инфраструктура Docker поднимается, собраны компоненты Rapid SCADA 6, создан и развёрнут демо-проект `SpartaDemo` с OPC UA-линией и PostgreSQL-архивом. Проверено end-to-end прохождение тегов от `opc-plc` через Communicator + Server в PostgreSQL (`mod_arc_postgre_sql.curcopy_current` / `mincopy_historical`). Создан и проверен `sparta-ai-service` (Python/FastAPI): читает текущие/исторические данные, выполняет детекцию аномалий (z-score/EWMA) и простой линейный прогноз. Исходный код `Sparta.Mcp` и `ModERP` пока отсутствует.

---

## 1. Общее описание проекта

**Sparta SCADA** — кастомная локальная SCADA-система, строящаяся поверх open-source платформы **Rapid SCADA 6** (Apache License 2.0). Система предназначена для:

- сбора данных с промышленного оборудования по протоколу **OPC UA**;
- локальной ИИ-аналитики данных оборудования;
- автоматической выдачи заявок на обслуживание оборудования во внешнюю **ERP-систему**.

Ключевое архитектурное решение: код ядра Rapid SCADA не изменяется. Все доработки реализуются через штатные точки расширения — модули Server (`Mod*`), драйверы Communicator (`Drv*`) и плагины Webstation (`Plg*`).

---

## 2. Текущее состояние репозитория

```
Sparta/
├── AGENTS.md                              # этот файл
├── README.md                              # документация проекта
├── docker-compose.yml                     # PostgreSQL + demo OPC UA server + Sparta.AI
├── .env.example                           # шаблон переменных окружения
├── .gitignore                             # исключения для Git
├── scada-agent-prompt.md                  # техническое задание
├── docs/                                  # документация (пусто)
├── migrations/
│   └── 001_create_work_orders.sql         # служебные таблицы заявок
├── scada-config/
│   ├── SpartaDemo/                        # демо-проект Rapid SCADA (BaseXML + Instances)
│   └── runtime/                           # развёрнутый runtime (генерируется)
├── scripts/
│   ├── start-infrastructure.ps1           # запуск инфраструктуры (PowerShell)
│   ├── start-infrastructure.sh            # запуск инфраструктуры (Bash)
│   ├── start-scada-runtime.bat            # запуск ScadaServer + ScadaComm
│   ├── stop-scada-runtime.bat             # остановка ScadaServer + ScadaComm
│   ├── copy-runtime-binaries.sh           # копирование собранных бинарников в runtime
│   ├── deploy-scada-config/               # C#-утилита: BaseXML → BaseDAT + deploy
│   ├── verify-stage1.py                   # проверка потока тегов в PostgreSQL
│   └── verify-stage2.py                   # проверка Sparta.AI сервиса
└── src/
    ├── ModERP/                            # C# модуль ScadaServer (пусто)
    ├── Sparta.AI/                         # sparta-ai-service (Python/FastAPI)
    │   ├── app/
    │   │   ├── main.py                    # FastAPI endpoints
    │   │   ├── config.py                  # конфигурация через env
    │   │   ├── db.py                      # PostgreSQL (psycopg3)
    │   │   ├── analytics.py               # z-score / EWMA / прогноз
    │   │   └── channels.py                # метаданные каналов из Cnl.xml
    │   ├── Dockerfile
    │   └── requirements.txt
    └── Sparta.Mcp/                        # sparta-mcp-server (пусто)
```

После Этапа 0 добавлены:

- `docker-compose.yml` с сервисами `postgres` (PostgreSQL 16) и `opc-plc` (Microsoft OPC PLC simulator);
- `.env.example` — шаблон переменных окружения (реальный `.env` не коммитится);
- SQL-миграция `001_create_work_orders.sql` для таблиц `work_orders` и `work_order_status_history`;
- скрипты запуска инфраструктуры для Windows (`ps1`) и Unix (`sh`).

После Этапа 1 добавлены:

- `scada-config/SpartaDemo/` — демо-проект Rapid SCADA: линия OPC UA, устройство `OPC PLC`, 6 каналов (StepUp, AlternatingBoolean, RandomSignedInt32, DipData, SpikeData, SlowUInt1), PostgreSQL-архивы (`CurCopy`, `MinCopy`, `EventsCopy`);
- `scripts/deploy-scada-config/` — утилита на C# для развёртывания проекта: загрузка BaseXML, конвертация в BaseDAT, копирование конфигураций приложений, создание `ScadaInstanceConfig.xml`;
- `scripts/copy-runtime-binaries.sh` — копирование собранных DLL/EXE Rapid SCADA, драйверов и модулей в `scada-config/runtime/Instances/Default/{ScadaServer,ScadaComm}`;
- `scripts/start-scada-runtime.bat` / `stop-scada-runtime.bat` — запуск и остановка ScadaServer + ScadaComm;
- `scripts/verify-stage1.py` — проверка наличия текущих и исторических данных в PostgreSQL.

После Этапа 2 добавлены:

- `src/Sparta.AI/` — сервис `sparta-ai-service` на Python/FastAPI: чтение текущих и исторических данных из PostgreSQL, детекция аномалий (z-score, EWMA), простой линейный прогноз;
- `src/Sparta.AI/Dockerfile` и сервис `sparta-ai-service` в `docker-compose.yml`;
- `scripts/verify-stage2.py` — проверка REST API и свежести данных.

Пока отсутствуют:

- исходный код `Sparta.Mcp` и `ModERP`;
- тесты;
- Webstation-конфигурация и мнемосхемы.

---

## 3. Планируемая технологическая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      Sparta SCADA                           │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Rapid SCADA 6 (upstream, Apache 2.0)     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │  │
│  │  │Communicator│  │   Server   │  │   Webstation   │   │  │
│  │  │ + DrvOpcUa │→ │ + ModERP   │→ │  схемы/тренды  │   │  │
│  │  │            │  │ (+ ModAI)  │  │  (+ ИИ-панель) │   │  │
│  │  └────────────┘  └────────────┘  └────────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────┼────────────────────────────┐   │
│  │      PostgreSQL — архивы Rapid SCADA + служебные таблицы│  │
│  └─────────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────┼────────────────────────────┐   │
│  │     Внешние сервисы Sparta                              │   │
│  │  ┌──────────────────┐   ┌────────────────────────┐    │   │
│  │  │ sparta-ai-service│   │  sparta-mcp-server     │    │   │
│  │  │ Python, FastAPI  │   │  Python, FastMCP       │    │   │
│  │  │  • чтение архивов│   │  • tools: get_tags,    │    │   │
│  │  │  • детекция      │   │    get_history,        │    │   │
│  │  │    аномалий      │   │    analytics_summary,  │    │   │
│  │  │  • прогнозирование│  │    create_work_order   │    │   │
│  │  │  • локальная LLM │   │  • ресурсы scada://... │    │   │
│  │  │    (Ollama)      │   │                        │    │   │
│  │  └──────────────────┘   └────────────────────────┘    │   │
│  │  ┌──────────────────┐   ┌────────────────────────┐    │   │
│  │  │ ModERP (C#)      │   │ ERP-система (внешняя)  │    │   │
│  │  │ модуль Rapid     │   │ интеграция по REST API │    │   │
│  │  │ SCADA Server     │   │                        │    │   │
│  │  └──────────────────┘   └────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  Оборудование:  ПЛК/контроллеры ←OPC UA→ DrvOpcUa          │
└─────────────────────────────────────────────────────────────┘
```

### Планируемые компоненты

| Компонент | Стек | Назначение |
|-----------|------|------------|
| `ModERP` | C# / .NET 6+ | Модуль Rapid SCADA Server: обработка триггеров, формирование заявок на обслуживание, интеграция с ERP по REST, очередь невыгруженных заявок, опрос статусов. |
| `sparta-ai-service` | Python 3.11+ / FastAPI | Чтение текущих и исторических данных из PostgreSQL, детекция аномалий, прогнозирование, генерация текстовых отчётов, опционально — локальная LLM через Ollama. |
| `sparta-mcp-server` | Python / FastMCP | MCP-сервер для LLM-агентов: инструменты чтения тегов, истории, аналитики и создания заявок. |
| `scada-config` | XML-конфиги Rapid SCADA | Демо-проект: линия связи OPC UA, каналы, мнемосхема, настройка PostgreSQL-архива. |
| `migrations` | SQL | Миграции PostgreSQL для служебных таблиц (заявки, статусы). |
| `docker-compose.yml` | Docker Compose | Инфраструктура: PostgreSQL, AI-сервис, MCP-сервер, опционально Ollama и demo OPC UA server. |

---

## 4. Планируемая структура репозитория

```
sparta-scada/
├── README.md
├── docker-compose.yml
├── AGENTS.md             # этот файл
├── docs/                 # архитектура, API, инструкции (рус.)
├── scada-config/         # экспорт конфигурации Rapid SCADA
├── src/
│   ├── ModERP/           # C# модуль ScadaServer
│   ├── Sparta.AI/        # sparta-ai-service (Python/FastAPI)
│   └── Sparta.Mcp/       # sparta-mcp-server (Python/FastMCP)
├── migrations/           # SQL-миграции PostgreSQL
└── scripts/              # скрипты сборки/запуска
```

> Пока эти директории не созданы. Реализация планируется по этапам, описанным в `scada-agent-prompt.md`.

---

## 5. Планируемый технологический стек

- **C# / .NET 6+** — модули Rapid SCADA (`ModERP`).
- **Python 3.11+** — сервисы `sparta-ai-service` и `sparta-mcp-server`.
- **FastAPI** — REST API `sparta-ai-service`.
- **FastMCP** — MCP-сервер `sparta-mcp-server`.
- **PostgreSQL** — единственная база данных (архивы Rapid SCADA + служебные таблицы).
- **OPC UA** — протокол сбора данных с оборудования.
- **Rapid SCADA 6** — ядро SCADA (upstream, без форка).
- **Docker / Docker Compose** — локальное развёртывание.
- **Ollama** — локальная LLM (опционально, за фичефлагом).

---

## 6. Планируемый порядок разработки

Этапы из `scada-agent-prompt.md`:

1. **Этап 0 — каркас**: репозиторий, `docker-compose` с PostgreSQL и demo OPC UA server, скелет `README.md`. ✅
2. **Этап 1 — данные**: демо-конфигурация Rapid SCADA с OPC UA, PostgreSQL-архив, проверка потока тегов. ✅ (Проверено: `opc-plc` → `ScadaComm`/`DrvOpcUa` → `ScadaServer`/`ModArcPostgreSql` → `PostgreSQL`.)
3. **Этап 2 — ИИ-сервис**: `Sparta.AI` с чтением тегов/истории и базовой детекцией аномалий. ✅ (Проверено: `GET /tags`, `GET /history`, `POST /analyze`, `POST /predict`; `scripts/verify-stage2.py` проходит.)
4. **Этап 3 — MCP-сервер**: `Sparta.Mcp` поверх `Sparta.AI`.
5. **Этап 4 — ERP-модуль**: `ModERP` с очередью заявок + эмулятор ERP в `docker-compose`.
6. **Этап 5 — прогнозирование и LLM-отчёты** (Ollama, за фичефлагом).
7. **Этап 6 — полировка**: документация, примеры, `docker-compose` «всё-в-одном».

Правило перехода между этапами: этап считается готовым только после end-to-end проверки (запуск + тест/команда), а не только после написания кода.

---

## 7. Актуальные команды сборки и запуска

### Этап 0 — инфраструктура

```bash
# Копирование шаблона переменных окружения
cp .env.example .env

# Запуск PostgreSQL и demo OPC UA server
./scripts/start-infrastructure.sh        # Linux/macOS/Git Bash
# или
./scripts/start-infrastructure.ps1       # Windows PowerShell

# Проверка состояния сервисов
docker compose ps

# Просмотр логов
docker compose logs -f

# Подключение к PostgreSQL
psql -h localhost -U scada -d scada

# Проверка доступности OPC UA demo-сервера
# Endpoint: opc.tcp://localhost:4840/
```

### Этап 1 — сборка и запуск Rapid SCADA

```bash
# 1. Инфраструктура должна быть запущена
docker compose up -d

# 2. Сборка Rapid SCADA (однократно или после обновления исходников)
dotnet build scada-v6-master/scada-v6-master/ScadaCommon/ScadaCommon.sln -c Release
dotnet build scada-v6-master/scada-v6-master/ScadaServer/ScadaServer/ScadaServer.sln -c Release
dotnet build scada-v6-master/scada-v6-master/ScadaComm/ScadaComm/ScadaComm.sln -c Release
dotnet build scada-v6-master/scada-v6-master/ScadaComm/OpenDrivers/OpenDrivers.sln -c Release
dotnet build scada-v6-master/scada-v6-master/ScadaServer/OpenModules/OpenModules.sln -c Release

# 3. Сборка утилиты развёртывания (первый раз)
dotnet build scripts/deploy-scada-config/deploy-scada-config.csproj -c Release

# 4. Развёртывание конфигурации и бинарников
rm -rf scada-config/runtime
dotnet scripts/deploy-scada-config/bin/Release/net10.0-windows/deploy-scada-config.dll \
  scada-config/SpartaDemo/SpartaDemo.rsproj scada-config/runtime
bash scripts/copy-runtime-binaries.sh

# 5. Запуск ScadaServer + ScadaComm (открывает два окна cmd)
scripts/start-scada-runtime.bat

# 6. Проверка потока тегов в PostgreSQL
python scripts/verify-stage1.py

# Остановка
scripts/stop-scada-runtime.bat
```

### Этап 2 — Sparta.AI сервис

```bash
# Вариант 1: в Docker (сервис уже описан в docker-compose.yml)
docker compose up --build -d sparta-ai-service
docker compose logs -f sparta-ai-service

# Вариант 2: локально для разработки
cd src/Sparta.AI
python -m venv .venv
.venv/Scripts/activate        # Windows Git Bash
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Проверка
python scripts/verify-stage2.py
# OpenAPI: http://localhost:8000/docs
```

Основные endpoint'ы:

- `GET /health` — состояние сервиса и БД;
- `GET /tags` — текущие значения каналов;
- `GET /history?cnl_num=101&limit=100` — история (также `tag_code=StepUp`);
- `POST /analyze` — детекция аномалий (`zscore` / `ewma`);
- `POST /predict` — простой линейный прогноз.

### Будущие команды (будут актуализироваться по мере разработки)

```bash
# Запуск MCP-сервера локально (Этап 3)
cd src/Sparta.Mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m sparta_mcp

# Сборка ModERP (Этап 4)
cd src/ModERP
dotnet build
```

---

## 8. Стиль кода и соглашения

Из `scada-agent-prompt.md`:

- **Язык кода и комментариев**: английский.
- **Документация**: русский (README, docs, AGENTS.md).
- **Идентификаторы и коммиты**: английский.
- **Коммиты**: conventional commits — `feat:`, `fix:`, `docs:` и т.д.
- **Лицензия**: Apache 2.0 с сохранением уведомлений Rapid SCADA.
- **Зависимости**: только open-source, только локальные сервисы, без облачных API.
- **Конфигурация**: без hardcoded секретов — только конфиги и переменные окружения.
- **Логирование**: structured logs во всех компонентах.
- **Отказоустойчивость**: падение AI-сервиса или ERP не должно останавливать сбор данных SCADA.

### C# (`ModERP`)

- Ориентироваться на существующие модули в исходниках Rapid SCADA: `ScadaServer/Modules`.
- Конфигурация модуля — в `ModERP.xml`.
- Модуль должен реализовывать интерфейсы Rapid SCADA Server.

### Python (`sparta-ai-service`, `sparta-mcp-server`)

- Конфигурация через `.env` и/или `config.yaml`.
- REST API `sparta-ai-service` должен предоставлять OpenAPI-документацию.
- `sparta-mcp-server` по умолчанию read-only; создание заявок (`create_work_order`) требует явного флага в конфиге.

---

## 9. Планируемая стратегия тестирования

- **Unit-тесты** на бизнес-логику `ModERP`:
  - правила триггеров (условие канала → заявка);
  - очередь невыгруженных заявок;
  - retry/backoff ERP-клиента.
- **Unit-тесты** на `Sparta.AI`:
  - детекция аномалий (z-score, EWMA);
  - чтение тегов/истории из PostgreSQL.
- **Интеграционные проверки**: end-to-end прохождение тега от OPC UA demo-сервера через Rapid SCADA в PostgreSQL и далее в AI-сервис.
- **Ручная проверка**: запуск `docker-compose` на чистой машине по `README.md`.

---

## 10. Соображения безопасности

- Все LLM-вычисления и хранение данных — **локально**, без облачных сервисов.
- MCP-сервер по умолчанию работает в read-only режиме; инструмент `create_work_order` включать только явным флагом.
- Секреты и параметры подключения — только через переменные окружения и конфиги, никаких hardcoded значений.
- ERP-интеграция через REST API с retry/backoff, таймаутами и persistent-очередью на случай недоступности ERP.
- OPC UA — промышленный протокол; при подключении к реальному оборудованию учитывать требования сетевой безопасности и изоляции промышленной сети.

---

## 11. Полезные ссылки и источники истины

- Rapid SCADA 6: https://github.com/RapidScada/scada-v6
- Документация Rapid SCADA: https://rapidscada.net/docs/en/latest/
- Лицензия: Apache License 2.0

---

## 12. Что делать агенту дальше

1. Перейти к **Этапу 3**: создать `src/Sparta.Mcp` (Python/FastMCP) поверх `sparta-ai-service`: tools `get_current_values`, `get_history`, `analytics_summary`, `create_work_order` (последний — за фичефлагом), ресурс `scada://equipment/{id}/report`.
2. Перед Этапом 3 убедиться, что `src/Sparta.Mcp/` пуст — создать там полноценный Python-пакет с `requirements.txt` или `pyproject.toml`.
3. После каждого этапа обновлять `AGENTS.md` и `README.md`: добавлять актуальные команды сборки/запуска, пути к файлам, инструкции по тестированию и заметки об ограничениях/блокерах.

> Важно: не вносить изменения в ядро Rapid SCADA без явной необходимости и предварительного обсуждения. Все расширения — через штатные механизмы модулей/драйверов/плагинов.

### Известные ограничения и заметки

- **Rapid SCADA запускается как два отдельных консольных окна** (`ScadaServerApp.exe`, `ScadaCommApp.exe`). Для production-развёртывания лучше использовать штатные службы Windows (`ScadaServerWkr` / `ScadaCommWkr`) или ScadaAgent + ScadaAdmin.
- **Webstation** в демо-проекте отключён (`WebApp enabled="false"`). Для визуализации нужно будет добавить конфигурацию Webstation и плагин `PlgMimic`.
- **Python в окружении — 3.13**, поэтому `Sparta.AI` использует `psycopg` (v3) вместо `psycopg2`: у `psycopg3` есть готовые wheels под Python 3.13. Скрипт `verify-stage1.py` по-прежнему использует `psycopg2` и работает на системном Python.
- **Ollama** присутствует в `PATH` — полезно для Этапа 5 (LLM-отчёты).
