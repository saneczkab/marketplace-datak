# US-MOD-06: справочник причин блокировки

## Что сделано

Реализован справочник `blocking_reasons`

- **`GET /api/v1/blocking-reasons`**
  - Query: `hard_block`, `is_active` (default `true`)
  - **200**: массив `BlockingReasonResponse` (`id`, `code`, `title`, `description`, `hard_block`, `is_active`)
- **`POST /api/v1/blocking-reasons`**
  - Body: `BlockingReasonCreateRequest`
  - **201**: созданная причина
  - **409**: дубль `code`
- **`PATCH /api/v1/blocking-reasons/{reason_id}`**
  - Body: `BlockingReasonUpdateRequest` (`title`, `description`, `is_active`)
  - **404**: причина не найдена
- **`DELETE /api/v1/blocking-reasons/{reason_id}`**
  - Soft-delete: `is_active=false`, строка в БД сохраняется
  - **204** / **404**

### Связь с MOD-04/MOD-05

- `tickets.blocking_reason_id` → FK `blocking_reasons.id` (`ON DELETE RESTRICT`)
- `block_ticket` принимает только активные причины (`is_active=true`)
- `hard_block` определяет `BLOCKED` vs `HARD_BLOCKED`

## Автотесты

```bash
make test
```

`tests/integration/test_blocking_reasons.py`:

## ADR

Рассматривались: enum в коде, таблица в БД с CRUD, i18n-каталог. Выбрана **таблица в БД + soft-delete**: новые причины добавляются через API без деплоя; исторические ссылки на `blocking_reason_id` сохраняются при деактивации; стабильный `code` даёт основу для будущей многоязычности (`title` по локалям). Django Admin в проекте отсутствует (FastAPI) — CRUD через REST по OpenAPI.
