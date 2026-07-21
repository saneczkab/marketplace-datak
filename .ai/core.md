# Core: общие правила фронтенда

## Стек (фиксированный)

- **React 19** + **TypeScript** (`strict: true`)
- **Vite** — сборка и dev-сервер
- **React Router DOM 7** — роутинг
- **Zustand** — глобальное состояние
- **Axios** — HTTP-клиент
- **CSS Modules** — стилизация компонентов

Дополнительные npm-библиотеки **приветствуются**, если они упрощают конкретную задачу (date-fns, clsx, uuid и т.д.). Запрещённых библиотек нет. Не добавляйте UI-kit (MUI, Ant Design и т.п.) без явного запроса — используйте CSS Modules и design tokens из [`design.md`](./design.md).

## MVP-ориентир

- Работаем в рамках **MVP**: код должен быть рабочим и поддерживаемым, без избыточной архитектуры «на будущее».
- **Только десктоп** — мобильная вёрстка не нужна. Минимальная ширина контента ~1200px (см. `max-width` в layout).
- Интерфейс **только на русском**.
- Loading/error/empty states обязательны на страницах с данными. Достаточно текста «Загрузка...» / «Ошибка: …» / «Не найдено» — skeleton screens не требуются.

## Единая структура микросервиса

Каждый фронтенд-микросервис (`b2c-frontend`, `b2b-frontend`, `moderation-frontend`) следует одной структуре:

```
src/
├── api/              # HTTP-клиенты (только axios через client.ts)
├── types/            # TypeScript-типы API (контракт с бэкендом)
├── store/            # Zustand stores
├── hooks/            # Переиспользуемые custom hooks
├── utils/            # Чистые функции без React
├── components/
│   ├── common/       # Переиспользуемые UI-компоненты
│   └── layout/       # Layout, Header, Footer
├── pages/            # Страницы (1 роут = 1 папка или 1 файл + .module.css)
├── assets/           # Статические ресурсы
├── App.tsx           # Роутинг
├── main.tsx          # Точка входа
└── index.css         # Глобальные CSS variables и reset
```

При создании новых папок сохраняйте единообразие между микросервисами.

## Слои и ответственность

| Слой | Ответственность |
|------|-----------------|
| `api/` | HTTP-запросы, маппинг query/body, возврат `response.data` |
| `types/` | Интерфейсы ответов и параметров API |
| `store/` | Глобальное состояние + side effects (fetch, mutate) |
| `hooks/` | Переиспользуемая логика React (fetch, debounce, pagination) |
| `utils/` | Форматирование, парсинг ошибок, работа с URL |
| `pages/` | Композиция UI, локальный state страницы |
| `components/common/` | Кнопки, инпуты, модалки, Pagination и т.д. |

## TypeScript

- `strict: true` — обязательно.
- `any` **запрещён**, кроме крайних случаев с комментарием `// eslint-disable-next-line` и обоснованием.
- Типы API — в `src/types/`, не дублировать inline в компонентах.
- Имена полей API — **snake_case** (как в бэкенде). Не переименовывать в camelCase на уровне типов и API-слоя.

## Именование и экспорты

| Сущность | Конвенция | Пример |
|----------|-----------|--------|
| Компонент | PascalCase | `ProductCard.tsx` |
| Store | `useXxxStore` / `xxxStore.ts` | `useCartStore`, `cartStore.ts` |
| Hook | `use` + PascalCase | `useProductList.ts` |
| Util | camelCase | `formatPrice.ts` |
| API-модуль | `xxxApi` объект | `productsApi`, `ordersApi` |
| CSS Module | `Component.module.css` | рядом с компонентом |

- **Страницы и layout-компоненты** — `default export`.
- **API-модули, utils, hooks, stores** — `named export` (API-объект) или `default export` (store hook), как в существующем `b2c-frontend`.
- **Common-комponentы** — `named export` (удобнее tree-shaking и реэкспорт).

## Комментарии

Комментарии — **только к неочевидной бизнес-логике**. Не комментировать каждую строку. Удалять `console.log` при правках затронутых файлов.

## Anti-patterns (топ ошибок)

1. **Переписывание проекта** — менять только то, что нужно для задачи.
2. **Код вне scope** — не рефакторить «заодно»; явный рефакторинг — отдельная задача для разработчика.
3. **Поломка существующей логики** — перед изменением API client, store, interceptors изучить текущее поведение.

Дополнительно:

- Не вызывать `axios`/`fetch` из компонентов — только через `src/api/`.
- Не менять `eslint.config.js`, `vite.config.ts`, `tsconfig.json` без прямой необходимости задачи.
- Не добавлять `data-tid`.
- Не трогать e2e/UI-тесты.

## Definition of Done

- [ ] TypeScript компилируется без ошибок (`npm run build`)
- [ ] ESLint проходит (`npm run lint`)
- [ ] Базовые юнит-тесты написаны (см. [`testing.md`](./testing.md))
- [ ] Loading / error / empty states на страницах с данными
- [ ] UI на русском
- [ ] Открыт PR из отдельной ветки (см. [`workflow.md`](./workflow.md))
