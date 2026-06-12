# US-B2B-11: Список товаров продавца (seller cabinet)

## Что сделано

`GET /api/v1/products` (Bearer JWT) — пагинированный список товаров продавца с
фильтром по статусу, поиском по названию и агрегатами по SKU. seller_id берётся
только из JWT; видны все статусы, включая удалённые (с флагом `deleted`).

## Запуск

```bash
make build up migrate
```

## Автотесты

```bash
make test
```

- `tests/integration/test_list_products.py`:
  - `list_returns_only_own_products`
  - `idor_query_param_seller_id_ignored`
  - `deleted_products_visible_with_deleted_flag`
  - `status_filter_works_correctly`
  - `search_by_title_case_insensitive`
  - `response_includes_sku_aggregates`, `pagination_limit_offset_works`

## ADR

**1. Endpoint: доработка существующего `GET /products` vs единый endpoint по канону**
- Альтернативы: один путь с ветвлением JWT/X-Service-Key (буква канона);
  доработать существующий seller-`GET /products` (B2C-каталог уже вынесен на
  `/public`, US-B2B-07).
- Выбор: доработать существующий seller-endpoint.
- Критерии: согласованность с уже принятым разделением путей `/public`;
  отсутствие риска IDOR через подмену заголовков на одном пути; меньший diff.

**2. Агрегация `skus_count` / `total_active_quantity`**
- Альтернативы: (A) отдельный grouped-запрос + сборка в сервисе; (B) annotate
  через LEFT JOIN + GROUP BY в основном запросе; (C) скоррелированные подзапросы.
- Выбор: A.
- Критерии: нет N+1 (один доп. запрос на страницу); минимальная сложность
  поддержки (копия паттерна `public_product.py`).

**3. IDOR query-параметры**
- `seller_id/user_id/owner_id` не объявлены как параметры → игнорируются
  (вариант «игнорировать», а не 400). seller_id всегда из JWT claims.

## Слои

- **Schemas** (`schemas/product.py`) — `ProductSellerListResponse`,
  `ProductSellerListItem`, `CategoryShort`, `ProductListImage`.
- **CRUD** (`crud/product.py`, `crud/category.py`) — страница seller-товаров +
  total_count, grouped-агрегаты по SKU, batch-загрузка имён категорий.
- **Service** (`services/product_service.py`) — `list_seller_products`: сборка
  items из страницы + images + categories + aggregates.
- **API** (`api/products.py`) — `GET /api/v1/products`, query-параметры
  `limit/offset/status/search`, seller_id из JWT.

## OpenAPI

Режим seller-cabinet `GET /products` (список) в `b2b/openapi.yaml`
(`neomarket-protocols`) на момент реализации отсутствует. Реализация следует
канон-flow `b2b-flows.md#list-products`. Скелет OpenAPI содержит расхождения с
каноном и кодом (`id: integer` вместо UUID, camelCase) — кандидат на отдельный
PR в protocols (вне scope задачи).
