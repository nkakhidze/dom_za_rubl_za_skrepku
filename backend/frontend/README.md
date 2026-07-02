# Frontend

## Environment

Create `frontend/.env`:

```env
VITE_API_BASE_URL=https://tomsk-dom-za-skrepku.space
```

For local development against a local backend, override it in `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Run

```powershell
npm install
npm run dev
```

The app uses:

- `GET /api/public/exchange-chain`
- `GET /api/offers`
- `GET /api/offers/{offer_id}`
- `POST /api/files/images`
- `POST /api/offers`

## Admin

Open:

```text
http://127.0.0.1:5173/admin/login
```

Login through backend auth:

```http
POST /api/auth/login
```

The frontend stores only the returned JWT access token in `localStorage` for the MVP and sends it as:

```http
Authorization: Bearer <access_token>
```

Do not store login/password in `localStorage`.

Temporary `ADMIN_API_TOKEN` fallback can still be enabled in backend dev env, but the frontend admin UI is JWT-first.

Admin pages use:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/admin/offers`
- `GET /api/admin/offers/{offer_id}`
- `GET /api/admin/offers/{offer_id}/photos`
- `PATCH /api/admin/offers/{offer_id}/moderation`
- `PATCH /api/admin/offers/{offer_id}/status`
- `POST /api/admin/offers/{offer_id}/select-next`
- `GET /api/admin/items`
- `POST /api/admin/items`
- `GET /api/admin/deals`
- `PATCH /api/admin/deals/{deal_id}/status`

Admin flow:

1. `/admin/items` creates the first current item in the exchange chain.
2. `/admin/offers` shows incoming user requests.
3. `/admin/offers/:id` can select a request as the next chain item.
4. Selection creates a completed deal and the received item becomes the new current item.
5. Public exchange history reads `/api/public/exchange-chain`.
