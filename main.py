from datetime import date, datetime
from collections import Counter
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import SQLModel, Session, select
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from models import engine, Product, Review, Order, OrderItem, Coupon
from auth import limiter

SQLModel.metadata.create_all(engine)

app = FastAPI(title="AURA Beauty API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from admin import router as admin_router
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:8666",
        "http://127.0.0.1:8666",
    ],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Perfume taxonomy ──────────────────────────────────────────────────────────
GENDERS = ["Women", "Men", "Unisex"]

FAMILIES = [
    "Floral", "Woody", "Oriental/Amber", "Fresh/Aquatic",
    "Citrus", "Gourmand", "Aromatic", "Leather", "Musk",
]

CONCENTRATIONS = ["Parfum", "Eau de Parfum", "Eau de Toilette", "Eau de Cologne"]

# Full taxonomy: gender → family → concentrations available
_FAMILY_CONCS: dict[str, list[str]] = {
    "Floral":          ["Parfum", "Eau de Parfum", "Eau de Toilette", "Eau de Cologne"],
    "Woody":           ["Parfum", "Eau de Parfum", "Eau de Toilette"],
    "Oriental/Amber":  ["Parfum", "Eau de Parfum", "Eau de Toilette"],
    "Fresh/Aquatic":   ["Eau de Parfum", "Eau de Toilette", "Eau de Cologne"],
    "Citrus":          ["Eau de Parfum", "Eau de Toilette", "Eau de Cologne"],
    "Gourmand":        ["Parfum", "Eau de Parfum", "Eau de Toilette"],
    "Aromatic":        ["Eau de Parfum", "Eau de Toilette", "Eau de Cologne"],
    "Leather":         ["Parfum", "Eau de Parfum"],
    "Musk":            ["Parfum", "Eau de Parfum", "Eau de Toilette"],
}

TAXONOMY: dict[str, dict[str, list[str]]] = {g: _FAMILY_CONCS for g in GENDERS}


# ── Per-product helpers ───────────────────────────────────────────────────────

def _sizes(p: Product) -> list[dict]:
    return [s for s in (p.sizes or []) if isinstance(s, dict)]

def _in_stock(p: Product) -> bool:
    return any(s.get("stock", 0) > 0 for s in _sizes(p))

def _min_price(p: Product) -> float:
    prices = [float(p.sale_price)] if p.sale_price else [float(s["price"]) for s in _sizes(p) if "price" in s]
    return min(prices) if prices else 0.0

def _max_price(p: Product) -> float:
    prices = [float(p.sale_price)] if p.sale_price else [float(s["price"]) for s in _sizes(p) if "price" in s]
    return max(prices) if prices else 0.0

def _all_notes(p: Product) -> list[str]:
    return [
        n.lower() for lst in [p.top_notes, p.heart_notes, p.base_notes]
        for n in (lst or []) if isinstance(n, str)
    ]


def compute_facets(rows: list[Product]) -> dict:
    notes_c:      Counter = Counter()
    sizes_c:      Counter = Counter()
    seasons_c:    Counter = Counter()
    occasions_c:  Counter = Counter()
    skin_type_c:  Counter = Counter()

    for p in rows:
        for n in _all_notes(p):
            notes_c[n] += 1
        for s in _sizes(p):
            if s.get("stock", 0) > 0:
                sizes_c[str(s["ml"])] += 1
        for se in (p.season or []):
            seasons_c[str(se)] += 1
        for oc in (p.occasion or []):
            occasions_c[str(oc)] += 1
        for st in (p.skin_type or []):
            skin_type_c[str(st)] += 1

    prices = [_min_price(p) for p in rows if _sizes(p)]
    return {
        "product_types":  dict(Counter(p.product_type  for p in rows if p.product_type)),
        "subcategories":  dict(Counter(p.subcategory   for p in rows if p.subcategory)),
        "genders":        dict(Counter(p.gender        for p in rows if p.gender)),
        "families":       dict(Counter(p.family        for p in rows if p.family)),
        "concentrations": dict(Counter(p.concentration for p in rows if p.concentration)),
        "collections":    dict(Counter(p.collection    for p in rows if p.collection)),
        "notes":          dict(notes_c.most_common(30)),
        "sizes":          dict(sizes_c),
        "seasons":        dict(seasons_c),
        "occasions":      dict(occasions_c),
        "skin_types":     dict(skin_type_c),
        "price_range": {
            "min": round(min(prices), 2) if prices else 0,
            "max": round(max(prices), 2) if prices else 0,
        },
    }


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Taxonomy ──────────────────────────────────────────────────────────────────

