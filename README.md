# AURA Perfume — Backend

FastAPI REST API for the AURA premium perfume store.

> **Two-repo project.** This repo (`backend/`) is one half. The frontend lives in the sibling `frontend/` repo. Run both simultaneously — they communicate over HTTP.

## Stack

- Python 3.11+
- FastAPI
- SQLModel (SQLAlchemy + Pydantic)
- SQLite (`perfume.db` — separate from the clothing shop)
- Uvicorn
- Anthropic / OpenAI-compatible LLM for the admin AI chat

## Setup

```bash
# 1. Create venv
python -m venv .venv

# 2. Activate (Windows)
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and fill in secrets
copy .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY, PIXABAY_API_KEY, LLM_* keys.
# JWT_SECRET is auto-generated; do NOT copy it from the clothing shop.

# 5. Create database tables
python -c "from models import engine; from sqlmodel import SQLModel; SQLModel.metadata.create_all(engine)"

# 6. Create your admin user (interactive — you type the credentials)
python create_admin.py

# 7. Seed the perfume catalog (ask Claude first — it will confirm before running)
# python seed_perfume.py
```

## Run (port 8002)

```bash
uvicorn main:app --reload --port 8002
```

API available at `http://localhost:8002/api`.

## Run alongside the clothing shop

The clothing shop runs on port 8001. This shop runs on 8002. They use separate `.db` files and separate frontends (5173 vs 5174), so they coexist without conflict.

## Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/taxonomy` | Gender → family → concentration tree |
| GET | `/api/products` | List/filter perfumes with facets |
| GET | `/api/products/{slug}` | Single product |
| GET | `/api/products/{slug}/reviews` | Reviews |
| POST | `/api/products/{slug}/reviews` | Add review |
| GET | `/api/products/{slug}/related` | Same-family products |
| POST | `/api/coupons/validate` | Validate coupon |
| POST | `/api/orders` | Create order |
| GET | `/api/orders/{id}` | Get order (requires customer email) |
| POST | `/api/admin/login` | Admin JWT login |
| GET | `/api/admin/orders` | List orders (staff+) |
| PATCH | `/api/admin/orders/{id}/status` | Update order status |
| POST | `/api/admin/chat` | AI assistant with tools |
