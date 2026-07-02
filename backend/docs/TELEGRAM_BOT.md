# Telegram Bot MVP

## Purpose

Telegram bot is a separate process. It talks to backend only through HTTP and must not import SQLAlchemy models, sessions, repositories, or backend services.

Main bot scenarios:

- `/start` resolves or creates a backend user by Telegram id.
- `/new_offer` collects offer fields and 1-3 photos.
- `/my_offers` shows offers owned by the current Telegram user.
- `/start link_<token>` links an existing site account with a Telegram account.

The bot intentionally does not implement the legacy `/new_item`, `/respond`, or `/my_deals` flow. Users submit `offers`; admins select one offer as the next chain item; backend then creates the corresponding `item` and `deal`.

## Environment

Backend and bot need the same internal token:

```env
TELEGRAM_BOT_TOKEN=change_me
TELEGRAM_BOT_USERNAME=change_me_bot
TELEGRAM_INTERNAL_API_TOKEN=change_me
BACKEND_BASE_URL=https://tomsk-dom-za-skrepku.space
BACKEND_API_URL=https://tomsk-dom-za-skrepku.space
PUBLIC_SITE_URL=https://tomsk-dom-za-skrepku.space
```

For Docker inside one Compose network, bot can use the backend service name:

```env
BACKEND_BASE_URL=http://backend:8000
```

`localhost` inside the bot container points to the bot container itself, not to backend.

For local polling against the deployed site, use public HTTPS URLs:

```env
BACKEND_BASE_URL=https://tomsk-dom-za-skrepku.space
BACKEND_API_URL=https://tomsk-dom-za-skrepku.space
PUBLIC_SITE_URL=https://tomsk-dom-za-skrepku.space
```

## Internal API

Bot uses internal endpoints protected by:

```text
Authorization: Bearer <TELEGRAM_INTERNAL_API_TOKEN>
```

Endpoints:

- `POST /api/internal/telegram/users/resolve`
- `GET /api/internal/telegram/offers?telegram_user_id=...`
- `POST /api/internal/telegram/offers`
- `POST /api/internal/telegram/account-links/consume`

The public website uses authenticated account endpoints:

- `GET /api/auth/account/telegram`
- `POST /api/auth/account/telegram/link`

## Account Linking

1. User logs in on the site.
2. User opens account page and requests Telegram linking.
3. Backend creates one-time `account_link_tokens` row and returns Telegram deep link.
4. User opens the link in Telegram.
5. Bot receives `/start link_<token>`.
6. Bot calls `/api/internal/telegram/account-links/consume`.
7. Backend links `user_identities(provider=telegram)` to the site user.
8. If a temporary Telegram user existed, backend moves that user's offers/items/deals to the site user and marks the temporary user as merged.

Conflicts:

- One Telegram account cannot be linked to two site users.
- One site user cannot have two Telegram identities.
- Expired or used tokens are rejected.

## Tables

New tables used by Telegram MVP:

- `user_identities` stores provider identities such as Telegram and MAX.
- `account_link_tokens` stores short-lived one-time account linking tokens.
- `telegram_notification_events` stores notification delivery attempts and prevents duplicate chain-selection notifications.

Changed tables:

- `users.merged_into_user_id` and `users.merged_at` mark temporary users merged into a real site user.
- `offers.source_idempotency_key` prevents duplicate offer creation from Telegram retries.

## Run

Backend:

```powershell
python -m uvicorn app.main:app --reload
```

Bot:

```powershell
python -m bot.main
```

If `TELEGRAM_BOT_TOKEN` or `TELEGRAM_INTERNAL_API_TOKEN` is missing or left as `change_me`, the bot starts in inactive mode and prints a message instead of polling Telegram.

## Tests

Targeted tests:

```powershell
python -m pytest tests/test_telegram_internal_http.py tests/test_bot_backend_client.py -q
```

Full backend tests:

```powershell
python -m pytest tests -q
```
