# RippleMate API

Backend API для RippleMate — платформы для запоминания чего угодно через бесконечный поток карточек с умным повторением.

## Стек

- **FastAPI** — асинхронный веб-фреймворк
- **PostgreSQL** + **SQLAlchemy** (async) — база данных и ORM
- **Alembic** — миграции БД
- **fastapi-users** — аутентификация (JWT)
- **Docker Compose** — локальный PostgreSQL
- **pytest** + **httpx** — тесты

## Структура проекта

```
app/
  api/routes/      # HTTP-эндпоинты
  core/            # конфигурация
  db/              # сессия БД, базовый класс моделей
  models/          # SQLAlchemy-модели
  repositories/    # слой доступа к данным
  services/        # слой бизнес-логики
  schemas/         # Pydantic-схемы запросов/ответов
  users.py         # настройка fastapi-users
alembic/           # миграции БД
tests/             # тесты pytest
```

## Установка и запуск

1. Клонируй репозиторий, создай виртуальное окружение и установи зависимости:
   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Скопируй `.env.example` в `.env` и заполни значения (список переменных ниже).

3. Подними PostgreSQL через Docker:
   ```
   docker compose up -d
   ```

4. Примени миграции:
   ```
   alembic upgrade head
   ```

5. Запусти сервер:
   ```
   uvicorn main:app --reload
   ```

6. Swagger-документация доступна на `http://127.0.0.1:8000/docs`.

## Переменные окружения (`.env`)

| Переменная | Описание |
|---|---|
| `POSTGRES_USER` | Пользователь БД |
| `POSTGRES_PASSWORD` | Пароль БД |
| `POSTGRES_DB` | Имя основной базы |
| `POSTGRES_TEST_DB` | Имя тестовой базы |
| `POSTGRES_HOST` | Хост БД |
| `POSTGRES_PORT` | Порт БД |
| `SECRET_KEY` | Секретный ключ для подписи JWT |
| `CORS_ORIGINS` | Список разрешённых origin'ов фронтенда через запятую |

## Тесты

Тесты используют отдельную БД (`POSTGRES_TEST_DB`), создать её нужно один раз:
```
docker exec <имя-контейнера-db> psql -U <user> -d <db> -c 'CREATE DATABASE ripplemate_test;'
```
Запуск тестов:
```
pytest -v
```
