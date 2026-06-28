# Дом за рубль за скрепку

Backend, frontend и Telegram-бот для MVP-проекта обменной цепочки: пользователь подаёт оффер, админ модерирует и публикует его, другой пользователь предлагает свой предмет в обмен, админ обрабатывает сделку.

## Стек

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL.
- Frontend: React, Vite, TypeScript.
- Bot: aiogram, HTTP-клиент к backend.
- Tests: pytest, FastAPI TestClient, httpx MockTransport.

## Архитектура

Backend находится в корне этого workspace:

- `app/api/routers` — HTTP routers.
- `app/db/models` — SQLAlchemy models.
- `app/schemas` — Pydantic request/response schemas.
- `app/services` — бизнес-логика.
- `alembic/versions` — миграции БД.
- `tests` — backend и bot-client тесты.

Frontend находится в `frontend`:

- публичный каталог офферов;
- форма подачи оффера;
- создание item и отклик на offer;
- “мои сделки”;
- админка офферов;
- админка сделок.

Telegram-бот находится в `bot`:

- `/start`
- `/new_offer`
- `/my_offers`
- `/new_item`
- `/my_items`
- `/respond <offer_id>`
- `/my_deals`

## Основные сущности

- `users` — пользователь сервиса.
- `messenger_accounts` — привязка пользователя к Telegram или другому мессенджеру.
- `offers` — офферы/заявки пользователя.
- `offer_photos` — фотографии оффера.
- `items` — предметы пользователя, которые можно предложить в обмен.
- `deals` — отклики/сделки между published offer и item.
- `alembic_version` — служебная таблица миграций.

Связи:

- `users 1:N offers`
- `users 1:N items`
- `users 1:N messenger_accounts`
- `offers 1:N offer_photos`
- `offers 1:N deals`
- `items 1:N deals`

Подробнее: [docs/DB_SCHEMA.md](docs/DB_SCHEMA.md).

## Быстрый старт

Создать виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Установить backend/dev зависимости:

```powershell
python -m pip install -r requirements-dev.txt
```

Скопировать env:

```powershell
Copy-Item .env.example .env
```

Заполнить `.env`, поднять PostgreSQL, применить миграции:

```powershell
python -m alembic upgrade head
```

Запустить backend:

```powershell
python -m uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Запуск через Docker Compose

Docker-контур поднимает:

- `db` — PostgreSQL 16;
- `backend` — FastAPI API на `8000`;
- `frontend` — собранный Vite frontend через nginx на `3000`;
- `telegram_bot` — aiogram bot process;
- volume `postgres_data` для БД;
- volume `uploads_data` для загруженных файлов.

Скопировать Docker env:

```powershell
Copy-Item .env.docker.example .env
```

Отредактировать секреты:

```env
POSTGRES_PASSWORD=change_me
ADMIN_API_TOKEN=change_me
TELEGRAM_BOT_TOKEN=change_me
```

Запустить:

```powershell
docker compose up --build
```

Проверить compose-файл без запуска контейнеров:

```powershell
docker compose --env-file .env.docker.example config
```

Открыть:

```text
Backend docs: http://127.0.0.1:8000/docs
Frontend: http://127.0.0.1:3000
Healthcheck: http://127.0.0.1:8000/api/health
```

Остановить:

```powershell
docker compose down
```

Остановить и удалить volumes:

```powershell
docker compose down -v
```

Миграции запускает только service `backend` через `scripts/backend-entrypoint.sh`: контейнер ждёт PostgreSQL, выполняет `alembic upgrade head`, затем стартует `uvicorn`.

В Docker `BACKEND_API_URL` для bot-сервиса должен быть `http://backend:8000`, потому что `localhost` внутри контейнера указывает на сам контейнер.

Если `TELEGRAM_BOT_TOKEN` пустой или равен `change_me`, bot-сервис пишет сообщение и остаётся неактивным. Backend и frontend при этом работают.

## Переменные окружения

Пример лежит в [.env.example](.env.example).

Используемые backend/bot переменные:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `DB_ECHO`
- `PUBLIC_BASE_URL`
- `UPLOAD_DIR`
- `MAX_UPLOAD_SIZE_MB`
- `ADMIN_API_TOKEN`
- `ALLOW_ADMIN_TOKEN_AUTH`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DEV_MODE`
- `INITIAL_ADMIN_LOGIN`
- `INITIAL_ADMIN_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `BACKEND_API_URL`
- `CORS_ORIGINS`

Frontend переменная:

- `VITE_API_BASE_URL`

`VITE_API_BASE_URL` нужно задавать в `frontend/.env`, пример есть в `frontend/.env.example`.

Для Docker-запуска используйте [.env.docker.example](.env.docker.example), где `POSTGRES_HOST=db`, `BACKEND_API_URL=http://backend:8000`, а внешний frontend порт — `3000`.

Настоящие секреты хранить только в `.env`. Не коммитить `.env`.

## База и миграции

Применить миграции:

```powershell
python -m alembic upgrade head
```

Проверить текущую версию:

```powershell
python -m alembic current
```

Создать новую миграцию:

```powershell
python -m alembic revision --autogenerate -m "message"
```

