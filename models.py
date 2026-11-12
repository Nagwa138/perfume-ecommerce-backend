from typing import Optional
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import SQLModel, Field, create_engine

engine = create_engine("sqlite:///shop.db", connect_args={"check_same_thread": False})


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True, default="")
    name: str
    brand: str = "NOVA WEAR"

    # ── Taxonomy ─────────────────────────────────────────────────────────
    department: str = Field(default="", index=True)   # Men / Women / Kids / Unisex
    category: str = Field(index=True)                 # Tops / Outerwear / Bottoms …
    subcategory: str = Field(default="", index=True)  # T-Shirts / Bomber / Jeans …

    # ── Pricing ──────────────────────────────────────────────────────────
    price: float
    sale_price: Optional[float] = None
    stock: int = 0

    # ── Descriptive content ───────────────────────────────────────────────
    description: str = ""
    details: Optional[list] = Field(default=None, sa_column=Column(JSON))

    # ── New product attributes ────────────────────────────────────────────
    fit: str = ""               # slim / regular / relaxed / oversized
    fabric: str = ""            # human-readable materials string
    materials: str = ""         # legacy; keep for compatibility
    season: str = ""            # all-season / summer / winter / spring-fall
    collection: str = ""        # Night City / Heritage Denim / Street Archive …
    care_instructions: str = ""

    # ── JSON arrays ───────────────────────────────────────────────────────
    sizes: Optional[list] = Field(default=None, sa_column=Column(JSON))
    colors: Optional[list] = Field(default=None, sa_column=Column(JSON))
    images: Optional[list] = Field(default=None, sa_column=Column(JSON))
    tags: Optional[list] = Field(default=None, sa_column=Column(JSON))

    # ── Metrics ───────────────────────────────────────────────────────────
    rating: float = 0.0
    review_count: int = 0
    is_new: bool = False
    is_featured: bool = False
    is_active: bool = True

    # ── Legacy single-image / single-color fields ─────────────────────────
    image: str = ""
    color: str = "#222222"


class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    author: str
    rating: int
    title: str = ""
    body: str = ""
    date: str = ""


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = "pending"
    customer_name: str
    customer_email: str
    customer_phone: str = ""
    customer_address: str = ""
    subtotal: float = 0.0
    shipping: float = 0.0
    discount: float = 0.0
    total: float = 0.0
    coupon_code: str = ""
    payment_method: str = "cod"
    created_at: str = ""


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_item"
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int
    product_name: str = ""
    size: str = ""
    color: str = ""
    qty: int = 1
    price: float = 0.0


class Coupon(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    percent: int = 10
    active: bool = True


class AdminUser(SQLModel, table=True):
    __tablename__ = "admin_user"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    role: str = "staff"   # "admin" | "staff"
    is_active: bool = True
    last_login: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    action: str
    entity: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
