# US-B2B-04: удаление товара

## Что сделано

Soft-delete товара продавцом: физически строка в БД не удаляется, выставляются `deleted = true` и `status = DELETED`. Товар исчезает из стандартного списка продавца и из публичного каталога B2C (фильтр `deleted = false`).
В одной транзакции с soft delete в outbox пишутся два события - `DELETED` для Moderation и `PRODUCT_DELETED` для B2C (payload включает `sku_ids` всех SKU товара). Доставка - transactional outbox (`outbox_events`) + worker - RabbitMQ - сервисы Moderation и B2C.

### API

- **`DELETE /api/v1/products/{product_id}`**
  - **Auth**: Bearer JWT.
  - **Код 204**: товар помечен удалённым, тело ответа пустое (по OpenAPI; в канон-flow указан `200 {"ok": true}`).
  - **Побочные эффекты**: `deleted = true`, `status = DELETED`; outbox-событие `DELETED` (`moderation.product.deleted`); outbox-событие `PRODUCT_DELETED` (`b2c.product.deleted`, поле `sku_ids`).
  - **Коды ошибок**: `404` `NOT_FOUND` (товар не найден или уже удалён); `403` `NOT_OWNER` (чужой товар); `401` без Bearer JWT.

Повторное удаление возвращает `404` (соответствие спецификации OpenAPI), а не `400` (как в канон-флоу)

## Запуск

```bash
make build up migrate
```

По адресу `localhost:8000/docs` можно найти документацию API-эндпоинтов

## Автотесты

```bash
make test
```

`test_delete_product.py` - сценарии квеста US-B2B-04

Тесты успешно проходят (см. джобу tests)

## ADR

- **Альтернативы доставки двух каскадных событий (`DELETED` + `PRODUCT_DELETED`)**:
  1. **Два синхронных POST** - в обработчике `DELETE` сразу вызывать HTTP Moderation и B2C; простая трассировка, но при недоступности любого из сервисов весь delete падает, хотя `deleted = true` в B2B уже мог быть записан (риск рассинхрона при частичном сбое).
  2. **Outbox для обоих** - в одной транзакции soft delete + две строки в `outbox_events`; worker доставляет независимо; ответ продавцу `204` не зависит от доступности Moderation/B2C.
  3. **Синхронно в Moderation + outbox в B2C** - компромисс: модерация узнаёт сразу, B2C - асинхронно; при падении Moderation delete откатывается целиком, при падении B2C - товар уже скрыт в B2B, но корзины B2C обновятся с задержкой.
- **Выбор**: outbox для обоих событий.
- **Критерии**: **недоступность сервиса** - продавец получает успешный `204`, события остаются `PENDING` и уходят после восстановления брокера/consumer; **согласованность при частичном сбое** - либо в БД зафиксированы и soft delete, и оба outbox-события, либо транзакция откатывается целиком, без состояния «удалён в B2B, но событие в B2C потеряно».

## Файлы

`services/b2b/`

### API эндпоинты

- `api/products.py` - `delete_product`

### Сервисы

- `services/product_service.py` - `remove_product`, `get_all_seller_products`

### CRUD

- `crud/product.py` - `soft_delete_product`, `get_seller_products`, `get_product_skus`
- `crud/outbox.py` - `enqueue_moderation_product_deleted`, `enqueue_b2c_product_deleted`, `build_moderation_product_deleted_payload`, `build_b2c_product_deleted_payload`
- `crud/public_product.py` - фильтр `deleted = false` для витрины B2C

### Исключения и схемы

- `exceptions/product.py` - `ProductAlreadyDeletedError`, `ProductNotOwnerError`
- `database/models/catalog/base.py` - `ProductStatusEnum.DELETED`, поле `deleted`

### Миграции

- `database/alembic/versions/52a3dd662571_add_deleted_product_status.py` - значение `DELETED` в enum статусов товара

### Автотесты

- `tests/integration/test_delete_product.py`
- `tests/integration/conftest.py` - `category_with_products`, `edit_product_data`