Таблицу `alembic_version` руками обычно не редактируют.

## Запуск backend

```powershell
python -m uvicorn app.main:app --reload
```

Backend слушает `http://127.0.0.1:8000`.

Корневой URL `/` не обязан отдавать страницу. Для проверки API используйте:

- `GET /api/health`
- `GET /docs`
- `GET /api/offers`

## Запуск frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend dev server обычно доступен на:

```text
http://127.0.0.1:5173
```

Сборка:

```powershell
npm run build
```

## Запуск Telegram-бота

Установить зависимости:

```powershell
python -m pip install -r requirements-bot.txt
```

В `.env` должны быть:

```env
TELEGRAM_BOT_TOKEN=change_me
BACKEND_API_URL=http://127.0.0.1:8000
```

Запуск:

```powershell
python -m bot.main
```

Backend может отправлять Telegram-уведомления через Bot API сам, если задан `TELEGRAM_BOT_TOKEN`. Но команды бота работают только при запущенном `python -m bot.main`.

Если `TELEGRAM_BOT_TOKEN` пустой или оставлен как `change_me`, уведомления пропускаются, а модерация/смена статусов всё равно сохраняется.

## Авторизация и роли

Основной вход в админку теперь идёт через JWT:

```http
POST /api/auth/login
```

Создать первого `super_admin`:

```powershell
python -m scripts.create_super_admin --login admin --password change_me
```

Админские endpoint’ы используют заголовок:

```text
Authorization: Bearer <access_token>
```

Swagger:

1. Выполнить `POST /api/auth/login`.
2. Скопировать `access_token`.
3. Нажать **Authorize** в `/docs`.
4. Вставить только сам JWT без слова `Bearer`.
5. Swagger сам отправит `Authorization: Bearer <access_token>`.

Роли:

- `user`
- `editor`
- `moderator`
- `admin`
- `super_admin`

Права MVP:

- `editor`: читать админские списки офферов;
- `moderator`: модерировать офферы и менять статусы сделок;
- `admin`: управлять пользователями и назначать `editor`/`moderator`;
- `super_admin`: назначать `admin` и `super_admin`.

Временный fallback через `ADMIN_API_TOKEN` оставлен для dev и управляется:

```env
ALLOW_ADMIN_TOKEN_AUTH=true
ALLOW_ADMIN_TOKEN_FALLBACK=true
```

Для production лучше использовать `ALLOW_ADMIN_TOKEN_FALLBACK=false`.

Frontend-админка:

- `http://127.0.0.1:5173/admin/offers`
- `http://127.0.0.1:5173/admin/deals`
- `http://127.0.0.1:5173/admin/login`

## Основной MVP-сценарий

1. Пользователь загружает фото: `POST /api/files/images`.
2. Пользователь создаёт оффер: `POST /api/offers`.
3. Админ видит оффер: `GET /api/admin/offers`.
4. Админ модерирует и публикует: `PATCH /api/admin/offers/{offer_id}/moderation`.
5. Оффер появляется в каталоге: `GET /api/offers`.
6. Другой пользователь создаёт item: `POST /api/items`.
7. Другой пользователь отправляет отклик: `POST /api/deals`.
8. Админ видит сделку: `GET /api/admin/deals`.
9. Админ меняет статус сделки: `PATCH /api/admin/deals/{deal_id}/status`.

Подробный сценарий: [docs/MVP_FLOW.md](docs/MVP_FLOW.md).

## Полезные endpoint’ы

Public/user:

- `POST /api/files/images`
- `POST /api/offers`
- `GET /api/offers`
- `GET /api/offers/{offer_id}`
- `POST /api/items`
- `GET /api/users/{user_id}/items`
- `POST /api/deals`
- `GET /api/users/{user_id}/offers`
- `GET /api/users/{user_id}/deals`
- `POST /api/users/telegram`
- `POST /api/auth/login`
- `GET /api/auth/me`

Admin:

- `GET /api/admin/offers`
- `GET /api/admin/offers/{offer_id}`
- `GET /api/admin/offers/{offer_id}/photos`
- `PATCH /api/admin/offers/{offer_id}/moderation`
- `PATCH /api/admin/offers/{offer_id}/status`
- `GET /api/admin/deals`
- `GET /api/admin/deals/{deal_id}`
- `PATCH /api/admin/deals/{deal_id}/status`
- `GET /api/admin/items`
- `POST /api/admin/items`
- `GET /api/admin/users`
- `GET /api/admin/users/{user_id}`
- `POST /api/admin/users/{user_id}/roles`
- `DELETE /api/admin/users/{user_id}/roles/{role}`

## Тесты и проверки

Backend tests:

```powershell
python -m pytest tests -q
```

Python compile:

```powershell
python -m compileall app bot tests
```

Frontend build:

```powershell
cd frontend
npm run build
```

## Структура проекта

```text
.
├── alembic/
├── app/
│   ├── api/routers/
│   ├── core/
│   ├── db/models/
│   ├── schemas/
│   └── services/
├── bot/
├── docs/
├── frontend/
│   └── src/
├── tests/
├── .env.example
├── .env.docker.example
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── requirements-bot.txt
└── README.md
```
