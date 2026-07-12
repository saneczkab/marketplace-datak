# API и бэкенд

## Принципы

1. **Источник правды** — код бэкенда в `services/{b2c,b2b,moderation}/`.
2. Перед новой интеграцией читай: `api/*.py`, `schemas/*.py`, `middlewares/token_verification.py`.
3. **Не менять бэкенд.** Если нужны изменения API — сообщить разработчику.
4. Типы на фронте (`src/types/`) повторяют **snake_case** полей бэкенда.

## Env-переменные

Каждый фронтенд-микросервис настраивает base URL своего бэкенда:

```env
# b2c-frontend
VITE_API_BASE_URL=http://localhost:8000

# b2b-frontend (планируется)
VITE_API_BASE_URL=http://localhost:8001

# moderation-frontend (планируется)
VITE_API_BASE_URL=http://localhost:8002
```

## Формат ошибок

Бэкенды возвращают структурированные ошибки:

```json
{
  "code": "NOT_FOUND",
  "message": "Описание ошибки",
  "details": []
}
```

HTTP 422 (validation):

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [...]
}
```

На фронте извлекайте `message` для отображения пользователю. Реализуйте `parseApiError` в `src/utils/parseApiError.ts`.

## Пагинация, фильтры, сортировка

### Общий паттерн (offset-based)

Все list-endpoints используют:

| Query param | Тип | Default | Описание |
|-------------|-----|---------|----------|
| `limit` | int | 20 | Размер страницы (max 100) |
| `offset` | int | 0 | Смещение |

Ответ:

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  limit: number;
  offset: number;
}
```

### Синхронизация с URL

Храните состояние списков в **URL search params** (React Router `useSearchParams`):

```
/catalog?category=<uuid>&page=2&sort=popularity&search=телефон
```

Конвертация:

```typescript
const page = parseInt(searchParams.get('page') || '1', 10);
const offset = (page - 1) * limit;
```

При смене фильтра сбрасывайте `page` на `1`.

### Фильтры (B2C каталог)

- Query param `filter` — **JSON-строка** с полями `category_id`, `price_min`, `price_max`, `seller_id`, `attributes`.
- Facets: `GET /api/v1/catalog/facets?category_id=...&filter=...`
- Sort (B2C products): `popularity` (default), другие значения — смотреть `product_service` / `InvalidSortError`.

### Поиск

- Query param `search` — строка.
- Debounce 300ms на фронте перед запросом.

---

## B2C Backend (`services/b2c/`)

Порт по умолчанию: **8000**. Prefix большинства роутов: `/api/v1`.

### Авторизация

| Endpoint | Метод | Auth |
|----------|-------|------|
| `/api/v1/auth/register` | POST | — |
| `/api/v1/auth/login` | POST | опционально `X-Session-Id` (UUID) для merge корзины |
| `/api/v1/auth/logout` | POST | Bearer |
| `/api/v1/auth/refresh` | POST | `refresh_token` в body |
| `/api/v1/auth/me` | GET | Bearer |

**LoginResponse:** `access_token`, `refresh_token`, `expires_in`, `token_type`.

**Заголовки:**
- `Authorization: Bearer <access_token>` — для защищённых endpoints.
- `X-Session-Id: <uuid>` — для анонимной корзины.

> **Важно:** `X-Session-Id` должен быть **валидным UUID**. Генерируйте через `crypto.randomUUID()` или библиотеку `uuid`.

### Защищённые пути (Bearer обязателен)

- `/api/v1/auth/me`, `/api/v1/auth/logout`
- `/api/v1/favorites/*`
- `/api/v1/orders/*`

### Корзина (`/api/v1/cart`)

- Аноним: `X-Session-Id` (UUID).
- Авторизован: `Authorization: Bearer` (session id не нужен).
- Merge при логине: `POST /api/v1/cart/merge` — Bearer + `X-Session-Id`.

| Endpoint | Метод |
|----------|-------|
| `/api/v1/cart` | GET, DELETE |
| `/api/v1/cart/items` | POST |
| `/api/v1/cart/items/{sku_id}` | PATCH, DELETE |
| `/api/v1/cart/validate` | POST |
| `/api/v1/cart/merge` | POST |

### Каталог и продукты

| Prefix | Основные endpoints |
|--------|-------------------|
| `/api/v1/catalog` | categories tree, filters, facets, collections, banners, products |
| `/api/v1/products` | list (paginated), product SKUs |
| `/api/v1/breadcrumbs` | `?category_id=` или `?product_id=` |

