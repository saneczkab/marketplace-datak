# Design system

## Общие принципы

- **Светлая тема** — основная. Белые и синие тона в приоритете.
- **Desktop-only** — проектируем для экрана ≥1200px. Media queries для mobile не нужны в MVP.
- **Однородность** — все страницы и микросервисы используют одни CSS variables, spacing и паттерны компонентов.
- **CSS Modules** — основной способ стилизации. Файл `Component.module.css` рядом с компонентом.
- **Иконки** — emoji (как переключатель темы в Header). SVG sprite (`public/icons.svg`) — допустим для статичных иконок.

## CSS Variables (design tokens)

Глобальные tokens — в `src/index.css`. Компоненты **не хардкодят** цвета — используют variables.

### Светлая тема (default)

```css
:root,
:root[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --text-primary: #213547;
  --text-secondary: #666666;
  --header-bg: #2c3e50;
  --header-text: #ffffff;
  --footer-bg: #34495e;
  --footer-text: #ffffff;
  --border-color: #e0e0e0;
  --card-bg: #ffffff;
  --button-primary: #667eea;        /* основной синий акцент */
  --button-primary-hover: #5568d3;
  --button-danger: #e74c3c;
  --button-danger-hover: #c0392b;
  --accent-color: #667eea;
  --shadow: rgba(0, 0, 0, 0.1);
}
```

### Тёмная тема

Поддерживается через `data-theme="dark"` на `<html>` (управляется `themeStore`). При добавлении новых colors всегда определяй **обе** темы.

### Рекомендуемые дополнительные tokens

При необходимости добавляй в `:root` (согласованно во всех микросервисах):

```css
--radius-sm: 4px;
--radius-md: 8px;
--spacing-xs: 0.25rem;
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;
--container-max-width: 1200px;
--font-size-sm: 0.875rem;
--font-size-base: 1rem;
--font-size-lg: 1.25rem;
--font-size-xl: 1.5rem;
```

## Типографика

- Шрифт: `Inter, system-ui, Avenir, Helvetica, Arial, sans-serif`
- Базовый размер: `1rem`, line-height: `1.5`
- Заголовки страниц: `1.5rem–2rem`, font-weight `600`
- Вторичный текст: `var(--text-secondary)`

## Layout

```css
.container {
  max-width: var(--container-max-width, 1200px);
  margin: 0 auto;
  padding: 0 20px;
}
```

- Header / Footer — full width, контент внутри `.container`.
- Основной контент страницы — в `.container` или grid/flex внутри него.

## Компоненты (common)

Создавай в `src/components/common/` при втором использовании.

### Button

```css
.button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: var(--radius-sm, 4px);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: background-color 0.2s;
}
.primary {
  background-color: var(--button-primary);
  color: #ffffff;
}
.primary:hover {
  background-color: var(--button-primary-hover);
}
.danger {
  background-color: var(--button-danger);
  color: #ffffff;
}
```

### Card

```css
.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 2px 4px var(--shadow);
}
```

### Input

```css
.input {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm, 4px);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: var(--font-size-base);
}
.input:focus {
  outline: 2px solid var(--accent-color);
  outline-offset: 1px;
}
```

## Inline-стили

- **Избегай** inline-стилей для статичного оформления.
- **Допустимо** для динамических значений: `marginLeft` в дереве категорий, width progress bar.

## Состояния UI

| Состояние | Паттерн |
|-----------|---------|
| Loading | `<div className={styles.loading}>Загрузка...</div>` |
| Error | `<p className={styles.error}>Ошибка: {message}</p>`, цвет `--button-danger` или красный текст |
| Empty | `<p className={styles.placeholder}>Товары не найдены</p>`, `--text-secondary` |
| Disabled button | `opacity: 0.6; cursor: not-allowed` |

Не добавляй skeleton screens и spinner-библиотеки без запроса.

## Формат цен

Рубли и копейки. Реализуй `formatPrice(amount: number): string` в `src/utils/formatPrice.ts`:

| Условие | Формат | Пример |
|---------|--------|--------|
| Копейки = 0 | `{рубли} ₽` | `1 500 ₽` |
| Есть копейки | `{рубли},{кк} ₽` (2 знака) | `1 500,50 ₽` |

```typescript
export function formatPrice(amount: number): string {
  const rubles = Math.floor(amount);
  const kopecks = Math.round((amount - rubles) * 100);
  const formattedRubles = rubles.toLocaleString('ru-RU');
  if (kopecks === 0) {
    return `${formattedRubles} ₽`;
  }
  return `${formattedRubles},${String(kopecks).padStart(2, '0')} ₽`;
}
```

Используй **везде** вместо `.toFixed(2)`.

## Изображения

- Fallback: `/no-image.png` (из `public/`)
- Всегда указывай `alt` (название товара или описание)
- Не оптимизируй через сторонние CDN без запроса

## Доступность (a11y) — MVP-уровень

Строгий WCAG не требуется, но базовые правила обязательны:

- **Кнопки без текста** (emoji, иконки) — `aria-label` на русском.
- **Формы** — `<label>` связан с `<input>` через `htmlFor` / `id`.
- **Интерактивные элементы** — используй `<button>` / `<a>`, не `<div onClick>`.
- **Контраст** — текст на фоне должен быть читаемым (primary text на bg-primary).
- **Focus** — не сбрасывай outline без замены (`:focus-visible`).

Keyboard navigation для сложных виджетов (dropdown, tree) — по мере реализации, минимум Tab до всех интерактивных элементов.

## Тёмная тема

- Переключение через `themeStore` → `document.documentElement.setAttribute('data-theme', theme)`.
- Новые компоненты **обязаны** использовать CSS variables, а не фиксированные hex-цвета — тогда dark theme работает автоматически.

## Чего не делать

- Не подключать Tailwind, MUI, styled-components без явного запроса.
- Не создавать отдельную папку `styles/` для component styles — colocation с CSS Modules.
- Не добавлять mobile breakpoints.
- Не расставлять `data-tid`.
