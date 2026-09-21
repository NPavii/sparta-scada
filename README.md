# Sparta SCADA

Кастомная SCADA-система на базе open-source платформы **Rapid SCADA 6** (Apache License 2.0).

## Цели проекта

- Подключение к промышленному оборудованию по **OPC UA** (теги чтение/запись).
- **Локальная ИИ-аналитика** по данным оборудования (аномалии, прогнозы, отчёты; LLM — опционально через Ollama). Никакого облака.
- **MCP-сервер** для доступа LLM-агентов к данным SCADA.
- Интеграция с **ERP**: автоматическая выдача заявок на обслуживание оборудования и получение их статусов.

## Архитектура (кратко)

```
Оборудование ←OPC UA→ Rapid SCADA 6 (Communicator/Server/Webstation, PostgreSQL-архив)
                          │
        ┌─────────────────┼──────────────────────┐
        ▼                 ▼                      ▼
  Sparta.AI          Sparta.MCP              ModERP
 (FastAPI: аналитика, (MCP-сервер: tools     (модуль ScadaServer:
  аномалии, прогнозы)  теги/история/заявки)   заявки в ERP по REST)
```

Подробное ТЗ для агента-разработчика: [docs/agent-prompt.md](docs/agent-prompt.md)

## Стек

- C# / .NET 6+ — модули Rapid SCADA
- Python 3.11+ / FastAPI / FastMCP — ИИ-сервис и MCP-сервер
- PostgreSQL — архивы Rapid SCADA + служебные таблицы
- Docker / docker-compose

## Лицензия

Apache License 2.0 (с сохранением уведомлений Rapid SCADA).
