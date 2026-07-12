# Workflow: Git, PR, scope

## Результат работы ИИ

**Готовый результат** — открытый **Pull Request** из отдельной ветки. Не коммит в `main`.

## Git

### Запрещено

- Коммиты и push в `main`.
- Force push.
- Изменение git config.
- `--no-verify`, `--no-gpg-sign` (skip hooks).

### Обязательный процесс

1. Создать ветку от `main`:
   ```
   git checkout main
   git pull
   git checkout -b {microservice}-{short-description}
   ```
   Пример: `b2c-catalog-filters`, `b2b-product-form`.

2. Внести изменения **только в scope задачи**.

3. Проверить:
   ```
   npm run lint
   npm run build
   npm run test:run   # когда настроены тесты
   ```

4. Commit с **Conventional Commits**:
   ```
   feat(b2c): add favorites page
   fix(b2c): use UUID for session id
   test(b2c): add formatPrice unit tests
   refactor(b2c): extract Breadcrumbs component
   ```

   Формат: `{type}({scope}): {description}`
   - type: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`
   - scope: `b2c`, `b2b`, `moderation`

5. Push и создать PR:
   ```
   git push -u origin HEAD
   gh pr create --title "..." --body "..."
   ```

### PR description (минимум)

```markdown
## Summary
- Кратко что сделано

## Test plan
- [ ] npm run lint
- [ ] npm run build
- [ ] npm run test:run
- [ ] Ручная проверка: ...
```

## Scope задачи

### Делать

- Минимальный diff под задачу.
- Следовать существующим паттернам в микросервисе.
- Читать код бэкенда для API-интеграции.

### Не делать без отдельной задачи

- Масштабный рефакторинг.
- Переписывание unrelated файлов.
- «Улучшения» вне запроса.

Если видишь необходимость рефакторинга — **опиши в PR comment** или отдельным пунктом в description, но не делай в том же PR.

## Работа с бэкендом

| Действие | Разрешено |
|----------|-----------|
| Читать код `services/b2c`, `b2b`, `moderation` | ✅ |
| Менять код бэкенда | ❌ |
| Добавлять frontend workaround | ✅ (если API поддерживает) |
| Запросить изменение API | ✅ — описать в PR для разработчика |

Если фронтенд **не может** реализовать задачу без изменения бэкенда:

1. Реализуй всё, что возможно.
2. В PR явно опиши блокер: какой endpoint/поле нужно добавить/изменить.
3. Не меняй бэкенд самостоятельно.

## Конфигурационные файлы

Менять `eslint.config.js`, `vite.config.ts`, `tsconfig.json`, `package.json` — **только если задача этого требует** (например, добавление vitest или новой зависимости для конкретной feature).

## Code review

PR проверяет **разработчик**. ИИ должен облегчить review:

- Понятные commit messages.
- PR description с test plan.
- Небольшие focused PR (одна feature/fix).
- Без лишних файлов и debug-кода.

## MVP-качество

Приоритет: **работает, читаемо, тестируемо, минимальный diff**.

Не нужно:

- Идеальная архитектура «на вырост».
- Преждевременная оптимизация.
- Полное покрытие тестами.

Нужно:

- Корректная API-интеграция по коду бэкенда.
- Loading/error/empty states.
- Базовые unit tests.
- Единообразие с существующим кодом микросервиса.

## Запреты

- `data-tid` — не добавлять.
- e2e / UI tests — не трогать.
- main branch — не коммитить.
- Backend code — не менять.
