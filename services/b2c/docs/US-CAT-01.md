# US-CAT-01: каталог товаров с фильтрацией и фасетами

## Что сделано

Реализован каталог товаров для B2C: получение списка товаров с фильтрацией, сортировкой и пагинацией, а также получение фасетов (счётчиков товаров по значениям фильтров) для динамического обновления UI фильтров.

Данные каталога читаются из локальной БД B2C, без отдельного обращения к B2B - это архитектурное решение - хранить данные в B2C и через очередь сообщений управлять обновлениями данных в сервисах.

В списке отображаются только видимые товары: `status = MODERATED`, `deleted = false`, хотя бы один SKU с `active_quantity > 0`.

### API

Перечень реализованных эндпоинтов:

- `GET /api/v1/catalog/products`
  - **Query params**: `limit` (default `20`, max `100`), `offset` (default `0`), `sort` (default `popularity`, допустимые значения: `price_asc`, `price_desc`, `popularity`, `new`), `q` (опционально - текстовый поиск, см. парный квест **US-CAT-02**)
  - **Фильтры** (deepObject, OpenAPI `CatalogFilter`): `filter[category_id]`, `filter[price_min]`, `filter[price_max]`, `filter[seller_id]`, `filter[attributes][<slug или uuid>]` - например `filter[category_id]=...&filter[price_min]=10000&filter[attributes][brand]=Apple`
  - **Код 200**: `PaginatedCatalogProducts` - `items[]` (`CatalogProductCard`: `id`, `name`, `min_price`, `has_stock`, `images`, …), `total_count`, `limit`, `offset`
  - **Код 400**: `{"code": "INVALID_REQUEST", "message": "Invalid sort parameter. Allowed: ..."}` (невалидный параметр сортировки)
  - **Код 500**: текст ошибки (прочие сбои)

- `GET /api/v1/catalog/facets`
  - **Query params**: `category_id` (обязательный UUID), `filter[attributes][<slug или uuid>]` (опционально - уже применённые фильтры для пересчёта счётчиков)
  - **Код 200**: `FacetsResponse` - `category_id`, `filters[]` (метаданные фильтров: `id`, `slug`, `name`, `type`, `value` / `min` / `max`), `facets[]` (`name`, `values[]` с полями `value` и `count`)
  - **Код 404**: `{"code": "CATEGORY_NOT_FOUND", "message": "..."}` (категория не найдена)
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

- `tests/integration/catalog/test_catalog.py::test_facets_returns_empty_list_for_empty_category` - фасеты возвращают пустой список для категории без товаров
- `tests/integration/catalog/test_catalog.py::test_facets_return_counts_per_filter_value` - фасеты возвращают корректные счётчики для каждого значения фильтра
- `tests/integration/catalog/test_catalog.py::test_catalog_returns_filtered_sorted_products` - каталог возвращает отфильтрованные и отсортированные товары (фильтр по категории, сортировка, пагинация)
- `tests/integration/catalog/test_catalog.py::test_invalid_sort_returns_400` - невалидный параметр сортировки возвращает 400
- `tests/integration/catalog/test_catalog.py::test_products_list_filters_only_visible_products` - список товаров фильтрует только видимые товары (по статусу и наличию на складе)

Требуемый в квесте тест `b2b_unavailable_returns_502` не реализован: данные каталога читаются из локальной БД B2C, без отдельного обращения к B2B - см. архитектурное решение выше.

Тесты успешно проходят (см. джобу tests).
