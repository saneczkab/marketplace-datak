# US-B2B-11: Список товаров продавца (seller cabinet)

## Что сделано

`GET /api/v1/products` (Bearer JWT) — пагинированный список товаров продавца с
фильтром по статусу, `include_deleted`, поиском по названию и агрегатами по SKU.
seller_id берётся только из JWT; ответ — `ProductShortResponse` + `skus_count` /
`total_active_quantity`; удалённые — при `include_deleted=true` (с флагом `deleted`).

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

**Агрегация `skus_count` / `total_active_quantity`**

Рассмотрены три подхода: `annotate` с `Count`/`Sum` в queryset списка (JOIN +
GROUP BY), prefetch SKU с подсчётом в сериализаторе и raw SQL. Выбран отдельный
grouped-запрос по `product_id IN (...)` с `func.count` и `func.sum` — тот же
смысл, что у annotate, но без JOIN в основном запросе страницы. По N+1: один
доп. запрос на страницу вместо N загрузок SKU или коррелированных подзапросов.
По поддержке: агрегация изолирована в CRUD, list-query остаётся простым; без
raw SQL и без логики подсчёта в сериализаторе.


## Слои

- **Schemas** (`schemas/product.py`) — `ProductSellerListResponse`,
  `ProductSellerListItem` (`ProductShortResponse` + агрегаты SKU).
- **CRUD** (`crud/product.py`) — страница seller-товаров + total_count,
  grouped-агрегаты по SKU (`count`, `sum(active_quantity)`, `min(price)`).
- **Service** (`services/product_service.py`) — `list_seller_products`: сборка
  items из страницы + cover_image + aggregates.
- **API** (`api/products.py`) — `GET /api/v1/products`, query-параметры
  `limit/offset/status/include_deleted/search`, seller_id из JWT.
