# US-MOD-05: жёсткая блокировка (необратимая)

## Что сделано

Реализован переход тикета `IN_REVIEW` -> `HARD_BLOCKED` через общий endpoint блокировки, отправка события `BLOCKED` с `hard_block=true` в B2B через outbox + RabbitMQ (`b2b.moderation.result`).
Seed-данные в `reference_data/blocking_reasons.py`. Миграция импортирует этот список.

- **`POST /api/v1/tickets/{ticket_id}/block`**
  - **Body**: `{ "blocking_reason_ids": ["..."], "comment": "...", "field_reports": [] }`
  - Тип блокировки определяется по `hard_block` выбранной причины из справочника `blocking_reasons`
  - **200**: `TicketResponse`, статус `HARD_BLOCKED` (или `BLOCKED` для soft-причин)
  - **403**: тикет закреплён за другим модератором или терминальный `HARD_BLOCKED`
  - **409**: неверный статус (не `IN_REVIEW`)
  - **400**: причина блокировки не найдена

### Исходящее событие

Outbox -> MQ routing key `b2b.moderation.result`, тело `ModerationEventRequest` с `event_type=BLOCKED`, `hard_block=true`, `blocking_reason_id`.

### Терминальность

- `PRODUCT_EDITED` / повторный `PRODUCT_CREATED` для `HARD_BLOCKED` - идемпотентно игнорируются
- `PRODUCT_DELETED` - удаляет запись тикета
- Любая мутация тикета (`approve`, `block`) на `HARD_BLOCKED` -> **403**

## Автотесты

```bash
make test
```

`tests/integration/test_ticket_hard_block.py`

## ADR

Рассматривались: терминальный enum-статус с проверкой на каждом mutating endpoint, отдельный флаг `is_terminal`, выделение `HARD_BLOCKED` в архивную таблицу. Выбран **терминальный enum + центральные guards** в `ticket_decision` и B2B event handlers: низкий риск обхода (все мутации проходят через 2–3 функции), простой аудит по `decision_at` и outbox payload, data-fix суперадмином через Django Admin без штатного API разблокировки.
