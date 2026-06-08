# US-B2B-09: применение решения модерации к товару

## Что сделано

Реализован приём событий от Moderation Service по OpenAPI: `POST /api/v1/moderation/events` (`X-Service-Key`) и  RabbitMQ consumer.

### API

- **`POST /api/v1/moderation/events`** (`MODERATION_SERVICE_KEY`)
  - **Body**: `ModerationEventRequest` (`idempotency_key`, `product_id`, `event_type`, `occurred_at`, …)
  - **204**: событие принято (или идемпотентный повтор)
  - **400**: невалидное тело (`blocking_reason_id` обязателен при `BLOCKED`)
  - **401**: отсутствует/неверный `X-Service-Key`


## Автотесты

```bash
make test
```

`tests/integration/test_moderation_events.py`

## ADR

Рассмотрены: таблица `processed_events`, поле `last_event_key` на Product, conditional upsert по статусу. Выбрана **таблица `(sender_service, idempotency_key)`** с TTL 24ч - минимальный риск race при параллельных HTTP/MQ-доставках и повторных retry Moderation; проще сопровождать, чем хранить event-tracking в доменной модели Product.

## Файлы

- `api/moderation_events.py`
- `schemas/moderation_event.py`
- `services/moderation_event_service.py`
- `crud/moderation_event.py`
- `crud/outbox.py` - `enqueue_product_blocked`
- `database/models/catalog/moderation_processed_events.py`
- `database/alembic/versions/c4a8f2e91b03_moderation_processed_events.py`
- `core/messaging.py` - moderation consumer
- `middlewares/service_key_verification.py` - `/api/v1/moderation`
- `tests/integration/test_moderation_events.py`
