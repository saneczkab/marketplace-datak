# US-CAT-02: поиск товаров

## Что сделано

Реализован текстовый поиск для B2C каталога: покупатель ищет товары по названию и описанию через параметр `q` на том же эндпоинте, что и листинг каталога (US-CAT-01). Поиск совместим с фильтрами категории, цены и атрибутов.

Данные каталога читаются из локальной БД B2C, без отдельного обращения к B2B - это архитектурное решение - хранить данные в B2C и через очередь сообщений управлять обновлениями данных в сервисах.

Поиск выполняется по полям `title` и `description` через SQL `ILIKE` с экранированием спецсимволов `%` и `_`. Условие видимости то же, что в каталоге: `status = MODERATED`, `deleted = false`, хотя бы один SKU с `active_quantity > 0`.

### API

Перечень реализованных эндпоинтов:

- `GET /api/v1/catalog/products`
  - **Query params (поиск)**: `q` (опционально, min 3 символа после trim, max 200), совместим с `filter[category_id]`, `filter[price_min]`, `filter[attributes][...]`, `sort`, `limit`, `offset` - см. **US-CAT-01**
  - **Код 200**: `PaginatedCatalogProducts` - совпадения по `title` или `description`; при отсутствии результатов `items: []`, `total_count: 0`
  - **Код 400**: `{"code": "INVALID_REQUEST", "message": "Search query must be at least 3 characters"}` (запрос короче 3 символов после trim) / `Search query must be at most 200 characters` (превышен лимит длины)
  - **Код 500**: текст ошибки (прочие сбои)

## Запуск

```bash
make build up migrate
```

По адресу `localhost:8000/docs` можно найти документацию API-эндпоинтов.

## Автотесты

```bash
make test
```

- `tests/integration/catalog/test_catalog.py::test_search_returns_matching_products` - поиск возвращает товары по title и description
- `tests/integration/catalog/test_catalog.py::test_short_query_returns_400` - запрос короче 3 символов возвращает 400
- `tests/integration/catalog/test_catalog.py::test_empty_results_returns_200` - нет совпадений → 200 с пустым списком
- `tests/integration/catalog/test_catalog.py::test_special_chars_do_not_break_query` - спецсимволы (`iPhone%15`, `кофе'`, …) не ломают запрос

Тесты успешно проходят (см. джобу tests).
