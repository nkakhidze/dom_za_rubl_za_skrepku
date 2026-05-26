# Paperclip House Backend

## Run Backend

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Run Telegram Bot

Install bot dependencies:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements-bot.txt
```

Set environment variables in `.env`:

```env
TELEGRAM_BOT_TOKEN=change_me
BACKEND_API_URL=http://127.0.0.1:8000
```

Start the bot:

```powershell
..\.venv\Scripts\python.exe -m bot.main
```

The MVP bot supports:

- `/start`
- `/new_offer`
- `/my_offers`

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend env example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Frontend admin panel:

```text
http://127.0.0.1:5173/admin/offers
```

Enter `ADMIN_API_TOKEN` from backend `.env` on the admin page.
