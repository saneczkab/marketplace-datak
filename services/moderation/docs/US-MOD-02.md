# US-MOD-02: получение следующей карточки из очереди

## Что сделано

Реализован атомарный claim следующего PENDING-тикета: перевод в `IN_REVIEW`, закрепление за модератором, защита от race через `SELECT FOR UPDATE SKIP LOCKED`, возврат 204 при пустой очереди, 409 если у модератора уже есть активный `IN_REVIEW`.
Просроченные `IN_REVIEW` (старше `IN_REVIEW_CLAIM_TIMEOUT_MINUTES`, default 30) автоматически возвращаются в `PENDING` при следующем claim.

### API

- **`POST /api/v1/queue/claim`**
  - **Body** (optional): `{ "queue_priority": 1..4, "category_ids": ["..."] }`
  - **200**: `TicketResponse` со статусом `IN_REVIEW`, `claimed_at`, `claim_expires_at`
  - **204**: очередь пуста
  - **409**: у модератора уже есть тикет в `IN_REVIEW`

## Автотесты

```bash
make test
```

`tests/integration/test_queue_claim.py`

## ADR

Рассматривались: PostgreSQL `SELECT FOR UPDATE SKIP LOCKED`, Redis distributed lock, отдельный queue-сервис. Выбран **SKIP LOCKED в Postgres**: без новых зависимостей, race виден в одном SQL-транзакционном блоке, при пропаже модератора карточка возвращается в очередь по configurable TTL (`claimed_at + IN_REVIEW_CLAIM_TIMEOUT_MINUTES`). Redis добавил бы инфраструктуру и split-brain при failover; отдельный queue-сервис - overkill для MVP.

## Файлы

- `api/queue.py`
- `crud/queue.py`
- `services/queue_service.py`
- `schemas/ticket.py` - `ClaimTicketRequest`, `claimed_at` в response
- `database/models/tickets/ticket.py` - поле `claimed_at`
- `database/alembic/versions/b7c8d9e0f1a2_queue_claim.py`
- `middlewares/token_verification.py` - auth для `/api/v1/queue`
