# US-MOD-03: одобрение товара модератором

## Что сделано

Реализован переход тикета `IN_REVIEW` -> `APPROVED`, отправка события `MODERATED` в B2B через outbox + RabbitMQ (`b2b.moderation.result`).

### API

- **`POST /api/v1/tickets/{ticket_id}/approve`**
  - **Body** (optional): `{ "comment": "..." }`
  - **200**: `TicketResponse`, статус `APPROVED`
  - **403**: тикет закреплён за другим модератором
  - **409**: неверный статус, нет SKU, HARD_BLOCKED

### Исходящее событие

Outbox -> MQ routing key `b2b.moderation.result`, тело `ModerationEventRequest` (совместимо с B2B `POST /api/v1/moderation/events`).

## Автотесты

```bash
make test
```

`tests/integration/test_ticket_approve.py`

## ADR

Рассматривались: синхронный HTTP в handler approve, outbox с фоновой отправкой в RabbitMQ, прямой publish без персистентности. Выбран **outbox + MQ**: надёжность при отказе B2B (retry worker), умеренная сложность, быстрый отклик модератору (200 после commit). Идемпотентность - `idempotency_key` в событии, дедупликация на стороне B2B.
