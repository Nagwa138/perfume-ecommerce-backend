"""
JWT auth helpers, role guards, rate-limiter config, audit logger.
Import `require_admin` or `require_role("staff")` as FastAPI Depends().
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session, select

load_dotenv()

_JWT_SECRET = os.getenv("JWT_SECRET", "")
if not _JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set in .env")

_ALGORITHM = "HS256"
_TOKEN_TTL_HOURS = 8

# ── Rate limiter (attach to app in main.py) ───────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_token(username: str, role: str) -> str:
    exp = datetime.now(tz=timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)
    payload = {"sub": username, "role": role, "exp": exp}
    return jwt.encode(payload, _JWT_SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── FastAPI dependencies ──────────────────────────────────────────────────────

def _get_payload(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return decode_token(authorization.removeprefix("Bearer ").strip())


def require_admin(payload: dict = Depends(_get_payload)) -> dict:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return payload


def require_role(minimum: str):
    """
    minimum="staff" → accept staff or admin.
    minimum="admin" → accept admin only (same as require_admin).
    """
    allowed = {"staff", "admin"} if minimum == "staff" else {"admin"}

    def _dep(payload: dict = Depends(_get_payload)) -> dict:
        if payload.get("role") not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return payload

    return _dep


# ── Audit logger ──────────────────────────────────────────────────────────────

def log_action(
    session: Session,
    username: str,
    action: str,
    entity: str,
    entity_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    from models import AuditLog  # local import avoids circular dep

    entry = AuditLog(
        username=username,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
        created_at=datetime.utcnow().isoformat(),
    )
    session.add(entry)
    session.commit()
