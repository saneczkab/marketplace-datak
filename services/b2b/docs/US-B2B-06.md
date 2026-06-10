# US-B2B-06: создание накладной на поступление товара

## Что сделано

Создание накладной продавцом

### API

- **`POST /api/v1/invoices`**
  - **Auth**: Bearer JWT (`seller_id` из claims, не из body).
  - **Body**: `InvoiceCreate (items*[])`; элемент `items` - `InvoiceItemCreate (sku_id* uuid, quantity* int, quantity > 0)`.
  - **Код 201**: `InvoiceResponse` (`status = CREATED`, `seller_id`, `items[]` с `id`, `sku_id`, `quantity`, `accepted_quantity`).
  - **Коды ошибок**: `400` `INVALID_REQUEST` (пустой `items`, `quantity <= 0`, товар SKU не `MODERATED`); `403` `NOT_OWNER` (чужой SKU); `404` `NOT_FOUND` (SKU не найден); `401` без Bearer JWT.

Статус накладной при создании - `CREATED` (OpenAPI), не `PENDING` (канон-flow). В ответе нет `sku_name` (в OpenAPI `InvoiceItemResponse` его нет).

## Запуск

```bash
make build up migrate
```

По адресу `localhost:8000/docs` можно найти документацию API-эндпоинтов

## Автотесты

```bash
make test
```

- `test_invoice.py`

Тесты успешно проходят (см. джобу tests)

## ADR

- **Альтернативы места проверки «товар SKU в статусе MODERATED»**:
  1. **Serializer (Pydantic)** - валидатор на `InvoiceCreate` / `InvoiceItemCreate` с доступом к БД через dependency; декларативно рядом со схемой запроса, но смешивает транспортный слой и запросы к БД, при добавлении других entry point (CLI, batch) проверку легко не подключить.
  2. **View (`api/invoice.py`)** - явные `if` в эндпоинте до вызова сервиса; быстро читается в одном файле, но при появлении `POST /invoices/bulk` или внутреннего вызова без HTTP дублирование или пропуск проверки.
  3. **Модель (SQLAlchemy)** - constraint/hook на `InvoiceItem`; гарантия на уровне БД, но статус живёт на `Product`, не на `InvoiceItem`; cross-table правило в модели накладной неудобно и неочевидно.
- **Выбор**: сервисный слой - `invoice_service.create_new_invoice` (ownership и `MODERATED` в одном цикле по `items` до `crud.create_invoice`).
- **Критерии**: **читаемость** - вся бизнес-логика создания накладной в одном месте, view только маппит исключения в HTTP-коды; **риск обойти проверку** - любой новый вызов создания накладной обязан идти через сервис, а не через «тонкий» эндпоинт с размазанными правилами.

## Файлы

`services/b2b/`

### API эндпоинты

- `api/invoice.py` - `create_invoice_endpoint`

### Сервисы

- `services/invoice_service.py` - `create_new_invoice`

### CRUD

- `crud/invoice.py` - `create_invoice`
- `crud/sku.py` - `get_sku_and_product`

### Исключения и схемы

- `exceptions/invoice.py` - `EmptyInvoiceError`, `InvoiceOwnershipError`, `SkuNotModeratedError`, `InvalidQuantityError`
- `schemas/invoice.py` - `InvoiceCreate`, `InvoiceItemCreate`, `InvoiceResponse`, `InvoiceItemResponse`
- `database/models/catalog/inventory.py` - `Invoice`, `InvoiceItem`, `InvoiceStatusEnum`

### Миграции

- `database/alembic/versions/9a1b2c3d4e5f_add_accepted_quantity_to_invoice_items.py` - `accepted_quantity` на позициях; enum статусов накладной `CREATED`, `PARTIALLY_ACCEPTED`, `ACCEPTED`, `CANCELLED`

### Автотесты

- `tests/integration/test_invoice.py`
- `tests/integration/conftest.py` - `edit_product_data`, `product_on_moderation_with_one_sku`
- `tests/factories/invoice.py`
