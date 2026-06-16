# US-MOD-04: мягкая блокировка с замечаниями

## Что сделано

Реализован переход тикета `IN_REVIEW` -> `BLOCKED` через общий endpoint блокировки (soft-причина с `hard_block=false`), сохранение `field_reports`, отправка события `BLOCKED` с `hard_block=false` в B2B через outbox + RabbitMQ (`b2b.moderation.result`).

- **`POST /api/v1/tickets/{ticket_id}/block`**
  - **Body**: `{ "blocking_reason_ids": ["..."], "comment": "...", "field_reports": [{ "field_path": "...", "message": "...", "sku_id": "..." }] }`
  - Тип блокировки определяется по `hard_block` выбранной причины из справочника `blocking_reasons`
  - **200**: `TicketResponse`, статус `BLOCKED` (или `HARD_BLOCKED` для hard-причин)
  - **403**: тикет закреплён за другим модератором или терминальный `HARD_BLOCKED`
  - **409**: неверный статус (не `IN_REVIEW`)
  - **400**: причина блокировки не найдена, недопустимый `field_path`

### Исходящее событие

Outbox -> MQ routing key `b2b.moderation.result`, тело `ModerationEventRequest` с `event_type=BLOCKED`, `hard_block=false`, `blocking_reason_id`, `field_reports` (в событии: `field_name`, `comment`, `sku_id`).

Причина с `hard_block=true` маршрутизируется в hard-block (MOD-5) через тот же endpoint.

## Автотесты

```bash
make test
```

`tests/integration/test_ticket_soft_block.py`

## ADR

Рассматривались: отдельная таблица `ticket_field_reports` с FK, JSONB-массив в `tickets`, event sourcing (только outbox). Выбрана **отдельная таблица с FK**: удобная аналитика по полю (`WHERE field_path = 'description'`), простые миграции при расширении схемы замечаний, предсказуемый размер payload в B2B (нормализованный список в событии). Hard-only причина **маршрутизируется в `HARD_BLOCKED`** через тот же endpoint (как MOD-5 в canon), без отдельного 400.
