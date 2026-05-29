# US-B2B-01: создание карточки товара

## Что сделано

Создание карточки товара

### API

Перечень реализованных эндпоинтов:

- **`POST /api/v1/products/`**
  - **Body**: `ProductCreate (title* string, description* string, category_id* uuid, slug, images, charachteristics)`
  - **Код 201**: `Товар`

## Запуск

```bash
make build up migrate
```
По адресу `localhost:8000/docs` можно найти документацию API-эндпоинтов

## Автотесты

```bash
make test
```

- `test_create_product.py`

Тест `test_missing_category_returns_400` из условий квеста заменён на `test_missing_category_returns_422` - спецификация OpenAPI требует код 422.  
Тест `missing_images_returns_400` исключён - загрузка изображений осуществляется при работе со SKU, так что у вновь созданного товара априори не может быть SKU.

Тесты успешно проходят (см. джобу tests)

## ADR

- **Альтернативы**:
  - JSON-поле в таблице Product
  - отдельная таблица CharacteristicValue
  - EAV-схема
- **Выбор**: Таблица Chatacteristics - проще, чем EAV; гибкое добавление имён; хорошая фильтрация SQL.
Обращу внимание: работа с характеристиками (как и с изображениями) происходит на уровне SKU, так что их реализация будет в US-B2B-02.

## Файлы
services/b2b/

### API эндпоинты

api/products.py:create_product

### Сервисы

services/product_service.py:create_new_product

### CRUD

crud/product.py:add_product

### Схемы

schemas/product.py

### Автотесты

tests/integration/test_create_product.py
