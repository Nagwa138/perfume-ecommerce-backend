"""
fetch_images_beauty.py
Downloads one representative photo per product across all beauty categories
(fragrance · skincare · makeup · haircare · body).

Sources:
  - If PIXABAY_API_KEY present in .env: Pixabay API, category-specific keywords.
  - Otherwise: loremflickr.com, keyword matched to product_type + subcategory.

Backs up perfume.db before writing. API key never printed or logged.

Run only after seed is confirmed:  python fetch_images_beauty.py  (from backend/)
PHP equiv: php artisan make:command FetchBeautyImages — a custom Artisan command
hitting an external image API, same pattern as this script using httpx instead of
Laravel's Http facade.
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
BACKEND_DIR    = Path(__file__).parent
FRONTEND_PUBLIC = BACKEND_DIR.parent / "frontend" / "public" / "products"
DB_PATH        = BACKEND_DIR / "perfume.db"
DB_BACKUP      = BACKEND_DIR / "perfume_before_beauty_images.db"

PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "")
USE_PIXABAY = bool(PIXABAY_KEY) and "your-key" not in PIXABAY_KEY.lower()

# ── Pixabay search terms: (product_type, subcategory_lower) → keyword ────────
# More specific sub-keys checked first; fall back to product_type key.
SUBCAT_KEYWORDS: dict[str, str] = {
    # Fragrance
    "floral":           "perfume bottle floral flowers",
    "woody":            "perfume bottle wood luxury",
    "oriental/amber":   "perfume bottle amber oriental",
    "fresh/aquatic":    "perfume bottle aquatic blue",
    "citrus":           "perfume bottle citrus bright",
    "gourmand":         "perfume bottle gold sweet",
    "aromatic":         "perfume bottle herbal green",
    "leather":          "perfume bottle dark leather",
    "musk":             "perfume bottle white minimalist",

    # Skincare subcategories
    "serum":            "serum face dropper bottle skincare",
    "moisturizer":      "moisturizer cream jar luxury",
    "eye cream":        "eye cream jar skincare",
    "cleanser":         "face cleanser skincare bottle foam",
    "toner":            "toner skincare bottle transparent",
    "face mask":        "face mask jar clay skincare",
    "spf":              "sunscreen spf bottle cream",
    "retinol":          "retinol serum bottle dark skincare",
    "vitamin c serum":  "vitamin c serum bottle orange skincare",

    # Makeup subcategories
    "lipstick":         "lipstick bullet tube luxury",
    "lip gloss":        "lip gloss tube makeup",
    "lip liner":        "lip liner pencil makeup",
    "foundation":       "foundation makeup bottle liquid",
    "concealer":        "concealer makeup bottle",
    "setting powder":   "setting powder compact makeup",
    "blush":            "blush compact pink makeup",
    "bronzer":          "bronzer compact makeup glow",
    "highlighter":      "highlighter compact makeup glow",
    "eyeshadow":        "eyeshadow palette makeup colors",
    "mascara":          "mascara tube wand makeup black",
    "eyeliner":         "eyeliner pen makeup",
    "brow":             "eyebrow pencil makeup",
    "nail polish":      "nail polish bottle lacquer",

    # Haircare subcategories
    "shampoo":          "shampoo bottle hair luxury",
    "conditioner":      "conditioner bottle hair",
    "hair mask":        "hair mask jar treatment",
    "hair oil":         "hair oil bottle dropper",
    "hair serum":       "hair serum bottle",
    "dry shampoo":      "dry shampoo spray bottle",

    # Body subcategories
    "body lotion":      "body lotion cream bottle luxury",
    "body oil":         "body oil bottle glass",
    "body scrub":       "body scrub jar exfoliant",
    "body wash":        "body wash shower gel bottle",
    "hand cream":       "hand cream tube luxury",
    "deodorant":        "deodorant stick bottle",
}

TYPE_KEYWORDS: dict[str, str] = {
    "perfume":  "perfume bottle luxury",
    "skincare": "skincare serum bottle cream",
    "makeup":   "makeup cosmetics luxury",
    "haircare": "hair product bottle shampoo",
    "body":     "body lotion cream bottle",
}

# loremflickr fallback keywords per product type
LF_TYPE: dict[str, str] = {
    "perfume":  "perfume,bottle",
    "skincare": "serum,skincare",
    "makeup":   "lipstick,makeup",
    "haircare": "shampoo,hair",
    "body":     "lotion,body",
}

LF_SUBCAT: dict[str, str] = {
    "serum":        "serum,skincare",
    "moisturizer":  "moisturizer,cream",
    "lipstick":     "lipstick,makeup",
    "foundation":   "foundation,makeup",
    "eyeshadow":    "eyeshadow,palette",
    "mascara":      "mascara,makeup",
    "nail polish":  "nailpolish,cosmetics",
    "shampoo":      "shampoo,bottle",
    "body lotion":  "lotion,body",
    "body oil":     "oil,body",
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


def _pixabay_url(keyword: str) -> str | None:
    """Return first image URL from Pixabay (key never logged)."""
    try:
        resp = httpx.get(
            "https://pixabay.com/api/",
            params={
                "key":          PIXABAY_KEY,
                "q":            keyword,
                "image_type":   "photo",
                "orientation":  "vertical",
                "per_page":     20,
                "page":         1,
                "safesearch":   "true",
            },
            timeout=15,
        )
        hits = resp.json().get("hits", [])
        if hits:
            return hits[0].get("webformatURL")
    except Exception:
        pass
    return None


def _loremflickr_url(product_id: int, keyword: str) -> str:
    return f"https://loremflickr.com/600/760/{keyword}?lock={product_id}"


def _keywords_for(p: Product) -> tuple[str, str]:
    """Return (pixabay_keyword, loremflickr_keyword) for a product."""
    sub = (p.subcategory or "").lower()
    fam = (p.family or "").lower()

    # Try subcategory first, then family (for fragrance), then type
    pix_kw = (
        SUBCAT_KEYWORDS.get(sub)
        or SUBCAT_KEYWORDS.get(fam)
        or TYPE_KEYWORDS.get(p.product_type, "beauty product bottle")
    )
    lf_kw = (
        LF_SUBCAT.get(sub)
        or LF_TYPE.get(p.product_type, "beauty,bottle")
    )
    return pix_kw, lf_kw


def main() -> None:
    backup_db()
    ensure_dir()

    with Session(engine) as session:
        products = list(session.exec(select(Product).order_by(Product.id)).all())  # type: ignore[arg-type]

    type_counts: dict[str, int] = {}
    success = 0
    skip = 0

    print(f"\nDownloading images for {len(products)} products "
          f"({'Pixabay' if USE_PIXABAY else 'loremflickr'})...\n")

    for idx, p in enumerate(products):
        dest = FRONTEND_PUBLIC / f"{p.slug}.jpg"

        if dest.exists() and dest.stat().st_size > 5000:
            skip += 1
            continue

        pix_kw, lf_kw = _keywords_for(p)

        if USE_PIXABAY:
            img_url = _pixabay_url(pix_kw) or _loremflickr_url(p.id or idx, lf_kw)
        else:
            img_url = _loremflickr_url(p.id or idx, lf_kw)

        ok = _download(img_url, dest)
        if ok:
            success += 1
            with Session(engine) as session:
                prod = session.get(Product, p.id)
                if prod:
                    prod.images = [f"/products/{p.slug}.jpg"]
                    session.add(prod)
                    session.commit()
            print(f"  OK  [{p.product_type:10}] {p.name}")
        else:
            print(f"  WARN: failed to download image for {p.name}")

        type_counts[p.product_type] = type_counts.get(p.product_type, 0) + 1

        if not USE_PIXABAY:
            time.sleep(0.1)

    print("\n── Summary ──────────────────────────────────────────────────")
    for t, count in sorted(type_counts.items()):
        print(f"  {t:<12} {count} products")
    print(f"\n  Downloaded: {success}  |  Skipped (cached): {skip}")
    print(f"  Images saved to: {FRONTEND_PUBLIC}")
    print("Done.")


if __name__ == "__main__":
    main()
