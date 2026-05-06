# US-CAT-05: навигация по категориям

## Что сделано

Реализована навигация по категориям для B2C каталога: запросы на получение дерева категорий, деталей категории, а также генерация хлебных крошек (цепочка от корня до категории).

### API

Перечень реализованных эндпоинтов:

- `GET /api/v1/categories`
  - **Query/Path params**: —
  - **Код 200**: `CategoryTreeResponse` — вложенная структура категорий (дерево) от корня
  - **Код 404**: `Root category not found. Check database` (если в БД нет корня)
  - **Код 503**: текст ошибки (прочие сбои)
- `GET /api/v1/categories/{id}`
  - **Query/Path params**: `id` (path), `include_product_count` (query, default `false`)
  - **Код 200**: `CategoryInfoResponse` — информация о категории (+ опционально `product_count`)
  - **Код 400**: `id must be a valid UUID` (невалидный UUID)
  - **Код 404**: `Category with id <id> not found`
  - **Код 503**: текст ошибки (прочие сбои)
- `GET /api/v1/breadcrumbs`
  - **Query/Path params**: ровно один из `category_id` или `product_id` (оба сразу → 400)
  - **Код 200**: `BreadcrumbResponse` — список `data[]` (путь от корня до текущей категории) + `meta.resolved_via`
  - **Код 400**: `Either category_id or product_id must be provided` (нет параметров) / неоднозначные параметры (переданы оба)
  - **Код 404**: `Category with id <id> not found` (категория не найдена)
  - **Код 422**: `Category with id <id> has missing parent <parent_id>` (orphan node: сломанная иерархия)
  - **Код 503**: текст ошибки (прочие сбои)

## Запуск

```bash
make build up migrate
```

По адресу `localhost:8000/docs` можно найти документацию API-эндпоинтов.

## Автотесты

```bash
make test
```

- `tests/integration/test_categories_navigation.py::test_category_tree_returns_nested_structure` — дерево категорий собирается в вложенную структуру
- `tests/integration/test_categories_navigation.py::test_breadcrumbs_return_path_from_root` — хлебные крошки возвращают путь от корня до категории
- `tests/integration/test_categories_navigation.py::test_unknown_category_returns_404` — неизвестная категория → 404
- `tests/integration/test_categories_navigation.py::test_orphan_node_returns_422` — orphan node (битая иерархия) → 422
- `tests/integration/test_categories_navigation.py::test_ambiguous_params_returns_400` — переданы и `category_id`, и `product_id` → 400

Тесты успешно проходят (см. джобу tests).

## ADR

- **Альтернативы**:
  - `ltree` в PostgreSQL: быстрые запросы пути/поддерева, но усложняет запись/валидации и переносимость
  - adjacency list (parent_id) + рекурсивные запросы (CTE): простая модель, но хлебные крошки требуют рекурсии, а orphan node нужно явно детектить при чтении/записи
  - materialized path (строка пути/массив): быстрые хлебные крошки, но сложнее поддерживать консистентность при перемещениях узлов
- **Выбор**: adjacency list. Критерии: 
  - скорость запроса хлебных крошек достигается рекурсией/кешированием дерева без усложнения схемы
  - обнаружение orphan node делается детерминированно при построении цепочки родителей (если родитель не найден → 422)

