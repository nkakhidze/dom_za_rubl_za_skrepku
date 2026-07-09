# Дом за скрепку

Backend, frontend и Telegram-бот для MVP-проекта обменной цепочки: пользователь подаёт заявку, админ оценивает предложения и выбирает одно следующим предметом цепочки, а публичная история строится из последовательности предметов и переходов между ними.

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

- публичная история обменов;
- форма подачи оффера;
- создание item и отклик на offer в legacy-сценарии;
- “мои сделки” в legacy-сценарии;
- админка заявок;
- админка предметов цепочки;
- админка сделок.

Telegram-бот находится в `bot`:

- `/start`
- `/new_offer`
- `/my_offers`
- `/start link_<token>`

Бот не ведёт legacy-сценарий `/new_item`, `/respond` и `/my_deals`. Пользователь через сайт или бот подаёт `offer`, админ выбирает заявку следующим предметом цепочки, а backend после этого создаёт `item` и `deal`.

## Основные сущности

- `users` — пользователь сервиса.
- `messenger_accounts` — привязка пользователя к Telegram или другому мессенджеру.
- `offers` — входящие заявки пользователей; это ещё не предмет цепочки.
- `offer_photos` — фотографии оффера.
- `items` — реальные предметы цепочки: стартовый, текущий, прошлые и будущие.
- `deals` — переходы между предметами цепочки: что отдали и что получили.
- `alembic_version` — служебная таблица миграций.

Связи:

- `users 1:N offers`
- `users 1:N items`
- `users 1:N messenger_accounts`
- `offers 1:N offer_photos`
- `offers 0:1 deals` в основной цепочке через выбранную заявку.
- `items 1:N deals` через `given_item_id` и `received_item_id`.

Подробнее: [docs/DB_SCHEMA.md](docs/DB_SCHEMA.md).

## Быстрый старт

Создать виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

## Регистрация, legal-документы и личный кабинет

Юридические документы хранятся в `legal/`:

- `legal/manifest.json` — активные редакции документов.
- `legal/user-agreement/2026-06-28.md`
- `legal/privacy-policy/2026-06-28.md`
- `legal/personal-data-consent/2026-06-28.md`
- `legal/public-data-consent/2026-06-28.md`
- `legal/marketing-consent/2026-06-28.md`

Новая редакция добавляется новым Markdown-файлом с датой версии. Старые файлы не удаляются и не перезаписываются; active version переключается только в `manifest.json`.

Публичные legal endpoint'ы:

- `GET /api/legal/documents`
- `GET /api/legal/documents/{document_code}`
- `GET /api/legal/documents/{document_code}/versions/{version}`

Регистрация обычного пользователя:

- `POST /api/auth/register`
- телефон и email необязательны;
- новый пользователь получает только роль `user`;
- роль из request не принимается;
- пароль хранится только как hash;
- обязательны подтверждение 18+, Пользовательское соглашение и согласие на обработку персональных данных;
- Политика обработки персональных данных фиксируется как версия ознакомления;
- маркетинговые каналы `email`, `telegram`, `max` независимы и выключены по умолчанию.

Личный кабинет:

- frontend route: `/account`
- backend: `GET /api/auth/account`
- управление рассылками: `PATCH /api/auth/me/consents/marketing`

Согласия фиксируются в таблице `user_consents`: `document_code`, `document_version`, `status`, `accepted_at`, `revoked_at`, `source`, `ip_address`, `user_agent`, `consent_payload`.

Админский вход отделён от пользовательского:

- пользовательский вход: `/login`
- регистрация: `/register`
- админский вход: `/admin/login`

Telegram/MAX/site аккаунты пока не объединяются автоматически. Объединение должно идти только через подтверждённый сценарий связывания, не по `display_name` и не по неподтверждённому телефону.

Подробнее: [docs/LEGAL_AND_CONSENTS.md](docs/LEGAL_AND_CONSENTS.md).

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
- `IMAGE_MAX_FILE_SIZE_MB`
- `IMAGE_MAX_DIMENSION`
- `IMAGE_MAIN_MAX_SIZE`
- `IMAGE_MAIN_QUALITY`
- `IMAGE_THUMB_MAX_SIZE`
- `IMAGE_THUMB_QUALITY`
- `IMAGE_WEBP_METHOD`
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

