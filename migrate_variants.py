"""
Additive migration — creates the product_variant table if it doesn't exist.
Existing tables and data are untouched (SQLModel.metadata.create_all is additive).

Run once:  python migrate_variants.py
The backend startup (main.py) also calls create_all, so simply restarting
the backend achieves the same result.
"""
from models import engine, SQLModel
from models import ProductVariant  # noqa: F401 — registers the model with metadata

SQLModel.metadata.create_all(engine)
print("Migration complete — product_variant table ready.")
