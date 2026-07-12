# Архитектура: state, hooks, utils

## Zustand vs локальный state

### Zustand store — когда использовать

- Состояние нужно **на нескольких страницах** или в layout (корзина, авторизация, тема, счётчик избранного).
- Данные **мутируются** с бэкенда и должны быть консистентны глобально.
- Несколько компонентов подписываются на одни и те же данные.

Примеры: `cartStore`, `authStore`, `themeStore`.

### Локальный state (`useState`) — когда использовать

- Данные **только для одной страницы** (список товаров каталога, форма фильтров).
- UI-состояние: открыт/закрыт dropdown, expanded-узлы дерева категорий.
- Данные не нужны после ухода со страницы.

### Custom hooks — когда использовать

- Логика **переиспользуется** на 2+ страницах, но **не требует глобального store**.
- Инкапсуляция fetch + loading/error (например, `useBreadcrumbs`, `usePaginatedList`).
- Debounce, AbortController, синхронизация с URL.

**Правило:** store → hooks → local state. Не создавай store «на всякий случай».

## Store: паттерн

Store вызывает API **напрямую** (без отдельного service-слоя). Это текущий паттерн проекта.

```typescript
// src/store/cartStore.ts — эталон
interface CartStore {
  cart: Cart | null;
  loading: boolean;
  error: string | null;
  fetchCart: () => Promise<void>;
  addItem: (skuId: string, quantity?: number) => Promise<void>;
}

const useCartStore = create<CartStore>((set, get) => ({
  cart: null,
  loading: false,
  error: null,

  fetchCart: async () => {
    set({ loading: true, error: null });
    try {
      const cart = await cartApi.getCart();
      set({ cart, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
}));
```

Каждый async-action: `loading: true` → try/catch → `loading: false`, `error` при ошибке.

## Hooks: где хранить

| Тип hook | Расположение |
|----------|--------------|
| Общий для микросервиса | `src/hooks/useDebounce.ts` |
| Domain-specific, переиспользуемый | `src/hooks/usePaginatedQuery.ts` |
| Только для одного компонента | `src/components/common/ProductCard/useProductCard.ts` или рядом с page |

**Именование:** всегда `use` + PascalCase. Один hook — один файл.

### Рекомендуемые общие hooks

Создавайте по мере необходимости, не заранее:

- `useDebounce(value, delay)` — для поиска (delay 300ms).
- `usePaginatedQuery(fetcher, params)` — fetch + pagination state + URL sync.
- `useAsyncEffect(fn, deps)` — fetch в useEffect с AbortController.

### Отмена запросов (AbortController)

При fetch в `useEffect` отменяйте запрос при размонтировании или смене deps:

```typescript
useEffect(() => {
  const controller = new AbortController();
  fetchData({ signal: controller.signal });
  return () => controller.abort();
}, [categoryId, page]);
```

Проброс `signal` добавляйте в API-методы по мере необходимости.

### Debounce

- Поиск в каталоге: **300ms** debounce перед запросом.
- Не debounce клики и submit форм.

### Retry

- Автоматический retry **не используем** в MVP.
- При ошибке показываем текст и кнопку «Повторить» (опционально).

## Utils: где хранить

`src/utils/` — **чистые функции** без React и без side effects:

| Файл | Назначение |
|------|------------|
| `formatPrice.ts` | Форматирование рублей (см. [`design.md`](./design.md)) |
| `parseApiError.ts` | Извлечение `message` из ответа axios |
| `pagination.ts` | `offsetToPage`, `pageToOffset`, `buildPaginationParams` |
| `session.ts` | Генерация/чтение UUID session id |

Не создавай utils для однострочных операций — оставь inline.

## API-слой

```typescript
// src/api/products.ts — эталон
export const productsApi = {
  getProductsList: async (params: ProductsListParams): Promise<ProductsListResponse> => {
    const response = await apiClient.get<ProductsListResponse>('/api/v1/products', { params });
    return response.data;
  },
};
```

- Один файл на домен (`products.ts`, `orders.ts`, `auth.ts`).
- Реэкспорт из `src/api/index.ts`.
- `apiClient` — единственная точка настройки axios (interceptors, base URL, headers).

## Components

### `components/common/`

Переиспользуемые UI-блоки: `Button`, `Input`, `Pagination`, `ErrorMessage`, `Breadcrumbs`, `PageMeta`.

Создавайте common-комponent только при **втором** использовании. Первое — можно inline в page.

### `components/layout/`

`Layout` (Outlet), `Header`, `Footer` — общая оболочка. Не класть сюда business-компоненты.

### Pages

Страница = композиция hooks/stores + common-кomponentов + свой `.module.css`.

```
src/pages/Catalog/
  Catalog.tsx
  Catalog.module.css
  useCatalogFilters.ts   # опционально, если логика объёмная
```

## Обработка ошибок (MVP)

Достаточно `error: string | null` в state/store и отображения на экране:

```tsx
{error && <p className={styles.error}>Ошибка: {error}</p>}
```

Используйте `parseApiError(error)` из utils для единообразного извлечения текста из `{ code, message }`.

Toast/модалки — не в MVP, если не запрошено явно.

## Новая страница (чеклист)

1. `src/pages/MyPage.tsx` + `MyPage.module.css`
2. Типы в `src/types/` (если новые)
3. API-методы в `src/api/`
4. Store или hook — по правилам выше
5. Роут в `App.tsx`
6. Ссылка в `Header.tsx` (если нужна в навигации)
7. Breadcrumbs и PageMeta (см. [`routing-seo.md`](./routing-seo.md))
8. Юнит-тесты (см. [`testing.md`](./testing.md))
