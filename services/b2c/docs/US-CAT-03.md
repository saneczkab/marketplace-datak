# US-CAT-03: карточка товара

## Что сделано

Реализована публичная карточка товара для покупателя: полное описание, изображения, характеристики и список SKU с ценами и наличием. Ответ соответствует OpenAPI-схеме `CatalogProductDetail` - расширение `CatalogProductCard` полями `description`, `attributes` и `skus`.

Данные каталога читаются из локальной БД B2C, без отдельного обращения к B2B - это архитектурное решение - хранить данные в B2C и через очередь сообщений управлять обновлениями данных в сервисах.

В ответе нет внутренних полей продавца: `cost_price`, `reserved_quantity`, `active_quantity`, `discount` - только публичные `price`, `old_price`, `available_quantity`.
Недоступные товары (`status != MODERATED`, `deleted = true`) возвращают 404. SKU с нулевым остатком остаётся в списке с `available_quantity = 0`; на уровне товара `has_stock = false`.

### API

- `GET /api/v1/catalog/products/{product_id}`
  - **Код 200**: `CatalogProductDetail` - поля карточки каталога (`id`, `name`, `slug`, `min_price`, `has_stock`, `images`, `category`, `seller`, ...) + `description`, `attributes`, `skus[]` (`CatalogSku`: `id`, `price`, `old_price`, `available_quantity`, `images`, ...)
  - **Код 404**: `{"code": "NOT_FOUND", "message": "..."}` - товар заблокирован, удалён или не найден

## Запуск

```bash
make build up migrate
```

## Автотесты

```bash
make test
```

`tests/integration/catalog/test_product.py`
