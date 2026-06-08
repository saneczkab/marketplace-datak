# US-B2B-08: резервирование и снятие резерва SKU

## Что сделано

Реализованы `POST /api/v1/inventory/reserve` и `POST /api/v1/inventory/unreserve`

### API

- **`POST /api/v1/inventory/reserve`** (`X-Service-Key`)
  - **Body**: `ReserveRequest` (`idempotency_key`, `order_id`, `items[]`)
  - **200**: `ReserveResponse` (`order_id`, `status: RESERVED`, `reserved_at`)
  - **409**: `INSUFFICIENT_STOCK`, `details.failed_items` (`OUT_OF_STOCK` / `INSUFFICIENT_STOCK` / `PRODUCT_UNAVAILABLE`)
  - **404**: SKU не найден

- **`POST /api/v1/inventory/unreserve`** (`X-Service-Key`)
  - **Body**: `InventoryOrderRequest` (`order_id`, `items[]`)
  - **200**: `InventoryOrderResponse` (`status: UNRESERVED`, `processed_at`)
  - Идемпотентность по `order_id`

### Очередь (outbox - RabbitMQ)

При `active_quantity == 0` после reserve в `outbox_events` пишется сообщение `SKU_OUT_OF_STOCK` (routing key `b2c.events`, формат B2C `B2BEvent`). Доставка - существующий outbox worker.

## Автотесты

```bash
make test
```

`tests/integration/test_reserve_inventory.py`

## ADR

Рассмотрены: одна транзакция с `SELECT FOR UPDATE`; optimistic locking с retry; двухфазный commit. Выбрана **одна транзакция с `SELECT FOR UPDATE`** (SKU блокируются в порядке `id`). Критерии: предсказуемая all-or-nothing семантика под конкурентным checkout; минимальная сложность в одной БД B2B.

## Файлы

- `api/inventory.py`, `services/inventory_service.py`, `crud/inventory.py`
- `schemas/inventory.py`, `exceptions/inventory.py`
- `database/models/catalog/inventory_operations.py`
- `database/alembic/versions/a8f3c2b91d04_inventory_reserve_operations.py`
- `crud/outbox.py` - `enqueue_b2c_event`
- `middlewares/service_key_verification.py` - префикс `/api/v1/inventory`
- `tests/integration/test_reserve_inventory.py`
