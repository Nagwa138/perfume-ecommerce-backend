from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import SQLModel, Session, select
from collections import Counter
from models import engine, Product, Review, Order, OrderItem, Coupon

SQLModel.metadata.create_all(engine)

# add payment_method column if it doesn't exist yet (safe one-time migration)
from sqlalchemy import text
with Session(engine) as _s:
    try:
        _s.exec(text("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'cod'"))
        _s.commit()
    except Exception:
        pass

app = FastAPI(title="Shop API")

from admin import router as admin_router
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://localhost:5175"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-admin-token"],
)

# ── Taxonomy definition ───────────────────────────────────────────────────────
TAXONOMY: dict[str, dict[str, list[str]]] = {
    "Men": {
        "Tops":                  ["T-Shirts", "Polos", "Shirts", "Tank Tops", "Long Sleeves"],
        "Hoodies & Sweatshirts": ["Pullover", "Zip Hoodie", "Crewneck", "Oversized"],
        "Knitwear":              ["Sweaters", "Cardigans", "Turtlenecks"],
        "Outerwear":             ["Bomber", "Denim Jacket", "Puffer", "Leather Jacket", "Windbreaker", "Trench"],
        "Bottoms":               ["Jeans", "Cargo Pants", "Joggers", "Chinos", "Shorts"],
        "Activewear":            ["Track Pants", "Training Tees"],
        "Footwear":              ["Sneakers", "Boots", "Loafers", "Slides"],
        "Accessories":           ["Caps", "Beanies", "Bags & Backpacks", "Belts", "Sunglasses", "Socks"],
    },
    "Women": {
        "Tops":                  ["T-Shirts", "Crop Tops", "Shirts", "Tank Tops", "Long Sleeves"],
        "Hoodies & Sweatshirts": ["Pullover", "Zip Hoodie", "Crewneck", "Oversized"],
        "Knitwear":              ["Sweaters", "Cardigans", "Turtlenecks"],
        "Outerwear":             ["Bomber", "Puffer", "Leather Jacket", "Windbreaker", "Trench", "Wool Coat", "Blazer"],
        "Bottoms":               ["Jeans", "Cargo Pants", "Joggers", "Shorts", "Skirts"],
        "Dresses":               ["Mini", "Midi", "Maxi"],
        "Activewear":            ["Leggings", "Sports Bras", "Track Pants", "Training Tees"],
        "Loungewear":            ["Loungewear Sets"],
        "Footwear":              ["Sneakers", "Boots", "Sandals", "Slides", "Loafers"],
        "Accessories":           ["Caps", "Beanies", "Bags & Backpacks", "Belts", "Sunglasses", "Socks", "Scarves", "Watches"],
    },
    "Kids": {
        "Tops":                  ["T-Shirts", "Long Sleeves"],
        "Hoodies & Sweatshirts": ["Pullover", "Zip Hoodie"],
        "Outerwear":             ["Puffer", "Windbreaker"],
        "Bottoms":               ["Jeans", "Joggers", "Shorts"],
        "Footwear":              ["Sneakers", "Boots"],
        "Accessories":           ["Caps", "Beanies", "Socks"],
    },
}


def compute_facets(rows: list[Product]) -> dict:
    sizes_c: Counter = Counter()
    colors_c: Counter = Counter()
    for p in rows:
        if p.sizes:
            for sz in p.sizes:
                sizes_c[str(sz)] += 1
        if p.colors:
            for c in p.colors:
                if isinstance(c, dict) and c.get("hex"):
                    colors_c[c["hex"]] += 1

    prices = [float(p.sale_price or p.price) for p in rows]
    return {
        "departments":  dict(Counter(p.department  for p in rows if p.department)),
        "categories":   dict(Counter(p.category    for p in rows if p.category)),
        "subcategories": dict(Counter(p.subcategory for p in rows if p.subcategory)),
        "fits":         dict(Counter(p.fit         for p in rows if p.fit)),
        "collections":  dict(Counter(p.collection  for p in rows if p.collection)),
        "sizes":        dict(sizes_c),
        "price_range":  {
            "min": round(min(prices), 2) if prices else 0,
            "max": round(max(prices), 2) if prices else 0,
        },
    }


