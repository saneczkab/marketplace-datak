# US-B2B-10: fulfill — финальное списание резерва при доставке

## Что сделано

Реализован эндпоинт `POST /api/v1/inventory/fulfill`, который при успешной доставке
заказа списывает `reserved_quantity` и `stock_quantity` у SKU (активный остаток
`active_quantity` не меняется). Идемпотентность гарантируется таблицей
`catalog.inventory_fulfill_operations`, ключ — `order_id`.

### API

- **`POST /api/v1/inventory/fulfill`** (`X-Service-Key: B2C_SERVICE_KEY`)
  - **Body**: `InventoryOrderRequest` (`order_id`, `items: [{sku_id, quantity}]`)
  - **200**: `InventoryOrderResponse` (`order_id`, `status: "FULFILLED"`, `processed_at`) — резерв списан (или повторный идемпотентный запрос)
  - **401**: отсутствует/неверный `X-Service-Key`
  - **404**: SKU не найден
  - **409**: `CONFLICT` — `reserved_quantity` SKU меньше запрошенного количества (all-or-nothing: при ошибке хотя бы по одному SKU транзакция откатывается)

## Автотесты

```bash
make test
```

`tests/integration/test_fulfill_inventory.py`

- `test_fulfill_decreases_reserved_and_stock_quantity` — после успешного fulfill `reserved_quantity` обоих SKU равен 0, а `stock_quantity` уменьшен на отгруженное количество
- `test_active_quantity_unchanged` — `active_quantity` не изменяется после fulfill
- `test_idempotent_fulfill_no_double_deduction` — повторный запрос с тем же `order_id` возвращает 200 и не списывает резерв повторно
- `test_fulfill_exceeding_reserved_returns_409` — запрос с `quantity` больше `reserved_quantity` возвращает 409 `CONFLICT`, резерв не изменяется (all-or-nothing)
- `test_missing_service_key_returns_401` — запрос без `X-Service-Key` возвращает 401 с `{"code": "UNAUTHORIZED"}`

## ADR

**Задача**: гарантировать, что при retry-запросе от B2C (`order_id` тот же) `reserved_quantity`
не будет уменьшен дважды.

**Рассмотренные альтернативы**:

1. **Отдельная таблица `inventory_fulfill_operations` с ключом `order_id`** *(выбрана)*
   — первый INSERT обнаруживает дубликат до выполнения декрементов; симметрично `InventoryUnreserveOperation`.
2. **Поле `last_fulfilled_order` на SKU** — ломается при заказах с несколькими SKU
   (нужно хранить состояние per-SKU, а не per-order) и при SKU, попадающих в разные заказы.
3. **Вывод идемпотентности из `reserved_quantity`** — невозможно отличить «уже выполнен»
   от «резерв не был создан»; высокий риск двойного списания при concurrent retry.

**Критерии**: риск двойного списания + сложность реализации.
**Победитель**: вариант 1 — минимальный риск (дубликат PK отбрасывается до изменений),
минимальная сложность (один INSERT, зеркало паттерна unreserve).

## Файлы

- `api/inventory.py` — роутер `POST /api/v1/inventory/fulfill` (рядом с `reserve`/`unreserve`)
- `schemas/inventory.py` — переиспользуются `InventoryOrderRequest`, `InventoryOrderResponse`
- `services/inventory_service.py` — `fulfill_inventory`
- `crud/inventory.py` — `get_fulfill_operation`, `save_fulfill`
- `exceptions/inventory.py` — `FulfillConflictError`
- `database/models/catalog/inventory_operations.py` — `InventoryFulfillOperation`
- `database/alembic/versions/f1a2b3c4d5e6_inventory_fulfill_operations.py`
- `middlewares/service_key_verification.py` — покрывается префиксом `/api/v1/inventory`
- `tests/integration/conftest.py` — `FulfillInventoryData`, `fulfill_inventory_data`
- `tests/integration/test_fulfill_inventory.py`
