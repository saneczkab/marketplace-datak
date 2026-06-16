# US-B2B-12: Удаление SKU

## Что сделано

`DELETE /api/v1/skus/{sku_id}` (Bearer JWT) — продавец удаляет отдельный вариант
(SKU). Ownership проверяется через связь `sku -> product -> seller`, `seller_id`
берётся только из JWT. Удаление физическое (hard delete); каскад БД удаляет
характеристики SKU. Ответ — `204 No Content` (по OpenAPI `b2b.yaml`,
`operationId: deleteSku`).

### Порядок проверок (критичен)

Инлайн early-return в `services/sku_service.py::delete_sku`, в фиксированном
порядке:

1. SKU не найден → `404 NOT_FOUND`
2. SKU чужого продавца → `403 NOT_OWNER`
3. Товар `HARD_BLOCKED` → `403 FORBIDDEN` («Cannot delete SKU of hard-blocked product»)
4. `reserved_quantity > 0` → `409 CONFLICT` («Cannot delete SKU with active reserves»)

### Побочные эффекты

Считаются по статусу и `active_quantity`, зафиксированным до удаления:

- Если после удаления у товара не осталось SKU **и** товар был `ON_MODERATION` →
  статус товара переводится в `CREATED` и в Moderation отправляется событие
  `DELETED` (`moderation.product.deleted`). «Последний SKU» считается после
  логического удаления текущего.
- Если у удалённого SKU `active_quantity > 0` **и** товар был `MODERATED` → в B2C
  отправляется событие `SKU_OUT_OF_STOCK` (routing key `b2c.events`).

Ветки взаимоисключающие (разные статусы товара). Случай «последний SKU, но товар
`MODERATED`/`CREATED`» — намеренный no-op (flow определяет только переход
`ON_MODERATION → CREATED`).

## Запуск

```bash
make build up migrate
```

## Автотесты

```bash
make test
```

- `tests/integration/test_delete_sku.py`:
  - `delete_sku_succeeds`
  - `delete_sku_with_active_reserves_returns_409`
  - `last_sku_on_moderation_transitions_product_to_created`
  - `delete_sku_hard_blocked_product_returns_403`
  - `sku_out_of_stock_event_on_moderated_product`
  - `delete_sku_not_owner_returns_403`, `delete_sku_not_found_returns_404`,
    `delete_sku_no_auth_returns_401`

## ADR

**Упорядочивание guardrail-проверок при удалении SKU**

Рассмотрены три подхода: (1) инлайн early-return проверки в `delete_sku`;
(2) единый метод `validate_deletion`; (3) проверки в Pydantic-сериализаторе.
Выбран вариант (1) — каждая проверка отдельным `if ... raise`, повторяет
паттерн `product_service.remove_product`. Критерии: читаемость
последовательности проверок (порядок виден буквально и ревьюится) и риск
перепутать порядок (`HARD_BLOCKED` должен идти до `reserved_quantity`) —
последовательность в одном месте, как в существующем прецеденте. Вариант (2)
прячет порядок за вызовом, вариант (3) не выражает проверки, зависящие от БД
(резервы, ownership, статус), и размазывает логику по слоям.

**Формат ответа: `204` vs `200 {"ok": true}`**

OpenAPI (`b2b.yaml`) предписывает `204 No Content` — это связывающий контракт для
других команд, поэтому реализован `204`. Канон-flow `b2b-flows.md` указывает
`200 {"ok": true}` — расхождение задокументировано и вынесено команде protocols.

## Слои

- **Exceptions** (`exceptions/sku.py`) — `SkuConflictError` (→ 409).
- **CRUD** (`crud/sku.py`) — `hard_delete_sku` (delete + flush, без commit).
- **CRUD** (`crud/outbox.py`) — `build_b2c_sku_out_of_stock_payload` /
  `enqueue_b2c_sku_out_of_stock` (единый источник payload `SKU_OUT_OF_STOCK`;
  `inventory_service` делегирует сюда).
- **Service** (`services/sku_service.py`) — `delete_sku`: упорядоченные
  guardrails + побочные эффекты, единый commit.
- **API** (`api/sku.py`) — `DELETE /api/v1/skus/{sku_id}` (204), маппинг
  доменных исключений на конверт ошибки.
