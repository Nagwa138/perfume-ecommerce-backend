"""
Additive migration for Step 1 (admin auth).

Safe to run multiple times — never drops or truncates anything.

What it does:
  1. Backs up shop.db → shop.db.bak
  2. CREATE TABLE admin_user IF NOT EXISTS
  3. CREATE TABLE audit_log IF NOT EXISTS
  4. ALTER TABLE product ADD COLUMN is_active BOOLEAN DEFAULT 1 (if missing)

Run with:  python migrate_admin.py
"""

import shutil
import sqlite3
from pathlib import Path

from sqlmodel import SQLModel

from models import engine, AdminUser, AuditLog  # noqa: F401 — registers tables

DB_PATH = Path("shop.db")
BAK_PATH = Path("shop.db.bak")

# 1. Backup ────────────────────────────────────────────────────────────────────
print(f"Backing up {DB_PATH} → {BAK_PATH}")
shutil.copy2(DB_PATH, BAK_PATH)
print("  Backup done.")

# 2. Create new tables (admin_user, audit_log) via SQLModel ───────────────────
print("Running SQLModel create_all (new tables only)…")
SQLModel.metadata.create_all(engine)
print("  Tables ensured.")

# 3. ALTER TABLE product ADD COLUMN is_active if missing ──────────────────────
con = sqlite3.connect(DB_PATH)
cur = con.cursor()
existing_cols = {row[1] for row in cur.execute("PRAGMA table_info(product)")}
if "is_active" not in existing_cols:
    print("Adding is_active column to product table…")
    cur.execute("ALTER TABLE product ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
    con.commit()
    print("  Column added.")
else:
    print("  is_active column already exists — skipping.")
con.close()

print("\nMigration complete. ✓")
