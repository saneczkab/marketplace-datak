# Роутинг, breadcrumbs, SEO, 404

## React Router

Роутинг настраивается в `App.tsx`. Layout с `Outlet` оборачивает все страницы.

```tsx
<Route path="/" element={<Layout />}>
  <Route index element={<Home />} />
  <Route path="catalog" element={<Catalog />} />
  <Route path="product/:id" element={<Product />} />
  <Route path="cart" element={<Cart />} />
  <Route path="*" element={<NotFound />} />
</Route>
```

### Правила маршрутов

- **kebab-case** в URL: `/order-history`, `/my-products`.
- **Параметры** — `:id`, `:slug` (uuid или slug — по API).
- **Query params** — для фильтров, пагинации, сортировки (не path segments).
- Каждый новый роут — **404-safe**: неизвестные пути попадают на `NotFound`.

### Ориентир по бэкенду

Количество страниц будет расти. При добавлении страницы:

1. Найди соответствующий router в `services/{backend}/api/`.
2. Создай page + API + types.
3. Добавь route в `App.tsx`.
4. Добавь в Header/sidebar, если нужна навигация.

## B2C: текущие и ожидаемые маршруты

| Path | Страница | Query params |
|------|----------|--------------|
| `/` | Главная | — |
| `/catalog` | Каталог | `category`, `page`, `sort`, `search`, `filter` |
| `/product/:id` | Товар | опционально `sku` |
| `/cart` | Корзина | — |
| `/favorites` | Избранное | `page` |
| `/login`, `/register` | Авторизация | `redirect` |
| `/orders` | Список заказов | `page`, `status` |
| `/orders/:id` | Детали заказа | — |
| `/checkout` | Оформление | — |

## B2B: ожидаемые маршруты

| Path | Страница |
|------|----------|
| `/login`, `/register` | Auth |
| `/products` | Список товаров |
| `/products/new` | Создание |
| `/products/:id` | Редактирование |
| `/invoices` | Накладные |
| `/invoices/:id` | Детали накладной |

## Moderation: ожидаемые маршруты

| Path | Страница |
|------|----------|
| `/queue` | Очередь (claim ticket) |
| `/tickets/:id` | Карточка тикета |
| `/blocking-reasons` | Справочник причин |

## Breadcrumbs

### API

B2C: `GET /api/v1/breadcrumbs?category_id=<uuid>` или `?product_id=<uuid>`.

Response:

```typescript
interface BreadcrumbItem {
  id: string;
  slug: string;
  name: string;
  url: string;
  level: number;
  is_current: boolean;
}
```

### Компонент

Создай `src/components/common/Breadcrumbs/Breadcrumbs.tsx`:

- Fetch через hook `useBreadcrumbs(categoryId?, productId?)`.
- Рендер: `Link` для всех items кроме `is_current` (текущий — `<span>`).
- Размещай под Header, над заголовком страницы.
- Используй на: Catalog, Product, Category pages.

### URL mapping

Поле `url` с бэкенда может быть slug-based — маппь на React Router paths (`/catalog?category=${id}` или `/product/${id}`) согласно вашей схеме роутов.

## SEO и meta-теги

### Компонент PageMeta

Создай `src/components/common/PageMeta/PageMeta.tsx` на базе side effect (без react-helmet, если не добавлена библиотека):

```tsx
interface PageMetaProps {
  title: string;
  description?: string;
  keywords?: string[];
  ogTitle?: string;
  ogDescription?: string;
  ogImage?: string;
}

// useEffect → document.title, meta tags
```

### Источники данных

- **Категория:** `CategoryInfoResponse.seo`, `meta_tags` (`/api/v1/catalog/categories/{id}`).
- **Товар:** SEO-поля из product detail response.
- **Статичные страницы:** hardcoded title/description на русском.

### Минимальный набор meta

```html
<title>{title} — Datak</title>
<meta name="description" content="..." />
<meta property="og:title" content="..." />
<meta property="og:description" content="..." />
<meta property="og:image" content="..." />  <!-- если есть -->
```

### Title pattern

- `{PageTitle} — Datak` для B2C.
- `{PageTitle} — NeoMarket B2B` для B2B.
- `{PageTitle} — Модерация` для Moderation.

## Страница 404

`src/pages/NotFound/NotFound.tsx`:

- Заголовок: «Страница не найдена»
- Текст: «Запрашиваемая страница не существует»
- Ссылка на главную
- `<PageMeta title="Страница не найдена" />`
- Route: `<Route path="*" element={<NotFound />} />` — последний среди routes

## Protected routes

Для страниц, требующих авторизации (orders, favorites, B2B products):

```tsx
// src/components/common/ProtectedRoute/ProtectedRoute.tsx
// Redirect на /login?redirect=<current_path> если нет токена
```

Проверяй наличие `access_token` в auth store. При 401 от API — clear tokens + redirect.

## Redirect после login

Сохраняй `redirect` query param:

```
/login?redirect=/orders
```

После успешного login → `navigate(redirect || '/')`.

## Навигация

- Основные ссылки — в `Header.tsx`.
- B2B/Moderation могут использовать sidebar — создай `components/layout/Sidebar.tsx` по аналогии с Header.
- Active link: `NavLink` из react-router или className по `useLocation()`.