# ── health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── taxonomy ──────────────────────────────────────────────────────────────────
@app.get("/api/taxonomy")
def get_taxonomy():
    return TAXONOMY


# ── products ──────────────────────────────────────────────────────────────────
@app.get("/api/products")
def list_products(
    q:           str | None = None,
    department:  str | None = None,
    category:    str | None = None,
    subcategory: str | None = None,
    fit:         str | None = None,
    collection:  str | None = None,
    min_price:   float | None = None,
    max_price:   float | None = None,
    in_stock:    bool | None = None,
    on_sale:     bool | None = None,
    size:        str | None = None,   # filtered in Python (JSON array field)
    color:       str | None = None,   # filtered in Python (JSON array field)
    sort:        str = "newest",
    page:        int = Query(1, ge=1),
    page_size:   int = Query(20, ge=1, le=100),
):
    with Session(engine) as s:
        stmt = select(Product)

        if q:
            stmt = stmt.where(
                Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%")
            )
        if department:
            stmt = stmt.where(Product.department == department)
        if category:
            stmt = stmt.where(Product.category == category)
        if subcategory:
            stmt = stmt.where(Product.subcategory == subcategory)
        if fit:
            stmt = stmt.where(Product.fit == fit)
        if collection:
            stmt = stmt.where(Product.collection == collection)
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if in_stock:
            stmt = stmt.where(Product.stock > 0)
        if on_sale:
            stmt = stmt.where(Product.sale_price.isnot(None))

        rows = list(s.exec(stmt).all())

        # ── Python-side JSON-field filters ────────────────────────────────
        if size:
            rows = [p for p in rows if p.sizes and size in p.sizes]
        if color:
            cl = color.lower()
            rows = [
                p for p in rows
                if p.colors and any(
                    (isinstance(c, dict) and (
                        c.get("hex", "").lower() == cl or
                        c.get("name", "").lower() == cl
                    ))
                    for c in p.colors
                )
            ]

        # ── Facets computed on full filtered set (before pagination) ──────
        facets = compute_facets(rows)

        # ── Sort ──────────────────────────────────────────────────────────
        if sort == "price_asc":
            rows.sort(key=lambda p: float(p.sale_price or p.price))
        elif sort == "price_desc":
            rows.sort(key=lambda p: float(p.sale_price or p.price), reverse=True)
        elif sort == "rating":
            rows.sort(key=lambda p: p.rating, reverse=True)
        elif sort == "popular":
            rows.sort(key=lambda p: p.review_count, reverse=True)
        else:
            rows.sort(key=lambda p: p.id or 0, reverse=True)

        total = len(rows)
        start = (page - 1) * page_size
        return {
            "items":  rows[start: start + page_size],
            "total":  total,
            "pages":  max(1, -(-total // page_size)),
            "facets": facets,
        }


@app.get("/api/categories")
def categories():
    # Returns a flat sorted list of distinct categories (backward-compatible)
    with Session(engine) as s:
        return sorted({p.category for p in s.exec(select(Product)).all()})


def _get_product(s: Session, slug_or_id: str) -> Product:
    p = s.exec(select(Product).where(Product.slug == slug_or_id)).first()
    if not p and slug_or_id.isdigit():
        p = s.get(Product, int(slug_or_id))
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@app.get("/api/products/{slug}")
def get_product(slug: str):
    with Session(engine) as s:
        return _get_product(s, slug)


@app.get("/api/products/{slug}/reviews")
def get_reviews(slug: str):
    with Session(engine) as s:
        p = _get_product(s, slug)
        return s.exec(select(Review).where(Review.product_id == p.id)).all()


class ReviewIn(BaseModel):
    author: str
    rating: int
    title: str = ""
    body: str = ""


@app.post("/api/products/{slug}/reviews", status_code=201)
def add_review(slug: str, data: ReviewIn):
    if not 1 <= data.rating <= 5:
        raise HTTPException(400, "Rating must be 1–5")
    from datetime import date
    with Session(engine) as s:
        p = _get_product(s, slug)
        rv = Review(product_id=p.id, author=data.author, rating=data.rating,
                    title=data.title, body=data.body,
                    date=date.today().isoformat())
        s.add(rv)
        all_ratings = [r.rating for r in s.exec(select(Review).where(Review.product_id == p.id)).all()]
        all_ratings.append(data.rating)
        p.review_count = len(all_ratings)
        p.rating = round(sum(all_ratings) / len(all_ratings), 1)
        s.add(p)
        s.commit(); s.refresh(rv)
        return rv


@app.get("/api/products/{slug}/related")
def related_products(slug: str):
    with Session(engine) as s:
        p = _get_product(s, slug)
        rows = s.exec(
            select(Product).where(Product.category == p.category, Product.id != p.id)
        ).all()
        return rows[:8]


# ── coupons ───────────────────────────────────────────────────────────────────
class CouponIn(BaseModel):
    code: str


@app.post("/api/coupons/validate")
def validate_coupon(data: CouponIn):
    with Session(engine) as s:
        c = s.exec(select(Coupon).where(
            Coupon.code == data.code.upper(), Coupon.active == True
        )).first()
        if not c:
            raise HTTPException(404, "Invalid or expired coupon")
        return {"code": c.code, "percent": c.percent}


# ── orders ────────────────────────────────────────────────────────────────────
class CartItem(BaseModel):
    product_id: int
    qty: int
    size: str = ""
    color: str = ""


class OrderIn(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str = ""
    customer_address: str = ""
    items: list[CartItem]
    coupon_code: str = ""
    payment_method: str = "cod"


SHIPPING_USD = 1.5          # EGP ~75
FREE_SHIPPING_USD = 50.0    # EGP ~2 500


@app.post("/api/orders", status_code=201)
def create_order(data: OrderIn):
    with Session(engine) as s:
        discount_pct = 0
        if data.coupon_code:
            c = s.exec(select(Coupon).where(
                Coupon.code == data.coupon_code.upper(), Coupon.active == True
            )).first()
            if not c:
                raise HTTPException(400, "Invalid coupon code")
            discount_pct = c.percent

        subtotal = 0.0
        line_items: list[tuple[Product, CartItem]] = []
        for it in data.items:
            p = s.get(Product, it.product_id)
            if not p or p.stock < it.qty:
                raise HTTPException(400, f"Unavailable: {it.product_id}")
            p.stock -= it.qty
            subtotal += float(p.sale_price or p.price) * it.qty
            s.add(p)
            line_items.append((p, it))

        discount  = round(subtotal * discount_pct / 100, 2)
        shipping  = 0.0 if subtotal >= FREE_SHIPPING_USD else SHIPPING_USD
        total     = round(subtotal - discount + shipping, 2)

        from datetime import datetime
        o = Order(
            customer_name=data.customer_name, customer_email=data.customer_email,
            customer_phone=data.customer_phone, customer_address=data.customer_address,
            subtotal=round(subtotal, 2), shipping=shipping,
            discount=discount, total=total,
            coupon_code=data.coupon_code.upper() if data.coupon_code else "",
            payment_method=data.payment_method,
            created_at=datetime.now().isoformat(),
        )
        s.add(o); s.flush()
        for prod, it in line_items:
            s.add(OrderItem(
                order_id=o.id, product_id=prod.id,
                product_name=prod.name, size=it.size, color=it.color,
                qty=it.qty, price=float(prod.sale_price or prod.price),
            ))
        s.commit(); s.refresh(o)
        return {"order_id": o.id, "total": o.total, "discount": o.discount}


@app.get("/api/orders/{order_id}")
def get_order(order_id: int, email: str = Query(...)):
    with Session(engine) as s:
        o = s.get(Order, order_id)
        if not o or o.customer_email.lower() != email.lower():
            raise HTTPException(404, "Order not found")
        items = s.exec(select(OrderItem).where(OrderItem.order_id == o.id)).all()
        return {**o.model_dump(), "items": [i.model_dump() for i in items]}