Для боевого сайта `VITE_API_BASE_URL` должен указывать на `https://tomsk-dom-za-skrepku.space`. Для локальной разработки с локальным backend можно переопределить его в `frontend/.env`, пример есть в `frontend/.env.example`.

Для Docker-запуска используйте [.env.docker.example](.env.docker.example), где `POSTGRES_HOST=db`, `BACKEND_API_URL=http://backend:8000`, а внешний frontend порт — `3000`.

Настоящие секреты хранить только в `.env`. Не коммитить `.env`.

## Загрузка изображений

`POST /api/files/images` принимает JPEG, PNG и WebP до `IMAGE_MAX_FILE_SIZE_MB` МБ. Backend проверяет реальный формат через Pillow, исправляет EXIF-ориентацию, не хранит оригинал и создаёт два файла:

- основное изображение `<uuid>.webp`, максимум `IMAGE_MAIN_MAX_SIZE` px по большей стороне, качество `IMAGE_MAIN_QUALITY`;
- превью `<uuid>_thumb.webp`, максимум `IMAGE_THUMB_MAX_SIZE` px, качество `IMAGE_THUMB_QUALITY`.

Response содержит `photo_url`/`image_url`, `thumbnail_url`, размеры и вес файлов. Старые записи без `thumbnail_url` продолжают отображаться через fallback на `photo_url`.

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
TELEGRAM_BOT_USERNAME=change_me_bot
TELEGRAM_INTERNAL_API_TOKEN=change_me
BACKEND_API_URL=https://tomsk-dom-za-skrepku.space
BACKEND_BASE_URL=https://tomsk-dom-za-skrepku.space
PUBLIC_SITE_URL=https://tomsk-dom-za-skrepku.space
```

Запуск:

```powershell
python -m bot.main
```

Backend может отправлять Telegram-уведомления через Bot API сам, если задан `TELEGRAM_BOT_TOKEN`. Но команды бота работают только при запущенном `python -m bot.main`.

Если `TELEGRAM_BOT_TOKEN` пустой или оставлен как `change_me`, уведомления пропускаются, а модерация/смена статусов всё равно сохраняется.

Для локального запуска бота против боевого сайта `TELEGRAM_INTERNAL_API_TOKEN` в локальном `.env` должен совпадать с токеном на сервере. `PUBLIC_SITE_URL` должен быть внешним HTTPS-адресом, потому что Telegram не принимает inline-кнопки на `localhost`. Если бот при `/start` пишет «Сервис временно недоступен», сначала проверьте, что `BACKEND_API_URL` и `BACKEND_BASE_URL` не указывают на `127.0.0.1`.

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

1. Админ создаёт стартовый предмет цепочки: `POST /api/admin/items`.
2. Пользователь загружает фото: `POST /api/files/images`.
3. Пользователь создаёт заявку: `POST /api/offers`.
4. Админ видит заявку: `GET /api/admin/offers`.
5. Админ оценивает заявку, задаёт `moderated_value`, `visibility_status` и `sort_priority`: `PATCH /api/admin/offers/{offer_id}/moderation`.
6. Админ выбирает заявку следующим предметом цепочки: `POST /api/admin/offers/{offer_id}/select-next`.
7. Backend создаёт новый `item`, помечает предыдущий текущий предмет как прошлый и создаёт `deal` между ними.
8. Публичная история показывает цепочку предметов: `GET /api/public/exchange-chain`.

Legacy-сценарий откликов `POST /api/items`, `POST /api/deals`, `GET /api/users/{user_id}/deals` пока сохранён для совместимости, но не является основной механикой публичной истории.

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
- `GET /api/public/current-item`
- `GET /api/public/exchange-chain`
- `POST /api/users/telegram`
- `POST /api/auth/login`
- `GET /api/auth/me`

Admin:

- `GET /api/admin/offers`
- `GET /api/admin/offers/{offer_id}`
- `GET /api/admin/offers/{offer_id}/photos`
- `PATCH /api/admin/offers/{offer_id}/moderation`
- `PATCH /api/admin/offers/{offer_id}/status`
- `POST /api/admin/offers/{offer_id}/select-next`
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
