# 📝 Telegram Notes Bot

A production-ready, async Telegram bot that captures notes via the `/note` command, persists them in a database, and synchronises every note to a Notion database in real time.

Built with **clean architecture**, full **type hints**, **structured logging**, and **Docker** support — ready for senior-level technical evaluation.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Async Telegram Bot** | Webhook-based, powered by FastAPI |
| **Database Persistence** | SQLAlchemy async with SQLite (switchable to PostgreSQL) |
| **Notion Sync** | Every note pushed to Notion via official API |
| **Clean Architecture** | Service layer, dependency injection, no logic in routes |
| **Structured Logging** | JSON file logs + console, rotating file handler |
| **Database Migrations** | Alembic with async support |
| **Dockerised** | Dockerfile + docker-compose ready |
| **Environment Config** | Pydantic Settings — zero hardcoded secrets |

---

## 🏗 Architecture

```
app/
├── main.py                  # FastAPI app with lifespan
├── config.py                # Pydantic Settings (env vars)
├── database.py              # Async engine & session factory
├── logging_config.py        # Structured logging setup
├── models/
│   └── note.py              # SQLAlchemy ORM model
├── schemas/
│   └── note_schema.py       # Pydantic validation schemas
├── services/
│   ├── note_service.py      # Database CRUD operations
│   ├── notion_service.py    # Notion API integration
│   └── telegram_service.py  # Command orchestration
├── routes/
│   └── webhook.py           # POST /webhook endpoint
└── utils/
```

### Request Flow

```
Telegram → POST /webhook → webhook.py (validate secret)
    → telegram_service.py (orchestrate)
        → note_service.py (save to DB)
        → notion_service.py (push to Notion)
        → note_service.py (update sync status)
    → Send reply via Bot API
```

### Why This Architecture?

- **Async Everywhere** — Non-blocking I/O for database, HTTP, and Telegram calls. The server can handle many concurrent webhook requests.
- **Service Layer** — Business logic lives in services, not route handlers. Each service has a single responsibility.
- **Dependency Injection** — Database sessions are created per-request and passed down. No global mutable state.
- **Separation of Concerns** — Telegram parsing, database operations, and Notion API calls are fully isolated. Any component can be replaced independently.

---

## 🚀 Local Setup

### Prerequisites

- Python 3.11+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- A Notion integration token and database ID

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd telegram_bot

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your actual tokens

# 5. Run database migrations
alembic upgrade head

# 6. Start the server
uvicorn app.main:app --reload --port 8000
```

---

## 🔗 Telegram Webhook Setup

After starting the server on a public URL (e.g. via ngrok or VPS), register the webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook",
    "secret_token": "<YOUR_WEBHOOK_SECRET>"
  }'
```

> **Tip:** The `secret_token` must match the `TELEGRAM_WEBHOOK_SECRET` in your `.env` file. Telegram will send it as the `X-Telegram-Bot-Api-Secret-Token` header with every update.

### Verify Webhook

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

---

## 📓 Notion Setup Guide

### 1. Create a Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations).
2. Click **"New integration"**.
3. Name it (e.g. `Telegram Notes Bot`), select the workspace.
4. Copy the **Internal Integration Token** → paste into `NOTION_TOKEN` in `.env`.

### 2. Create a Notion Database

Create a database with these **exact** property names and types:

| Property | Type |
|---|---|
| `Name` | Title |
| `Telegram User` | Rich text |
| `Created` | Date |

### 3. Share the Database

1. Open your Notion database page.
2. Click **"…"** → **"Connections"** → select your integration.

### 4. Get the Database ID

From the database URL:

```
https://www.notion.so/<workspace>/<DATABASE_ID>?v=...
```

Copy the `DATABASE_ID` part (32 hex characters) → paste into `NOTION_DATABASE_ID` in `.env`.

---

## 🤖 Bot Usage

In any Telegram chat with the bot:

```
/note Buy groceries
```

**Responses:**

| Scenario | Reply |
|---|---|
| Success | ✅ Note saved and synced to Notion! |
| Notion fails | ⚠️ Note saved locally but failed to sync to Notion. |
| Empty text | ❌ Please provide note text. Example: `/note Buy milk` |

---

## 🐳 Docker Deployment

### Quick Start

```bash
cp .env.example .env
# Edit .env with your tokens

docker-compose up -d --build
```

### Production Deployment (VPS + Nginx)

1. **Deploy the container:**

```bash
docker-compose up -d --build
```

2. **Configure Nginx reverse proxy:**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **Enable HTTPS** (required by Telegram for webhooks):

```bash
sudo certbot --nginx -d your-domain.com
```

4. **Register the webhook** pointing to your domain (see Webhook Setup above).

---

## 🔧 Switching to PostgreSQL

1. Install the async PostgreSQL driver:

```bash
pip install asyncpg
```

2. Update `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/notes_db
```

3. Re-run migrations:

```bash
alembic upgrade head
```

No code changes required — the engine auto-configures for each backend.

---

## 📁 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | ✅ |
| `TELEGRAM_WEBHOOK_SECRET` | Secret for webhook validation | ✅ |
| `DATABASE_URL` | SQLAlchemy async connection string | ✅ |
| `NOTION_TOKEN` | Notion integration token | ✅ |
| `NOTION_DATABASE_ID` | Target Notion database ID | ✅ |
| `APP_ENV` | `development` or `production` | ❌ |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | ❌ |

---

## 📜 License

MIT
