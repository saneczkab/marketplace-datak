# US-CAT-04: блок похожих товаров

## Что сделано

Реализован эндпоинт **`GET /api/v1/products/{id}/similar`**: проверка существования товара и категории, выборка до `limit` (по умолчанию 8) товаров из поддерева категории, заданной query-параметром **`category`**, с исключением текущего `id`. В CRUD используется обход дерева категорий от переданного узла вниз (`get_category_descendants`), фильтр `Product.category_id.in_(...)`, сортировка **`created_at` по убыванию**, пагинация `offset`/`limit`. Ответ — **`SimilarProductsResponse`** (алиас **`ProductShortListResponse`**): `items`, `total_count`, `limit`, `offset`. Для элементов списка **`ProductShort`** сейчас подставляются заглушки: `image=""`, `price=0.0`, `in_stock=False`, `is_in_cart=False` (без подтягивания SKU/картинки из БД).

### API

- **`GET /api/v1/products/{id}/similar`**
  - **Path**: `id` — UUID товара.
  - **Query**: `category` — UUID категории (**обязательный**); `limit` — по умолчанию `8`; `offset` — по умолчанию `0`.
  - **Код 200**: объект списка коротких карточек — `items` (массив `ProductShort`: `id`, `title`, `image`, `price`, `in_stock`, `is_in_cart`), `total_count`, `limit`, `offset`; при отсутствии кандидатов — **`items`: `[]`**, `total_count`: `0`**.
  - **Код 400**: неизвестная `category` (`CategoryNotFoundError`), иные `ValueError` из обработчика.
  - **Код 404**: товар с `id` не найден (`ProductNotFoundError`).
  - **Код 422**: отсутствует обязательный query-параметр `category` (валидация FastAPI).

## Файлы

| Файл | Назначение |
|------|------------|
| `api/product.py` | Роут `GET /{id}/similar`, привязка зависимостей, маппинг исключений в HTTP-коды. |
| `services/product_service.py` | `get_similar_products`: проверка товара и категории, вызов CRUD, сборка `SimilarProductsResponse` из ORM. |
| `crud/product.py` | `get_similar_products`, `get_category_descendants` — область категорий и SQL-выборка похожих. |
| `schemas/product.py` | `ProductShort`, `ProductShortListResponse`, алиас `SimilarProductsResponse`. |
| `exceptions/product.py` | `ProductNotFoundError` для 404. |
| `exceptions/category.py` | `CategoryNotFoundError` для 400 при неверной категории. |
| `tests/integration/test_similar.py` | Интеграционные сценарии similar / empty / 404 / неверная категория. |
| `tests/integration/conftest.py` | Фикстуры `similar_products_data`, `one_product_category`, тип `SimilarProductsData`. |

## Запуск

```bash
make build up migrate
```

По адресу `localhost:8000/docs` можно найти документацию API-эндпоинтов.

## Автотесты

```bash
make test
```

- **`tests/integration/test_similar.py::test_similar_returns_up_to_8_from_same_category`** — 200, не более 8 позиций, текущий товар не в `items`, только кандидаты из той же категории фикстуры.
- **`tests/integration/test_similar.py::test_empty_category_returns_200_empty_list`** — 200, пустой `items` и `total_count == 0`, если в выбранном поддереве категории нет других товаров (фикстура с «чужой» пустой категорией в query).
- **`tests/integration/test_similar.py::test_unknown_product_returns_404`** — несуществующий `id` товара.
- **`tests/integration/test_similar.py::test_unknown_category_returns_400`** — несуществующий `category` в query.

Тесты успешно проходят (см. джобу tests);

## ADR

**Альтернативы выборки похожих:**

1. **Случайная выборка** (`ORDER BY RANDOM()` и аналоги) — богаче по ощущению «подборки», но нагрузка на БД и **нестабильный** порядок при повторных запросах.
2. **Сходство по характеристикам** — ближе к «похожести», выше сложность запросов и поддержки на MVP.
3. **Кэш предвычисленных рекомендаций** — предсказуемость и скорость чтения, но отдельное хранилище, пайплайн обновления и согласованность с каталогом.

**Выбор:** детерминированная выборка из поддерева категории с **`ORDER BY created_at DESC`** и фиксированным `limit`/`offset` — простой запрос к уже имеющейся модели каталога, одинаковый результат при повторе запроса при неизменных данных.

**Критерии:** (1) **сложность MVP** — один SQL без фоновых джоб и без скоринга по атрибутам; (2) **консистентность при повторных запросах** — фиксированный порядок по дате создания вместо случайной перетасовки.
