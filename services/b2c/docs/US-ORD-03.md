# US-ORD-03: отмена заказа

## Что сделано

Реализована отмена заказа со статусом `CREATED`, `PAID`, `ASSEMBLING`

### API

- **`POST /api/v1/orders/{order_id}/cancel`**
  - **Заголовки**: `Authorization`
  - **Path**:
    - `order_id` (uuid) - идентификатор заказа
  - **Body** (`OrderCancelRequest`, optional):
    - `reason` (string, optional, max 500)
  - **Код 200**: `OrderResponse` — заказ переведён в `CANCELLED` или `CANCEL_PENDING`
  - **Код 401**: нет или невалидный JWT
  - **Код 404**: заказ не найден или не принадлежит пользователю
  - **Код 409**: `CANCEL_NOT_ALLOWED` — отмена недоступна в текущем статусе (`DELIVERING`, `DELIVERED`, `CANCELLED`, `CANCEL_PENDING`)

## Запуск

```bash
make build up migrate
```

По адресу `localhost:8000/docs` — описание API

## Автотесты

```bash
uv run python -m pytest -q tests/integration/order/test_cancel_order.py
```

## ADR

Рассмотрены три способа async retry для `unreserve`: Celery task с exponential backoff, management command по cron и Django Q.  
С учётом принятой архитектуры с RabbitMQ для синхронизации данных между сервисами, cron-подход даёт лишний параллельный механизм фона и усложняет сопровождение.  
Celery в этом контексте даёт лучший контроль над повторными попытками, задержками и наблюдаемостью выполнения, а также естественно переживает перезапуски веб-приложения при запущенных воркерах и брокере.  
Django Q тоже решает задачу фона, но добавляет отдельный runtime-слой без преимуществ относительно связки RabbitMQ + Celery.  
Выбор: Celery task с exponential backoff как основной механизм retry `unreserve` в связке с RabbitMQ по критериям сложности настройки в существующей архитектуре и гарантии выполнения после рестартов. На первой итерации реализован scaffold: при падении `unreserve` статус `CANCEL_PENDING` + лог, без фонового воркера.

## Файлы

### API

- `api/orders.py`

### Сервисы

- `services/order_service.py`

### CRUD

- `crud/order.py`

### Клиент B2B

- `clients/b2b_client.py`

### Схемы

- `schemas/order.py`

### Модели

- `database/models/orders/order.py`

### Исключения

- `exceptions/order.py`

### Автотесты

- `tests/integration/order/test_cancel_order.py`
