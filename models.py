from typing import Optional
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import SQLModel, Field, create_engine

engine = create_engine("sqlite:///perfume.db", connect_args={"check_same_thread": False})


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True, default="")
    name: str

    # ── Brand / taxonomy ──────────────────────────────────────────────────────
    brand: str = ""
    gender: str = Field(default="Unisex", index=True)         # Women / Men / Unisex
    family: str = Field(default="", index=True)               # Floral / Woody / …
    concentration: str = Field(default="", index=True)        # Parfum / EdP / EdT / EdC

    # ── Note pyramid (JSON arrays of strings) ─────────────────────────────────
    top_notes:   Optional[list] = Field(default=None, sa_column=Column(JSON))
    heart_notes: Optional[list] = Field(default=None, sa_column=Column(JSON))
    base_notes:  Optional[list] = Field(default=None, sa_column=Column(JSON))

    # ── Sizes: [{ml: int, price: float, stock: int}] ──────────────────────────
    # Stock is tracked per size — there is no flat stock field.
    sizes: Optional[list] = Field(default=None, sa_column=Column(JSON))

    # ── Sensory characteristics ───────────────────────────────────────────────
    longevity: int = 5     # 1–10 hours
    sillage:   int = 5     # 1–10 projection

    # ── Context (JSON arrays of strings) ─────────────────────────────────────
    season:   Optional[list] = Field(default=None, sa_column=Column(JSON))
    occasion: Optional[list] = Field(default=None, sa_column=Column(JSON))

    # ── Metadata ──────────────────────────────────────────────────────────────
    perfumer:    str = ""
    year:        Optional[int] = None
    description: str = ""
    collection:  str = ""

    # ── Bottle aesthetics ─────────────────────────────────────────────────────
    bottle_color: str = "#C8A951"    # hex colour for the liquid mesh
    cap_style:    str = "round"      # round | square | tall

    # ── Media / pricing / flags ───────────────────────────────────────────────
    images:     Optional[list] = Field(default=None, sa_column=Column(JSON))
    tags:       Optional[list] = Field(default=None, sa_column=Column(JSON))
    sale_price: Optional[float] = None

    # ── Product-type classification ───────────────────────────────────────────
    # perfume | skincare | makeup | haircare | body
    product_type: str = Field(default="perfume", index=True)
    subcategory:  str = ""   # Serum / Foundation / Shampoo / Body Cream / …

    # ── Cosmetic fields (skincare / makeup / hair / body) ─────────────────────
    # Makeup shade variants: [{name, shade_hex, stock}]
    variants:    Optional[list] = Field(default=None, sa_column=Column(JSON))
    # Applicable skin types: dry | oily | combination | sensitive | normal | all
    skin_type:   Optional[list] = Field(default=None, sa_column=Column(JSON))
    ingredients: str = ""    # key actives / INCI excerpt
    how_to_use:  str = ""    # application instructions

    # ── Metrics ───────────────────────────────────────────────────────────────
    rating:       float = 0.0
    review_count: int   = 0
    is_new:       bool  = False
    is_featured:  bool  = False
    is_active:    bool  = True


class Review(SQLModel, table=True):
    id:         Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    author:     str
    rating:     int
    title:      str = ""
    body:       str = ""
    date:       str = ""


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id:               Optional[int] = Field(default=None, primary_key=True)
    status:           str   = "pending"
    customer_name:    str
    customer_email:   str
    customer_phone:   str   = ""
    customer_address: str   = ""
    subtotal:         float = 0.0
    shipping:         float = 0.0
    discount:         float = 0.0
    total:            float = 0.0
    coupon_code:      str   = ""
    payment_method:   str   = "cod"
    created_at:       str   = ""


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_item"
    id:           Optional[int] = Field(default=None, primary_key=True)
    order_id:     int   = Field(foreign_key="orders.id", index=True)
    product_id:   int
    product_name: str   = ""
    size_ml:      int   = 0        # chosen size in ml
    qty:          int   = 1
    price:        float = 0.0      # price at time of order


class Coupon(SQLModel, table=True):
    id:      Optional[int] = Field(default=None, primary_key=True)
    code:    str = Field(unique=True, index=True)
    percent: int  = 10
    active:  bool = True


class AdminUser(SQLModel, table=True):
    __tablename__ = "admin_user"
    id:            Optional[int] = Field(default=None, primary_key=True)
    username:      str = Field(unique=True, index=True)
    password_hash: str
    role:          str  = "staff"   # "admin" | "staff"
    is_active:     bool = True
    last_login:    Optional[str] = None
    created_at:    str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    id:         Optional[int] = Field(default=None, primary_key=True)
    username:   str
    action:     str
    entity:     str
    entity_id:  Optional[int] = None
    details:    Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Settings(SQLModel, table=True):
    key:   str = Field(primary_key=True)
    value: str = ""
