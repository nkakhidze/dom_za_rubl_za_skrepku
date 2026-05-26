# Frontend

## Environment

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Run

```powershell
npm install
npm run dev
```

The app uses:

- `GET /api/offers`
- `GET /api/offers/{offer_id}`
- `POST /api/files/images`
- `POST /api/offers`

## Admin

Open:

```text
http://127.0.0.1:5173/admin/offers
```

Enter the backend admin token from `.env`:

```env
ADMIN_API_TOKEN=change_me
```

The token is stored in browser `localStorage` and sent as:

```http
Authorization: Bearer <token>
```

Admin pages use:

- `GET /api/admin/offers`
- `GET /api/admin/offers/{offer_id}`
- `GET /api/admin/offers/{offer_id}/photos`
- `PATCH /api/admin/offers/{offer_id}/moderation`
- `PATCH /api/admin/offers/{offer_id}/status`
