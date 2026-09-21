# Sparta SCADA

Кастомная локальная SCADA-система поверх open-source платформы **Rapid SCADA 6**.

- Сбор данных с промышленного оборудования по **OPC UA**.
- Локальная **ИИ-аналитика** данных оборудования.
- Автоматическая выдача заявок на обслуживание во внешнюю **ERP-систему**.

Всё выполняется локально, без облачных сервисов. Ядро Rapid SCADA не изменяется — все доработки реализуются через штатные точки расширения (модули Server, драйверы Communicator, плагины Webstation).

---

## Архитектура

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
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  Оборудование:  ПЛК/контроллеры ←OPC UA→ DrvOpcUa          │
└─────────────────────────────────────────────────────────────┘
```

---

## Требования

- [Docker](https://www.docker.com/) и Docker Compose
- [Rapid SCADA 6](https://rapidscada.net/) (исходники включены как `scada-v6-master/`)
- [.NET 8+ SDK](https://dotnet.microsoft.com/) (для сборки Rapid SCADA на Этапе 1 и ModERP на Этапе 4)
- Python 3.11+ (для Этапов 2–3)

---

## Быстрый старт

```bash
# 1. Скопируйте шаблон переменных окружения
cp .env.example .env

# 2. Запустите инфраструктуру
docker compose up -d

# 3. Проверьте, что сервисы поднялись
docker compose ps

# 4. Проверьте доступность OPC UA demo-сервера
#    Endpoint: opc.tcp://localhost:4840/
```

---

## Этап 1 — поток данных OPC UA → Rapid SCADA → PostgreSQL

Демо-конфигурация Rapid SCADA находится в `scada-config/SpartaDemo/`. Проект подключается к локальному OPC UA demo-серверу (`opc-plc`) и пишет текущие и минутные архивы в PostgreSQL через `ModArcPostgreSql`.

### Сборка и запуск вручную

```bash
# 1. Запустить инфраструктуру (если ещё не запущена)
docker compose up -d

# 2. Собрать Rapid SCADA и модули
dotnet build scada-v6-master/scada-v6-master/ScadaCommon/ScadaCommon.sln -c Release
dotnet build scada-v6-master/scada-v6-master/ScadaServer/ScadaServer/ScadaServer.sln -c Release
dotnet build scada-v6-master/scada-v6-master/ScadaComm/ScadaComm/ScadaComm.sln -c Release
dotnet build scada-v6-master/scada-v6-master/ScadaComm/OpenDrivers/OpenDrivers.sln -c Release
dotnet build scada-v6-master/scada-v6-master/ScadaServer/OpenModules/OpenModules.sln -c Release

# 3. Развернуть конфигурацию и бинарники
rm -rf scada-config/runtime
dotnet scripts/deploy-scada-config/bin/Release/net10.0-windows/deploy-scada-config.dll \
  scada-config/SpartaDemo/SpartaDemo.rsproj scada-config/runtime
bash scripts/copy-runtime-binaries.sh

# 4. Запустить Rapid SCADA
scripts/start-scada-runtime.bat

# 5. Проверить поток тегов в PostgreSQL
python scripts/verify-stage1.py
```

### Проверка вручную

```bash
# Текущие значения тегов
docker exec sparta-postgres psql -U scada -d scada \
  -c "SELECT cnl_num, val, time_stamp FROM mod_arc_postgre_sql.curcopy_current ORDER BY cnl_num;"

# История за последние 5 минут
docker exec sparta-postgres psql -U scada -d scada \
  -c "SELECT cnl_num, val, time_stamp FROM mod_arc_postgre_sql.mincopy_historical WHERE time_stamp >= now() - interval '5 minutes' ORDER BY time_stamp DESC;"
```

### Остановка

```bash
scripts/stop-scada-runtime.bat
```

---

## Этап 2 — сервис `Sparta.AI` (Python/FastAPI)

Сервис `sparta-ai-service` читает текущие и исторические данные из PostgreSQL-архива Rapid SCADA и предоставляет REST API для аналитики.

### Запуск в Docker (рекомендуется)

```bash
# Сервис входит в общий docker-compose.yml
docker compose up --build -d sparta-ai-service

# Проверка
curl http://localhost:8000/health
curl http://localhost:8000/tags
```

### Локальный запуск для разработки

```bash
cd src/Sparta.AI
python -m venv .venv
.venv/Scripts/activate        # Windows Git Bash
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### API

- `GET /health` — состояние сервиса и подключения к БД.
- `GET /tags` — список каналов с текущими значениями.
- `GET /history?cnl_num=101&limit=100` — история по каналу (также `tag_code=StepUp`).
- `POST /analyze` — детекция аномалий (`zscore` / `ewma`).
- `POST /predict` — простой линейный прогноз.

OpenAPI-документация: http://localhost:8000/docs

### Проверка

```bash
python scripts/verify-stage2.py
```

---

## Структура репозитория

```
sparta-scada/
├── README.md
├── docker-compose.yml
├── .env.example
├── AGENTS.md             # инструкции для AI-агентов
├── docs/                 # документация
├── scada-config/         # конфигурация Rapid SCADA
│   ├── SpartaDemo/       # демо-проект (BaseXML + Instances)
│   └── runtime/          # развёрнутый runtime (создаётся скриптами)
├── src/
│   ├── ModERP/           # C# модуль ScadaServer
│   ├── Sparta.AI/        # sparta-ai-service (Python/FastAPI)
│   └── Sparta.Mcp/       # sparta-mcp-server (Python/FastMCP)
├── migrations/           # SQL-миграции PostgreSQL
└── scripts/              # скрипты сборки/запуска
```

---

## Этапы разработки

1. **Этап 0 — каркас**: репозиторий, `docker-compose` с PostgreSQL + demo OPC UA server, README. ✅
2. **Этап 1 — данные**: демо-конфигурация Rapid SCADA с OPC UA, PostgreSQL-архив, проверка потока тегов. ✅
3. **Этап 2 — ИИ-сервис**: `Sparta.AI` с чтением тегов/истории и базовой детекцией аномалий. ✅
4. **Этап 3 — MCP-сервер**: `Sparta.Mcp` поверх `Sparta.AI`.
5. **Этап 4 — ERP-модуль**: `ModERP` с очередью заявок + эмулятор ERP в `docker-compose`.
6. **Этап 5 — прогнозирование и LLM-отчёты** (Ollama, за фичефлагом).
7. **Этап 6 — полировка**: документация, примеры, `docker-compose` «всё-в-одном».

---

## Лицензия

Apache License 2.0 с сохранением уведомлений Rapid SCADA.
