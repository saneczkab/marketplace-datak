
# Использование uv 
Для добавления зависимости для определенного сервиса используйте команду
```
uv add fastapi --project services/b2b
```
заменив `fastapi` на требуемую зависимость и `b2b` на требуемый микросервис

Для запуска конкретного микросервиса 
```
uv run --project services/b2b uvicorn services.b2b.main:app
```