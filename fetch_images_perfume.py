"""
fetch_images_perfume.py
Downloads one representative photo per perfume into frontend/public/products/.
Sources:
  - If PIXABAY_API_KEY present in .env: Pixabay API, family-specific keywords.
  - Otherwise: loremflickr.com/600/760/perfume,bottle (lock=product.id, free).
Updates each product's images field in perfume.db.
Backs up perfume.db before writing.
API key is read from .env, never printed or logged.

Run: python fetch_images_perfume.py   (from backend/)
PHP equiv: php artisan storage:link  +  a custom Artisan command hitting an API.
Key concept: httpx (sync) replaces Laravel's Http facade for external requests.
"""
import os
import shutil
import time
from pathlib import Path
from dotenv import load_dotenv
import httpx
from sqlmodel import Session, select
from models import engine, Product

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent
FRONTEND_PUBLIC = BACKEND_DIR.parent / "frontend" / "public" / "products"
DB_PATH = BACKEND_DIR / "perfume.db"
DB_BACKUP = BACKEND_DIR / "perfume_before_images.db"

PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "")
USE_PIXABAY = bool(PIXABAY_KEY) and "your-key" not in PIXABAY_KEY.lower()

# ── Pixabay search terms per family ──────────────────────────────────────────
FAMILY_KEYWORDS: dict[str, str] = {
    "Floral":          "perfume bottle floral",
    "Woody":           "perfume bottle wood luxury",
    "Oriental/Amber":  "perfume bottle amber oriental",
    "Fresh/Aquatic":   "perfume bottle aquatic blue",
    "Citrus":          "perfume bottle citrus bright",
    "Gourmand":        "perfume bottle gold sweet",
    "Aromatic":        "perfume bottle herbal green",
    "Leather":         "perfume bottle dark leather",
    "Musk":            "perfume bottle white minimalist",
}


def backup_db() -> None:
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, DB_BACKUP)
        print(f"Backed up: {DB_BACKUP.name}")


def ensure_dir() -> None:
    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)


def _download(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 1000:
                dest.write_bytes(resp.content)
                return True
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(1.5)
    return False


def _pixabay_url(keyword: str, page: int) -> str | None:
    """Return first image URL from Pixabay for the keyword (key never logged)."""
    try:
        resp = httpx.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_KEY,         # key sent as param, not printed
                "q": keyword,
                "image_type": "photo",
                "orientation": "vertical",
                "per_page": 20,
                "page": page,
                "safesearch": "true",
            },
            timeout=15,
        )
        hits = resp.json().get("hits", [])
        if hits:
            return hits[0].get("webformatURL")
    except Exception:
        pass
    return None


def _loremflickr_url(product_id: int, keyword: str = "perfume,bottle") -> str:
    return f"https://loremflickr.com/600/760/{keyword}?lock={product_id}"


def main() -> None:
    backup_db()
    ensure_dir()

    with Session(engine) as session:
        products = list(session.exec(select(Product).order_by(Product.id)).all())  # type: ignore[arg-type]

    # Count per family (for the per-line report)
    family_counts: dict[str, int] = {}
    success = 0
    skip = 0

    # Pixabay: pre-fetch one URL per family to cycle through
    pixabay_cache: dict[str, str | None] = {}

    print(f"\nDownloading images for {len(products)} products "
          f"({'Pixabay' if USE_PIXABAY else 'loremflickr'})...\n")

    for idx, p in enumerate(products):
        dest = FRONTEND_PUBLIC / f"{p.slug}.jpg"

        if dest.exists() and dest.stat().st_size > 5000:
            skip += 1
            continue

        # Choose source URL
        if USE_PIXABAY:
            kw = FAMILY_KEYWORDS.get(p.family, "perfume bottle luxury")
            if kw not in pixabay_cache:
                page = 1 + (family_counts.get(p.family, 0) // 20)
                pixabay_cache[kw] = _pixabay_url(kw, page)
            img_url = pixabay_cache.get(kw) or _loremflickr_url(p.id or idx)
            # rotate cache for next product in same family
            pixabay_cache.pop(kw, None)
        else:
            img_url = _loremflickr_url(p.id or idx)

        ok = _download(img_url, dest)
        if ok:
            success += 1
            # Update product images in DB
            with Session(engine) as session:
                prod = session.get(Product, p.id)
                if prod:
                    prod.images = [f"/products/{p.slug}.jpg"]
                    session.add(prod)
                    session.commit()
        else:
            print(f"  WARN: failed to download image for {p.name}")

        family_counts[p.family] = family_counts.get(p.family, 0) + 1

        # Polite delay
        if not USE_PIXABAY:
            time.sleep(0.1)

    print("\n── Summary ──────────────────────────────────────────────────")
    for family, count in sorted(family_counts.items()):
        print(f"  {family:<22} {count} products")
    print(f"\n  Downloaded: {success}  |  Skipped (cached): {skip}")
    print(f"  Images saved to: {FRONTEND_PUBLIC}")
    print("Done.")


if __name__ == "__main__":
    main()