@app.get("/api/taxonomy")
def get_taxonomy():
    return TAXONOMY


# ── Products ──────────────────────────────────────────────────────────────────

@app.get("/api/products")
def list_products(
    q:            str | None = None,
    product_type: str | None = None,          # perfume | skincare | makeup | haircare | body
    subcategory:  str | None = None,          # Serum / Foundation / …
    gender:       str | None = None,
    family:       str | None = None,
    concentration: str | None = None,
    collection:   str | None = None,
    note:         str | None = None,
    size_ml:      int | None = None,
    season:       str | None = Query(None),
    occasion:     str | None = Query(None),
    skin_type:    str | None = Query(None),
    min_price:    float | None = None,
    max_price:    float | None = None,
    in_stock:     bool | None = None,
    on_sale:      bool | None = None,
    sort:         str = "newest",
    page:         int = Query(1, ge=1),
    page_size:    int = Query(20, ge=1, le=100),
):
    with Session(engine) as s:
        stmt = select(Product).where(Product.is_active == True)

        # SQL-side filters (indexed columns)
        if q:
            stmt = stmt.where(
                Product.name.ilike(f"%{q}%") |
                Product.description.ilike(f"%{q}%") |
                Product.brand.ilike(f"%{q}%")
            )
        if product_type:
            stmt = stmt.where(Product.product_type == product_type)
        if subcategory:
            stmt = stmt.where(Product.subcategory == subcategory)
        if gender:
            stmt = stmt.where(Product.gender == gender)
        if family:
            stmt = stmt.where(Product.family == family)
        if concentration:
            stmt = stmt.where(Product.concentration == concentration)
        if collection:
            stmt = stmt.where(Product.collection == collection)
        if on_sale:
            stmt = stmt.where(Product.sale_price.isnot(None))

        rows = list(s.exec(stmt).all())

    # Python-side filters on JSON fields
    if note:
        nl = note.lower()
        rows = [p for p in rows if nl in _all_notes(p)]
    if size_ml is not None:
        rows = [p for p in rows if any(sz.get("ml") == size_ml for sz in _sizes(p))]
    if season:
        sl = season.lower()
        rows = [p for p in rows if any(s_.lower() == sl for s_ in (p.season or []))]
    if occasion:
        ol = occasion.lower()
        rows = [p for p in rows if any(o_.lower() == ol for o_ in (p.occasion or []))]
    if skin_type:
        stl = skin_type.lower()
        rows = [p for p in rows if any(st.lower() == stl for st in (p.skin_type or []))]
    if in_stock:
        rows = [p for p in rows if _in_stock(p)]
    if min_price is not None:
        rows = [p for p in rows if _max_price(p) >= min_price]
    if max_price is not None:
        rows = [p for p in rows if _min_price(p) <= max_price]

    # Facets computed on the full filtered set (before pagination)
    facets = compute_facets(rows)

    # Sort
    if sort == "price_asc":
        rows.sort(key=_min_price)
    elif sort == "price_desc":
        rows.sort(key=_max_price, reverse=True)
    elif sort == "rating":
        rows.sort(key=lambda p: p.rating, reverse=True)
    elif sort == "popular":
        rows.sort(key=lambda p: p.review_count, reverse=True)
    else:  # newest
        rows.sort(key=lambda p: p.id or 0, reverse=True)

    total = len(rows)
    start = (page - 1) * page_size
    return {
        "items":  rows[start: start + page_size],
        "total":  total,
        "pages":  max(1, -(-total // page_size)),
        "facets": facets,
    }


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
    title:  str = ""
    body:   str = ""


@app.post("/api/products/{slug}/reviews", status_code=201)
def add_review(slug: str, data: ReviewIn):
    if not 1 <= data.rating <= 5:
        raise HTTPException(400, "Rating must be 1–5")
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
        s.commit()
        s.refresh(rv)
        return rv


@app.get("/api/products/{slug}/related")
def related_products(slug: str):
    with Session(engine) as s:
        p = _get_product(s, slug)
        rows = s.exec(
            select(Product).where(
                Product.family == p.family,
                Product.id != p.id,
                Product.is_active == True,
            )
        ).all()
        return rows[:8]


# ── Coupons ───────────────────────────────────────────────────────────────────

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


# ── Orders ────────────────────────────────────────────────────────────────────

class CartItem(BaseModel):
    product_id: int
    qty:        int
    size_ml:    int = 0   # chosen size in ml


class OrderIn(BaseModel):
    customer_name:    str
    customer_email:   str
    customer_phone:   str = ""
    customer_address: str = ""
    items:            list[CartItem]
    coupon_code:      str = ""
    payment_method:   str = "cod"


SHIPPING_USD      = 1.5
FREE_SHIPPING_USD = 50.0


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
        line_items: list[tuple[Product, CartItem, float]] = []

        for it in data.items:
            p = s.get(Product, it.product_id)
            if not p:
                raise HTTPException(400, f"Product {it.product_id} not found")

            # Find the chosen size in the product's sizes array
            sizes = [sz for sz in (p.sizes or []) if isinstance(sz, dict)]
            size_obj = next((sz for sz in sizes if sz.get("ml") == it.size_ml), None)
            if size_obj is None:
                raise HTTPException(400, f"Size {it.size_ml}ml not found for product {it.product_id}")
            if size_obj.get("stock", 0) < it.qty:
                raise HTTPException(400, f"Insufficient stock for {p.name} {it.size_ml}ml")

            unit_price = float(p.sale_price if p.sale_price else size_obj["price"])
            subtotal += unit_price * it.qty

            # Decrement per-size stock (mutate the dict in the list)
            size_obj["stock"] = size_obj["stock"] - it.qty
            p.sizes = sizes  # re-assign to trigger SQLAlchemy dirty-tracking
            s.add(p)
            line_items.append((p, it, unit_price))

        discount = round(subtotal * discount_pct / 100, 2)
        shipping = 0.0 if subtotal >= FREE_SHIPPING_USD else SHIPPING_USD
        total    = round(subtotal - discount + shipping, 2)

        o = Order(
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            customer_phone=data.customer_phone,
            customer_address=data.customer_address,
            subtotal=round(subtotal, 2),
            shipping=shipping,
            discount=discount,
            total=total,
            coupon_code=data.coupon_code.upper() if data.coupon_code else "",
            payment_method=data.payment_method,
            created_at=datetime.now().isoformat(),
        )
        s.add(o)
        s.flush()

        for prod, it, unit_price in line_items:
            s.add(OrderItem(
                order_id=o.id,
                product_id=prod.id,
                product_name=prod.name,
                size_ml=it.size_ml,
                qty=it.qty,
                price=unit_price,
            ))

        s.commit()
        s.refresh(o)
        return {"order_id": o.id, "total": o.total, "discount": o.discount}


@app.get("/api/orders/{order_id}")
def get_order(order_id: int, email: str = Query(...)):
    with Session(engine) as s:
        o = s.get(Order, order_id)
        if not o or o.customer_email.lower() != email.lower():
            raise HTTPException(404, "Order not found")
        items = s.exec(select(OrderItem).where(OrderItem.order_id == o.id)).all()
        return {**o.model_dump(), "items": [i.model_dump() for i in items]}
