import os, json, re
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from models import engine, Product, Order, OrderItem, AdminUser
from auth import (
    limiter, verify_password, create_token, log_action,
    require_admin, require_role,
)

load_dotenv()
router = APIRouter(prefix="/api/admin")

KEY   = os.getenv("ANTHROPIC_API_KEY", "")
MOCK  = (not KEY) or ("your-key" in KEY)
MODEL = "claude-sonnet-4-6"

if not MOCK:
    import anthropic
    client = anthropic.Anthropic(api_key=KEY)

SYSTEM = (
    "You are the AURA store admin assistant for a luxury perfume e-commerce shop. "
    "Use the tools to read and modify the perfume catalog. Never invent data. "
    "Before deleting a product, ask the admin to confirm; only pass confirmed=true after they explicitly say yes. "
    "Keep replies concise and professional."
)

TOOLS = [
    {
        "name": "list_products",
        "description": "List perfumes, filtered by gender, family, concentration or name. Returns up to 12 results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gender":        {"type": "string", "description": "Women, Men or Unisex"},
                "family":        {"type": "string", "description": "Floral, Woody, Oriental/Amber, etc."},
                "concentration": {"type": "string", "description": "Parfum, Eau de Parfum, etc."},
                "name_contains": {"type": "string"},
            },
        },
    },
    {
        "name": "create_product",
        "description": "Create a new perfume product in the catalog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":          {"type": "string"},
                "brand":         {"type": "string"},
                "gender":        {"type": "string", "enum": ["Women", "Men", "Unisex"]},
                "family":        {"type": "string"},
                "concentration": {"type": "string"},
                "top_notes":     {"type": "array", "items": {"type": "string"}},
                "heart_notes":   {"type": "array", "items": {"type": "string"}},
                "base_notes":    {"type": "array", "items": {"type": "string"}},
                "sizes":         {
                    "type": "array",
                    "description": "List of {ml, price, stock} objects, e.g. [{\"ml\":50,\"price\":89,\"stock\":20}]",
                    "items": {"type": "object"},
                },
                "longevity":     {"type": "integer", "minimum": 1, "maximum": 10},
                "sillage":       {"type": "integer", "minimum": 1, "maximum": 10},
                "bottle_color":  {"type": "string", "description": "Hex colour for the liquid, e.g. #C8A951"},
                "cap_style":     {"type": "string", "enum": ["round", "square", "tall"]},
                "description":   {"type": "string"},
                "collection":    {"type": "string"},
                "perfumer":      {"type": "string"},
                "year":          {"type": "integer"},
                "season":        {"type": "array", "items": {"type": "string"}},
                "occasion":      {"type": "array", "items": {"type": "string"}},
                "tags":          {"type": "array", "items": {"type": "string"}},
            },
            "required": ["name", "brand", "family", "concentration"],
        },
    },
    {
        "name": "update_price",
        "description": "Update the price for a specific size (by ml) of a product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "size_ml":    {"type": "integer", "description": "Target size in ml"},
                "price":      {"type": "number"},
            },
            "required": ["product_id", "size_ml", "price"],
        },
    },
    {
        "name": "set_stock",
        "description": "Set the stock quantity for a specific size of a product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "size_ml":    {"type": "integer"},
                "stock":      {"type": "integer"},
            },
            "required": ["product_id", "size_ml", "stock"],
        },
    },
    {
        "name": "set_sale_price",
        "description": "Set or clear a product-level sale price (applies to all sizes).",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "sale_price": {"type": ["number", "null"], "description": "Pass null to clear the sale"},
            },
            "required": ["product_id", "sale_price"],
        },
    },
    {
        "name": "delete_product",
        "description": "Soft-delete a product (sets is_active=false). Requires confirmed=true.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "confirmed":  {"type": "boolean"},
            },
            "required": ["product_id", "confirmed"],
        },
    },
    {
        "name": "low_stock_report",
        "description": "List products where any size has stock below the threshold (default 5). Max 12 rows.",
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold": {"type": "integer", "default": 5},
            },
        },
    },
    {
        "name": "top_sellers",
        "description": "Top-selling products by order count, max 12.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_sales_summary",
        "description": "Total orders and revenue.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _slug_for(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def run_tool(name: str, a: dict):
    with Session(engine) as s:
        try:
            if name == "list_products":
                q = select(Product).where(Product.is_active == True)
                if a.get("gender"):
                    q = q.where(Product.gender == a["gender"])
                if a.get("family"):
                    q = q.where(Product.family == a["family"])
                if a.get("concentration"):
                    q = q.where(Product.concentration == a["concentration"])
                rows = list(s.exec(q).all())
                if a.get("name_contains"):
                    rows = [p for p in rows if a["name_contains"].lower() in p.name.lower()]
                return [
                    {
                        "id": p.id, "name": p.name, "brand": p.brand,
                        "gender": p.gender, "family": p.family,
                        "concentration": p.concentration,
                        "sizes": p.sizes,
                        "sale_price": p.sale_price,
                    }
                    for p in rows[:12]
                ]

            if name == "create_product":
                slug_base = _slug_for(a["name"])
                # Ensure slug uniqueness
                slug = slug_base
                n = 1
                while s.exec(select(Product).where(Product.slug == slug)).first():
                    slug = f"{slug_base}-{n}"; n += 1

                sizes = a.get("sizes") or [
                    {"ml": 30,  "price": 65.0,  "stock": 20},
                    {"ml": 50,  "price": 95.0,  "stock": 20},
                    {"ml": 100, "price": 135.0, "stock": 20},
                ]
                img = f"https://loremflickr.com/600/760/perfume,bottle?lock={hash(slug) % 10000}"
                p = Product(
                    slug=slug,
                    name=a["name"],
                    brand=a.get("brand", ""),
                    gender=a.get("gender", "Unisex"),
                    family=a["family"],
                    concentration=a["concentration"],
                    top_notes=a.get("top_notes", []),
                    heart_notes=a.get("heart_notes", []),
                    base_notes=a.get("base_notes", []),
                    sizes=sizes,
                    longevity=a.get("longevity", 6),
                    sillage=a.get("sillage", 6),
                    bottle_color=a.get("bottle_color", "#C8A951"),
                    cap_style=a.get("cap_style", "round"),
                    description=a.get("description", ""),
                    collection=a.get("collection", ""),
                    perfumer=a.get("perfumer", ""),
                    year=a.get("year"),
                    season=a.get("season", []),
                    occasion=a.get("occasion", []),
                    tags=a.get("tags", []),
                    images=[img],
                )
                s.add(p)
                s.commit()
                s.refresh(p)
                return {"created_id": p.id, "slug": p.slug}

            if name == "update_price":
                p = s.get(Product, a["product_id"])
                if not p:
                    return {"error": "product not found"}
                sizes = [sz for sz in (p.sizes or []) if isinstance(sz, dict)]
                target = next((sz for sz in sizes if sz.get("ml") == a["size_ml"]), None)
                if target is None:
                    return {"error": f"size {a['size_ml']}ml not found"}
                target["price"] = float(a["price"])
                p.sizes = sizes
                s.add(p)
                s.commit()
                return {"ok": True}

            if name == "set_stock":
                p = s.get(Product, a["product_id"])
                if not p:
                    return {"error": "product not found"}
                sizes = [sz for sz in (p.sizes or []) if isinstance(sz, dict)]
                target = next((sz for sz in sizes if sz.get("ml") == a["size_ml"]), None)
                if target is None:
                    return {"error": f"size {a['size_ml']}ml not found"}
                target["stock"] = int(a["stock"])
                p.sizes = sizes
                s.add(p)
                s.commit()
                return {"ok": True}

            if name == "set_sale_price":
                p = s.get(Product, a["product_id"])
                if not p:
                    return {"error": "product not found"}
                p.sale_price = float(a["sale_price"]) if a.get("sale_price") is not None else None
                s.add(p)
                s.commit()
                return {"ok": True}

            if name == "delete_product":
                if not a.get("confirmed"):
                    return {"error": "ask the admin to confirm deletion first; only proceed when they say yes"}
                p = s.get(Product, a["product_id"])
                if not p:
                    return {"error": "product not found"}
                p.is_active = False
                s.add(p)
                s.commit()
                return {"ok": True, "deleted": p.name}

            if name == "low_stock_report":
                threshold = int(a.get("threshold", 5))
                rows = s.exec(select(Product).where(Product.is_active == True)).all()
                low = []
                for p in rows:
                    for sz in [sz for sz in (p.sizes or []) if isinstance(sz, dict)]:
                        if sz.get("stock", 0) < threshold:
                            low.append({
                                "id": p.id, "name": p.name,
                                "size_ml": sz.get("ml"), "stock": sz.get("stock", 0),
                            })
                return low[:12]

            if name == "top_sellers":
                from sqlalchemy import func
                result = s.exec(
                    select(OrderItem.product_id, func.count(OrderItem.id).label("cnt"))
                    .group_by(OrderItem.product_id)
                    .order_by(func.count(OrderItem.id).desc())
                ).all()
                out = []
                for row in result[:12]:
                    p = s.get(Product, row[0])
                    out.append({
                        "id": row[0],
                        "name": p.name if p else "?",
                        "orders": row[1],
                    })
                return out

            if name == "get_sales_summary":
                orders = s.exec(select(Order)).all()
                return {
                    "orders": len(orders),
                    "revenue": round(sum(o.total for o in orders), 2),
                }

        except Exception as e:
            return {"error": str(e)}

    return {"error": "unknown tool"}


# ── OpenAI-compatible chat (Gemini / other providers) ────────────────────────

OA_TOOLS = [{"type": "function", "function": {
    "name": t["name"],
    "description": t["description"],
    "parameters": t["input_schema"],
}} for t in TOOLS]


def chat_openai(messages: list[dict]) -> str:
    try:
        from openai import OpenAI
        oa = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
        )
        msgs = [{"role": "system", "content": SYSTEM}] + messages
        for _ in range(8):
            r = oa.chat.completions.create(
                model=os.getenv("LLM_MODEL"),
                messages=msgs,
                tools=OA_TOOLS,
                timeout=30,
            )
            m = r.choices[0].message
            if not m.tool_calls:
                return m.content or ""
            msgs.append(m)
            for c in m.tool_calls:
                out = run_tool(c.function.name, json.loads(c.function.arguments or "{}"))
                msgs.append({
                    "role": "tool",
                    "tool_call_id": c.id,
                    "content": json.dumps(out),
                })
        return "Too many tool steps — please rephrase."
    except Exception as e:
        return f"LLM error: {e}"


