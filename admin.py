import os, json
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

KEY = os.getenv("ANTHROPIC_API_KEY", "")
MOCK = (not KEY) or ("your-key" in KEY)
MODEL = "claude-sonnet-5-5"

if not MOCK:
    import anthropic
    client = anthropic.Anthropic(api_key=KEY)

SYSTEM = (
    "You are the store admin assistant for a clothing e-commerce shop. "
    "Use the tools to read and change the catalog. Never invent data. "
    "Before deleting a product, ask the admin to confirm; only pass confirmed=true after they say yes. "
    "Keep replies short."
)

TOOLS = [
    {"name": "list_products", "description": "List products, optionally filtered by department, category, subcategory or name text. Returns up to 12 results.",
     "input_schema": {"type": "object", "properties": {
         "department":  {"type": "string", "description": "Men, Women or Kids"},
         "category":    {"type": "string"},
         "subcategory": {"type": "string"},
         "name_contains": {"type": "string"}}}},
    {"name": "create_product", "description": "Create a new product.",
     "input_schema": {"type": "object", "properties": {
         "name":        {"type": "string"},
         "department":  {"type": "string"},
         "category":    {"type": "string"},
         "subcategory": {"type": "string"},
         "price":       {"type": "number"},
         "stock":       {"type": "integer"},
         "fit":         {"type": "string"},
         "fabric":      {"type": "string"},
         "collection":  {"type": "string"},
         "description": {"type": "string"}},
         "required": ["name", "category", "price"]}},
    {"name": "update_price", "description": "Set a product's price.",
     "input_schema": {"type": "object", "properties": {
         "product_id": {"type": "integer"}, "price": {"type": "number"}},
         "required": ["product_id", "price"]}},
    {"name": "set_stock", "description": "Set a product's stock quantity.",
     "input_schema": {"type": "object", "properties": {
         "product_id": {"type": "integer"}, "stock": {"type": "integer"}},
         "required": ["product_id", "stock"]}},
    {"name": "delete_product", "description": "Delete a product. Only with confirmed=true after the admin agreed.",
     "input_schema": {"type": "object", "properties": {
         "product_id": {"type": "integer"}, "confirmed": {"type": "boolean"}},
         "required": ["product_id", "confirmed"]}},
    {"name": "get_sales_summary", "description": "Number of orders and total revenue.",
     "input_schema": {"type": "object", "properties": {}}},
]


def run_tool(name: str, a: dict):
    with Session(engine) as s:
        if name == "list_products":
            q = select(Product).where(Product.is_active == True)
            if a.get("department"):
                q = q.where(Product.department == a["department"])
            if a.get("category"):
                q = q.where(Product.category == a["category"])
            if a.get("subcategory"):
                q = q.where(Product.subcategory == a["subcategory"])
            rows = s.exec(q).all()
            if a.get("name_contains"):
                rows = [p for p in rows if a["name_contains"].lower() in p.name.lower()]
            return [{"id": p.id, "name": p.name, "department": p.department,
                     "category": p.category, "subcategory": p.subcategory,
                     "price": p.price, "stock": p.stock} for p in rows[:12]]
        if name == "create_product":
            import re
            slug_base = re.sub(r"[^a-z0-9]+", "-", a["name"].lower()).strip("-")
            p = Product(
                slug=slug_base,
                name=a["name"],
                department=a.get("department", ""),
                category=a["category"],
                subcategory=a.get("subcategory", ""),
                price=a["price"],
                stock=a.get("stock", 10),
                fit=a.get("fit", ""),
                fabric=a.get("fabric", ""),
                collection=a.get("collection", ""),
                description=a.get("description", ""),
                image=f"https://picsum.photos/seed/{slug_base}/600/760",
                images=[f"https://picsum.photos/seed/{slug_base}/600/760"],
            )
            s.add(p); s.commit(); s.refresh(p)
            return {"created_id": p.id}
        if name in ("update_price", "set_stock", "delete_product"):
            p = s.get(Product, a["product_id"])
            if not p:
                return {"error": "product not found"}
            if name == "update_price":
                p.price = a["price"]; s.add(p)
            elif name == "set_stock":
                p.stock = a["stock"]; s.add(p)
            else:
                if not a.get("confirmed"):
                    return {"error": "ask the admin to confirm first"}
                p.is_active = False; s.add(p)  # soft-delete
            s.commit()
            return {"ok": True}
        if name == "get_sales_summary":
            orders = s.exec(select(Order)).all()
            return {"orders": len(orders), "revenue": round(sum(o.total for o in orders), 2)}
    return {"error": "unknown tool"}


OA_TOOLS = [{"type": "function", "function": {
    "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
    for t in TOOLS]


def chat_openai(messages: list[dict]) -> str:
    try:
        from openai import OpenAI
        oa = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"))
        msgs = [{"role": "system", "content": SYSTEM}] + messages
        for _ in range(6):
            r = oa.chat.completions.create(
                model=os.getenv("LLM_MODEL"), messages=msgs, tools=OA_TOOLS, timeout=30
            )
            m = r.choices[0].message
            if not m.tool_calls:
                return m.content or ""
            msgs.append(m)
            for c in m.tool_calls:
                out = run_tool(c.function.name, json.loads(c.function.arguments or "{}"))
                msgs.append({"role": "tool", "tool_call_id": c.id, "content": json.dumps(out)})
        return "Too many steps, please rephrase."
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

    # Update last_login
    with Session(engine) as s:
        db_user = s.get(AdminUser, user.id)
        db_user.last_login = datetime.utcnow().isoformat()
        s.add(db_user)
        s.commit()

    token = create_token(user.username, user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "username": user.username}


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
def update_order_status(order_id: int, body: StatusIn, payload: dict = Depends(require_role("staff"))):
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
    if os.getenv("LLM_API_KEY"):
        return {"reply": chat_openai(data.messages)}

    if MOCK:
        out = run_tool("get_sales_summary", {})
        return {"reply": f"[mock mode, no API key] Sales so far: {out}"}

    msgs = list(data.messages)
    for _ in range(6):
        resp = client.messages.create(model=MODEL, max_tokens=1024,
                                      system=SYSTEM, tools=TOOLS, messages=msgs)
        if resp.stop_reason != "tool_use":
            return {"reply": "".join(b.text for b in resp.content if b.type == "text")}
        msgs.append({"role": "assistant", "content": resp.content})
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                results.append({"type": "tool_result", "tool_use_id": b.id,
                                "content": json.dumps(run_tool(b.name, b.input))})
        msgs.append({"role": "user", "content": results})
    return {"reply": "Too many steps, please rephrase."}
