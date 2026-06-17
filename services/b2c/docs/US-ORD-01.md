# US-ORD-01: оформление заказа (checkout)

## Что сделано

Реализован checkout для авторизованного покупателя: создание заказа из корзины с фиксацией цен/названий (исторический снимок в `OrderItem`), идемпотентность повторных запросов, заглушка оплаты (заказ сразу в статусе `PAID`).

Ключевое изменение по сравнению с прошлой попыткой: **резерв остатков вынесен в B2B**. B2C больше не мутирует локальное зеркало остатков (`active_quantity`/`reserved_quantity`) — управление складом является зоной ответственности B2B. На этапе checkout B2C делает HTTP-вызов `POST /api/v1/inventory/reserve` (защищён `X-Service-Key`); локальное зеркало каталога используется только для чтения цен/названий и pre-check статуса товара (BLOCKED/DELETED/не MODERATED — это B2C знает авторитетно из событий модерации).

Последовательность соответствует канону B2C-9: idempotency check → ensure address/payment → `validate_cart` → pre-check статуса → reserve в B2B (all-or-nothing, тот же `idempotency_key`) → создание Order с фиксацией цен.

### API

- **`POST /api/v1/orders`**
  - **Заголовки**: `Authorization: Bearer <JWT>`, `Idempotency-Key: <UUID>`
  - **Body** (`OrderCreateRequest`):
    - `address_id` (uuid) — адрес доставки покупателя
    - `payment_method_id` (uuid) — способ оплаты покупателя
    - `comment` (string, optional, max 1000)
    - `items_snapshot` (optional) — снимок позиций корзины для сверки перед оформлением
  - **Код 201**: `OrderResponse` — созданный или ранее созданный (идемпотентный) заказ; `address` — объект, цены зафиксированы
  - **Код 400**: пустая корзина; невалидный `Idempotency-Key`
  - **Код 401**: нет или невалидный JWT
  - **Код 404**: адрес или способ оплаты не найден / не принадлежит пользователю
  - **Код 409**:
    - `IDEMPOTENCY_CONFLICT` — тот же `Idempotency-Key`, но другое тело запроса
    - `RESERVE_FAILED` — резерв не удался (`details[]`: `sku_id`, `requested`, `reason`, опц. `available`). Источник: локальный pre-check статуса либо проксированные `failed_items` из ответа B2B reserve 409
  - **Код 422**: корзина не прошла валидацию — тело `CartValidationResponse` `{is_valid, cart, issues}` (по OpenAPI/канону B2C-9, без Error-конверта)
  - **Код 503**: `B2B_UNAVAILABLE` — B2B недоступен (таймаут/ошибка соединения/5xx) на этапе резерва

### Вызов B2B

- **`POST {B2B_BASE_URL}/api/v1/inventory/reserve`**, заголовок `X-Service-Key: {B2B_SERVICE_KEY}`
  - Body: `{idempotency_key, order_id, items: [{sku_id, quantity}]}`
  - 200 → резерв выполнен; 409 → `RESERVE_FAILED` (проксируем `details.failed_items`); 404 → `RESERVE_FAILED` (`SKU_NOT_FOUND`); таймаут/5xx → `B2B_UNAVAILABLE`

## Запуск

```bash
make build up migrate
```

Переменные окружения для вызова B2B (см. `.env.example`): `B2B_BASE_URL`, `B2B_SERVICE_KEY` (= `B2C_SERVICE_KEY` в B2B), `B2B_REQUEST_TIMEOUT`.

По адресу `localhost:8000/docs` — описание API.

## Автотесты

```bash
make test
# или точечно:
uv run python -m pytest -q tests/integration/order/test_checkout.py
```

- `test_checkout_creates_paid_order_with_fixed_prices` — happy path: заказ `PAID`, `unit_price`/`line_total` зафиксированы в `OrderItem`
- `test_partial_reserve_failure_returns_409` — товар не в статусе MODERATED → 409 `RESERVE_FAILED` (локальный pre-check)
- `test_partial_reserve_failure_b2b_returns_409` — B2B reserve вернул 409 → 409 `RESERVE_FAILED` с проксированными `failed_items`
- `test_b2b_unavailable_returns_503` — B2B недоступен → 503 `B2B_UNAVAILABLE`
- `test_cart_validation_error_returns_422` — корзина невалидна → 422, тело `{is_valid, cart, issues}`
- `test_idempotency_returns_existing_order` — повтор с тем же `Idempotency-Key` → существующий заказ (резерв не вызывается)
- `test_order_not_authorized_returns_401` — без JWT → 401

B2B в интеграционных тестах не поднимается: HTTP-клиент `get_b2b_client` подменяется через `app.dependency_overrides` фейком `FakeB2BClient` (поведение reserve: ok/conflict/unavailable).

Все тесты проходят локально (`84 passed`).

## ADR

### Хранение идемпотентности

- **Альтернативы**: уникальный индекс на `orders.idempotency_key`; отдельная таблица-кэш ключей; Redis с TTL.
- **Выбор**: уникальный индекс на `orders.idempotency_key` + `idempotency_request_hash` в той же строке заказа.
- **Критерии**:
  - **Race condition**: unique в PostgreSQL гарантирует ровно один заказ на ключ — проигравший конкурентный запрос завершается через `IntegrityError` и возвращает уже созданный заказ. Резерв в B2B идемпотентен по тому же `idempotency_key`, поэтому повторные/гоночные запросы не резервируют дважды. Отдельная таблица/Redis оправданы, только если узким местом станет дублирующая работа до insert.
  - **Сложность реализации**: минимальные изменения, без второй сущности с синхронизацией статусов и без внешней зависимости (Redis).

### Где выполняется резерв остатков

- **Альтернативы**: локальный резерв в зеркале B2C (как было); вызов B2B `/inventory/reserve` по HTTP.
- **Выбор**: вызов B2B. Управление остатками — единый источник истины в B2B; локальный резерв в B2C создаёт риск перепродажи при рассинхроне зеркала. Цена при этом фиксируется из локального зеркала (снимок на момент покупки) — это допустимо, т.к. цена не требует строгой согласованности остатка.

## Файлы

### Конфигурация
- `core/config.py` — `B2B_BASE_URL`, `B2B_SERVICE_KEY`, `B2B_REQUEST_TIMEOUT`
- `.env`, `.env.example`

### Клиенты (новое)
- `clients/b2b_client.py` — `B2BClient.reserve`, зависимость `get_b2b_client`

### API
- `api/orders.py`

### Сервисы
- `services/order_service.py`

### CRUD
- `crud/order.py`

### Схемы
- `schemas/order.py`, `schemas/cart.py` (`CartValidationResponse`)

### Исключения
- `exceptions/order.py` — `ReserveFailedError` (несёт `failed_items`), `B2BUnavailableError`

### Автотесты
- `tests/integration/order/test_checkout.py`
- `tests/integration/order/conftest.py` — `FakeB2BClient`, override `get_b2b_client`