# ── Pydantic bodies ───────────────────────────────────────────────────────────

class LoginIn(BaseModel):
    username: str
    password: str


class ChatIn(BaseModel):
    messages: list[dict]


class StatusIn(BaseModel):
    status: str


# ── Auth endpoints (public) ───────────────────────────────────────────────────

@router.post("/login")
@limiter.limit("5/10minute")
def login(request: Request, body: LoginIn):
    with Session(engine) as s:
        user = s.exec(select(AdminUser).where(AdminUser.username == body.username)).first()
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    with Session(engine) as s:
        db_user = s.get(AdminUser, user.id)
        db_user.last_login = datetime.utcnow().isoformat()
        s.add(db_user)
        s.commit()

    token = create_token(user.username, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
    }


@router.get("/me")
def me(payload: dict = Depends(require_role("staff"))):
    with Session(engine) as s:
        user = s.exec(select(AdminUser).where(AdminUser.username == payload["sub"])).first()
    if not user:
        raise HTTPException(404, "User not found")
    return {"username": user.username, "role": user.role, "last_login": user.last_login}


# ── Order endpoints ───────────────────────────────────────────────────────────

@router.get("/orders")
def list_orders(payload: dict = Depends(require_role("staff"))):
    with Session(engine) as s:
        orders = s.exec(select(Order).order_by(Order.id.desc())).all()
        result = []
        for o in orders:
            items = s.exec(select(OrderItem).where(OrderItem.order_id == o.id)).all()
            d = o.model_dump()
            d["items"] = [i.model_dump() for i in items]
            result.append(d)
        return result


