# US-MOD-01: приём событий о товаре от B2B

## Что сделано

Реализован приём событий о товаре от B2B (Flow MOD-1): создание и обновление карточек модерации по `PRODUCT_CREATED` / `PRODUCT_EDITED` / `PRODUCT_DELETED`.

Снимок товара для тикета (`json_after`) собирается из **локальной реплики каталога** в Moderation, без HTTP-запросов в B2B. Реплика обновляется RabbitMQ consumer'ом по событиям `PRODUCT_UPDATE` / `SKU_UPDATE` (routing key `catalog.events`) - по тому же принципу, что B2C/B2B держат локальные данные и синхронизируют их через очередь.

### API

- **`POST /api/v1/b2b/events`** (`X-Service-Key` = `B2B_SERVICE_KEY`)
  - **Body**: `IncomingB2BEvent` (`event_type`, `idempotency_key`, `occurred_at`, `payload`)
  - **Код 202**: событие принято (в т.ч. идемпотентный повтор)
  - **Код 400**: невалидное тело / бизнес-ошибка (`TicketAlreadyExistsError`, `TicketNotFoundError`, …)
  - **Код 401**: отсутствует или неверный `X-Service-Key`

## Запуск

```bash
make build up migrate
```

По адресу `localhost:8002/docs` - описание API.

## Автотесты

```bash
make test
```

`tests/integration/test_b2b_events.py`

## ADR

**Хранение что было / что стало в карточке**

Рассматривались три варианта: пара полных снимков `json_before` + `json_after`, только актуальный `json_after`, и хранение дельты изменений. Выбраны `json_before` + `json_after` (JSONB в `tickets`): при `PRODUCT_CREATED` заполняется только `json_after`, при `PRODUCT_EDITED` прежний `json_after` переносится в `json_before`, новый снимок пишется в `json_after`. Для модератора и разбора инцидента два полных снимка сразу показывают контекст правки без реконструкции состояния; вариант только `json_after` экономит место, но теряет историю последней версии на карточке. Дельта компактнее по объёму, но усложняет чтение UI и восстановление картины при сбоях - нужен базовый снимок и логика склейки.

## Файлы

### Middleware

- `middlewares/service_key_verification.py` - `/api/v1/b2b`

### API

- `api/b2b_events.py`

### Сервисы

- `services/b2b_event_service.py` - валидация `IncomingB2BEvent`, вызов CRUD
- `services/catalog_sync_service.py` - парсинг сообщений очереди, вызов CRUD
- `core/messaging.py` - consumer `moderation.catalog.events`

### CRUD

- `crud/b2b_event.py` - обработка B2B-событий, `commit`
- `crud/catalog_event.py` - обработка catalog-событий, `commit`
- `crud/ticket.py`
- `crud/catalog.py` - реплика каталога, `build_product_snapshot`
- `crud/processed_event.py`, `crud/processed_catalog_event.py`

### Схемы

- `schemas/b2b_event.py`
- `schemas/catalog_event.py`
- `schemas/product_snapshot.py`

### Модели

- `database/models/tickets/` - `tickets`, `ticket_field_reports`
- `database/models/catalog/` - реплика каталога
- `database/models/processed_events/` - `processed_b2b_events`, `processed_catalog_events`

### Исключения

- `exceptions/b2b_event.py`, `exceptions/catalog.py`
