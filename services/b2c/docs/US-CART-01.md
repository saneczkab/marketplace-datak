# US-CART-01: избранное покупателя

## Что сделано

Реализация действий с избранным и подписками

### API

Используется Authorization Bearer token

- **`GET /api/v1/favorites`**
  - **Query params**: `limit` (1-100, по умолчанию 20), `offset` (от 0)
  - **Код 200**: список избранного
  - **Код 401**: не авторизован

- **`PUT /api/v1/favorites/{product_id}`**
  - **Path params**: `product_id`
  - **Код 204**: добавлено в избранное
  - **Код 404**: товар не найден / недоступен для добавления
  - **Код 401**: не авторизован

- **`DELETE /api/v1/favorites/{product_id}`**
  - **Path params**: `product_id`
  - **Код 204**: удалено избранное
  - **Код 401**: не авторизован

- **`POST /api/v1/favorites/{product_id}/subscribe`**
  - **Path params**: `product_id`
  - **Body**: `{ "events": ["BACK_IN_STOCK", "PRICE_DROP"] }`
  - **Код 204**: подписка создана или обновлена
  - **Код 401**: не авторизован
  - **Код 404**: товар не найден
  - **Код 422**: неверные значения в `events`

- **`DELETE /api/v1/favorites/{product_id}/subscribe`**
  - **Path params**: `product_id`
  - **Код 204**: подписка удалена
  - **Код 401**: не авторизован

## Запуск

```bash
make build up migrate
```

По адресу `localhost:8000/docs` — описание API.

## Автотесты

```bash
make test
```

## ADR

- **Альтернативы**:
  - `user_id` в query/body - IDOR на список избранного
  - заголовок `X-User-Id` - подделывается клиентом
  - `user_id` из JWT после проверки подписи и активной сессии - нельзя указать чужой профиль без компрометации токена
- **Выбор**: JWT + middleware

## Файлы

### Middleware

- `middlewares/token_verification.py`

### API эндпоинты

- `api/favorite.py`
- `api/subscriptions.py`

### Сервисы

- `services/favorite_service.py`
- `services/subscription_service.py`

### CRUD

- `crud/favorite.py`
- `crud/subscription.py`

### Схемы

- `schemas/catalog.py`
- `schemas/subscription.py`

### Автотесты

- `tests/integration/cart/test_favorite.py`
    - Задание требует тест `add_to_favorites_returns_201`, однако в спецификации указан код 204, автотест изменён на `test_add_to_favorites_returns_204`
    - Задание требует тест `repeat_add_returns_200_not_duplicate`, однако в спецификации для повторного добавления соответствует код 204, так что проверяется сценарий `repeat_add_returns_204_not_duplicate`
- `tests/integration/cart/test_subscription.py`
