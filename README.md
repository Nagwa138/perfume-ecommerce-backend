# 3d-ecommerce-backend

FastAPI backend for the 3D e-commerce shop. Provides a REST API for products, categories, orders, and coupon validation backed by SQLite via SQLModel.

## Stack

- Python 3.11+
- FastAPI
- SQLModel (SQLAlchemy + Pydantic)
- SQLite
- Uvicorn

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install fastapi sqlmodel uvicorn python-multipart
```

Create a `.env` file (see `.env.example` if provided).

## Run

```bash
uvicorn main:app --reload --port 8001
```

API available at `http://localhost:8001/api`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/products` | List products (filter by category, q, sort, page) |
| GET | `/api/products/{slug}` | Single product by slug or ID |
| GET | `/api/products/{slug}/related` | Related products (same category) |
| GET | `/api/categories` | List all categories |
| POST | `/api/orders` | Create order |
| GET | `/api/orders/{id}` | Get order |
| POST | `/api/coupons/validate` | Validate coupon code |
