# Тестирование

## Scope

ИИ **пишет юнит-тесты** фронтенда, покрывающие базовые кейсы.

ИИ **не пишет и не меняет**:

- e2e тесты (Playwright)
- UI-автотесты
- Скриншотные / visual regression тесты
- `data-tid` атрибуты (расставляет тестировщик)

## Стек (рекомендуемый)

При настройке тестов в микросервисе используй:

- **Vitest** — test runner (нативная интеграция с Vite)
- **@testing-library/react** — рендер компонентов
- **@testing-library/jest-dom** — matchers
- **@testing-library/user-event** — симуляция действий

Добавление этих devDependencies приветствуется при первой задаче с тестами.

## Что тестировать

### Для страниц (минимум)

- Рендер loading state
- Рендер error state при failed fetch
- Рендер empty state
- Рендер данных при successful mock

### Не нужно (нетривиальные случаи)

- Полные integration flows (login → cart → checkout)
- Edge cases API (409, idempotency conflicts)
- Visual/layout тесты
- Accessibility audit automation
- Performance тесты

## Структура файлов

```
src/
├── utils/
│   ├── formatPrice.ts
│   └── formatPrice.test.ts      # рядом с файлом
├── components/common/Button/
│   ├── Button.tsx
│   └── Button.test.tsx
├── store/
│   ├── cartStore.ts
│   └── cartStore.test.ts
└── pages/Catalog/
    ├── Catalog.tsx
    └── Catalog.test.tsx
```

Именование: `*.test.ts` / `*.test.tsx`.

## Паттерны

### Utils

```typescript
import { describe, it, expect } from 'vitest';
import { formatPrice } from './formatPrice';

describe('formatPrice', () => {
  it('форматирует целые рубли без копеек', () => {
    expect(formatPrice(1500)).toBe('1 500 ₽');
  });

  it('форматирует рубли с копейками', () => {
    expect(formatPrice(1500.5)).toBe('1 500,50 ₽');
  });
});
```

### Components

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

it('вызывает onClick при клике', async () => {
  const onClick = vi.fn();
  render(<Button onClick={onClick}>Купить</Button>);
  await userEvent.click(screen.getByRole('button', { name: 'Купить' }));
  expect(onClick).toHaveBeenCalledOnce();
});
```

### Store (mock API)

```typescript
import { vi } from 'vitest';

vi.mock('../api', () => ({
  cartApi: {
    getCart: vi.fn().mockResolvedValue({ items: [], summary: { total_items: 0, total_price: 0 } }),
  },
}));
```

### Hooks

Используй `@testing-library/react` → `renderHook`.

## Mocking

- **API** — mock `src/api/*` modules через `vi.mock`.
- **Router** — `MemoryRouter` wrapper при тестировании компонентов с `Link`/`useNavigate`.
- **Zustand store** — reset state в `beforeEach` или mock store module.

## Scripts

Добавь в `package.json` при настройке:

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run"
  }
}
```

## Когда писать тесты

- **Новый util/hook/store** — тесты в том же PR.
- **Новая common-кomponenta** — базовый render test.
- **Новая страница** — loading/error/success render tests.
- **Bug fix** — regression test, если баг в логике (не в вёрстке).

## Когда НЕ писать тесты

- Чисто визуальные изменения CSS.
- Одноразовые page-specific компоненты без логики.
- Конфигурационные файлы.