**Breadcrumbs response:** `{ data: BreadcrumbItem[], meta: BreadcrumbMeta }`.

### Заказы (`/api/v1/orders`, Bearer)

| Endpoint | Метод | Особенности |
|----------|-------|-------------|
| `/api/v1/orders` | GET | `limit`, `offset`, `status` |
| `/api/v1/orders` | POST | Header `Idempotency-Key: <uuid>` |
| `/api/v1/orders/{id}` | GET | |
| `/api/v1/orders/{id}/cancel` | POST | |

### Избранное (`/api/v1/favorites`, Bearer)

- GET — paginated list
- PUT `/{product_id}` — add (204)
- DELETE `/{product_id}` — remove (204)

### Подписки (`/api/v1/subscriptions`)

- POST subscribe / DELETE unsubscribe по `product_id`.

### Ожидаемые B2C-страницы (ориентир по API)

| Страница | API |
|----------|-----|
| Главная | banners, collections |
| Каталог | catalog/products, categories, facets, filters |
| Товар | catalog/products/{id}, SKUs, similar |
| Корзина | cart |
| Auth (login/register) | auth |
| Избранное | favorites |
| Заказы (список/детали/создание) | orders |
| Профиль | auth/me |

---

## B2B Backend (`services/b2b/`)

Prefix: `/api/v1`. Порт — уточнить в docker-compose (обычно отличный от B2C).

### Авторизация

| Endpoint | Метод |
|----------|-------|
| `/api/v1/auth/register` | POST |
| `/api/v1/auth/login` | POST |
| `/api/v1/auth/logout` | POST (`refresh_token` query) |
| `/api/v1/auth/refresh` | POST (`refresh_token` query) |

**TokenResponse:** `user_id`, `access_token`, `refresh_token`, `token_type`, `expires_in`.

### Защищённые prefixes (Bearer)

- `/api/v1/products`
- `/api/v1/skus`
- `/api/v1/invoices`

### Основные endpoints

| Prefix | Назначение |
|--------|------------|
| `/api/v1/products` | CRUD товаров продавца (list с `limit`, `offset`, `status`, `search`) |
| `/api/v1/skus` | CRUD SKU |
| `/api/v1/categories` | Категории |
| `/api/v1/invoices` | Накладные (list paginated) |
| `/api/v1/inventory` | reserve / unreserve / fulfill |
| `/api/v1/images` | Загрузка изображений |
| `/api/v1/public/products` | Публичный каталог (для B2C sync) |
| `/api/v1/moderation/events` | События модерации (service-to-service) |

### Ожидаемые B2B-страницы

| Страница | API |
|----------|-----|
| Login / Register | auth |
| Список товаров | products |
| Создание/редактирование товара | products, skus, images, categories |
| Накладные | invoices |
| Склад | inventory |

---

## Moderation Backend (`services/moderation/`)

Prefix: `/api/v1`.

### Авторизация

Защищённые prefixes (Bearer JWT):

- `/api/v1/tickets`
- `/api/v1/queue`
- `/api/v1/blocking-reasons`

> Endpoints регистрации/логина модератора в текущем коде **не выделены** — при реализации auth-store ориентируйтесь на паттерн B2B/B2C и middleware `token_verification.py`.

### Основные endpoints

| Prefix | Назначение |
|--------|------------|
| `/api/v1/queue/claim` | POST — взять следующий тикет (204 если очередь пуста) |
| `/api/v1/tickets/{id}/approve` | POST |
| `/api/v1/tickets/{id}/block` | POST |
| `/api/v1/blocking-reasons` | CRUD причин блокировки |
| `/api/v1/b2b/events` | Service-to-service (не для фронта) |

### Ожидаемые Moderation-страницы

| Страница | API |
|----------|-----|
| Очередь модерации | queue/claim |
| Карточка тикета | tickets approve/block |
| Справочник причин | blocking-reasons |

---

## API Client (axios)

Единый `src/api/client.ts` на микросервис:

```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});
```

### Request interceptor

- Подставлять `Authorization: Bearer` из auth store / localStorage.
- Для B2C: `X-Session-Id` (UUID) для анонимных запросов корзины.

### Response interceptor

- Логировать ошибки в dev.
- Пробрасывать `Promise.reject(error)` — обработка в store/hook.

### Idempotency

Для `POST /api/v1/orders` генерировать `Idempotency-Key: crypto.randomUUID()` на каждую попытку создания заказа.

## Service keys

Заголовок `X-Service-key` используется **только** для service-to-service endpoints (`/api/v1/b2b/events`). **Фронтенд не отправляет** service keys.