@router.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: int, body: StatusIn,
    payload: dict = Depends(require_role("staff")),
):
    with Session(engine) as s:
        o = s.get(Order, order_id)
        if not o:
            raise HTTPException(404, "Order not found")
        old_status = o.status
        o.status = body.status
        s.add(o)
        s.commit()
        log_action(s, payload["sub"], "update_status", "order", order_id,
                   f"{old_status} → {body.status}")
    return {"ok": True}


# ── Chat endpoint ─────────────────────────────────────────────────────────────

@router.post("/chat")
def chat(data: ChatIn, payload: dict = Depends(require_role("staff"))):
    # Prefer the OpenAI-compatible provider (Gemini, etc.) if configured
    if os.getenv("LLM_API_KEY"):
        return {"reply": chat_openai(data.messages)}

    # Fallback: Anthropic direct
    if MOCK:
        out = run_tool("get_sales_summary", {})
        return {"reply": f"[mock — no API key] Sales: {out}"}

    msgs = list(data.messages)
    for _ in range(8):
        resp = client.messages.create(
            model=MODEL, max_tokens=1024,
            system=SYSTEM, tools=TOOLS, messages=msgs,
        )
        if resp.stop_reason != "tool_use":
            return {"reply": "".join(b.text for b in resp.content if b.type == "text")}
        msgs.append({"role": "assistant", "content": resp.content})
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                results.append({
                    "type": "tool_result",
                    "tool_use_id": b.id,
                    "content": json.dumps(run_tool(b.name, b.input)),
                })
        msgs.append({"role": "user", "content": results})
    return {"reply": "Too many tool steps — please rephrase."}
