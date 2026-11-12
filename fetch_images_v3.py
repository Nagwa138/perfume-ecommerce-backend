"""
fetch_images_v3.py — replace picsum placeholders with category-matched photos.

Logic:
  1. Back up shop.db → shop.db.bak before any writes.
  2. If PIXABAY_API_KEY is set, search Pixabay with the specific keyword for
     each subcategory; if Pixabay returns 0 hits, retry with a broader fallback
     keyword. The keyword used is shown in the per-subcategory output line.
  3. If Pixabay is unavailable or returns nothing, use loremflickr with the
     same keyword downloaded locally.
  4. Update Product.image and Product.images only — no other fields touched.
  5. Print one line per subcategory: name, count, keyword used.
  6. Print final count of products whose image is still a picsum URL (target 0).

Run:  python fetch_images_v3.py
"""

import os, re, json, time, shutil, urllib.request, urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import Session, select
from models import engine, Product

load_dotenv()
_KEY       = os.getenv("PIXABAY_API_KEY", "")   # never printed
USE_PIXABAY = bool(_KEY)

IMG_DIR = Path(__file__).parent.parent / "frontend" / "public" / "products"
DB_PATH = Path(__file__).parent / "shop.db"
IMG_DIR.mkdir(parents=True, exist_ok=True)

# ── Keyword table: specific → broader fallback ────────────────────────────────
# Format: "Subcategory": ("specific keyword", "broader fallback")
KEYWORDS: dict[str, tuple[str, str]] = {
    # Tops
    "T-Shirts":          ("fashion tshirt",           "shirt"),
    "Polos":             ("polo shirt fashion",        "shirt"),
    "Shirts":            ("casual shirt fashion",      "shirt"),
    "Tank Tops":         ("tank top fashion",          "top"),
    "Long Sleeves":      ("long sleeve shirt",         "shirt"),
    "Crop Tops":         ("crop top women",            "top"),
    # Hoodies & Sweatshirts
    "Pullover":          ("pullover hoodie",           "hoodie"),
    "Zip Hoodie":        ("zip hoodie fashion",        "hoodie"),
    "Crewneck":          ("crewneck sweatshirt",       "sweatshirt"),
    "Oversized":         ("oversized hoodie street",   "hoodie"),
    # Knitwear
    "Sweaters":          ("knit sweater fashion",      "sweater"),
    "Cardigans":         ("cardigan fashion",          "cardigan"),
    "Turtlenecks":       ("turtleneck sweater",        "sweater"),
    # Outerwear
    "Bomber":            ("bomber jacket fashion",     "jacket"),
    "Denim Jacket":      ("denim jacket fashion",      "jacket"),
    "Puffer":            ("puffer jacket winter",      "jacket"),
    "Leather Jacket":    ("leather jacket fashion",    "jacket"),
    "Windbreaker":       ("windbreaker jacket",        "jacket"),
    "Trench":            ("trench coat fashion",       "coat"),
    "Wool Coat":         ("wool coat women fashion",   "coat"),
    "Blazer":            ("blazer fashion women",      "blazer"),
    # Bottoms
    "Jeans":             ("jeans denim fashion",       "jeans"),
    "Cargo Pants":       ("cargo pants street",        "pants"),
    "Joggers":           ("jogger pants fashion",      "pants"),
    "Chinos":            ("chino pants men",           "pants"),
    "Shorts":            ("shorts summer fashion",     "shorts"),
    "Skirts":            ("skirt women fashion",       "skirt"),
    # Dresses
    "Mini":              ("mini dress women fashion",  "dress"),
    "Midi":              ("midi dress women fashion",  "dress"),
    "Maxi":              ("maxi dress women fashion",  "dress"),
    # Activewear
    "Leggings":          ("leggings athletic women",   "leggings"),
    "Sports Bras":       ("sports bra women",          "sportswear"),
    "Track Pants":       ("track pants sport",         "pants"),
    "Training Tees":     ("training shirt athlete",    "shirt"),
    # Loungewear
    "Loungewear Sets":   ("loungewear set women",      "loungewear"),
    # Footwear
    "Sneakers":          ("sneakers shoes fashion",    "shoes"),
    "Boots":             ("boots fashion street",      "boots"),
    "Loafers":           ("loafers shoes fashion",     "shoes"),
    "Slides":            ("slides sandals fashion",    "sandals"),
    "Sandals":           ("sandals heels women",       "sandals"),
    # Accessories
    "Caps":              ("cap hat streetwear",        "hat"),
    "Beanies":           ("beanie hat fashion",        "hat"),
    "Bags & Backpacks":  ("backpack fashion street",   "backpack"),
    "Belts":             ("belt fashion",              "belt"),
    "Sunglasses":        ("sunglasses fashion",        "sunglasses"),
    "Socks":             ("socks fashion",             "socks"),
    "Scarves":           ("scarf women fashion",       "scarf"),
    "Watches":           ("watch fashion",             "watch"),
}

def _default_kw(subcategory: str) -> tuple[str, str]:
    return (subcategory + " fashion", subcategory)

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

# ── Pixabay ───────────────────────────────────────────────────────────────────

_pix_cache: dict[str, list[str]] = {}

def pixabay_urls(keyword: str, per_page: int = 12) -> list[str]:
    """Returns download URLs from Pixabay. Returns [] on any error."""
    if keyword in _pix_cache:
        return _pix_cache[keyword]
    qs = urllib.parse.urlencode({
        "key":         _KEY,
        "q":           keyword,
        "image_type":  "photo",
        "per_page":    per_page,
        "safesearch":  "true",
        "orientation": "vertical",
    })
    try:
        req = urllib.request.Request(
            f"https://pixabay.com/api/?{qs}",
            headers={"User-Agent": "NovaSeedScript/1.0"},
        )
        with urllib.request.urlopen(req, timeout=14) as r:
            data = json.loads(r.read())
        urls = [h["webformatURL"] for h in data.get("hits", [])]
        _pix_cache[keyword] = urls
        time.sleep(0.25)
        return urls
    except Exception as err:
        print(f"      [pixabay error] '{keyword}': {type(err).__name__}")
        _pix_cache[keyword] = []
        return []

# ── Download helper ───────────────────────────────────────────────────────────

def _download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=14) as r, open(dest, "wb") as f:
            f.write(r.read())
        ok = dest.stat().st_size > 2_000
        if not ok:
            dest.unlink(missing_ok=True)
        return ok
    except Exception:
        dest.unlink(missing_ok=True)
        return False

# ── Per-product image resolution ─────────────────────────────────────────────

def resolve_image(product_id: int, subcategory: str) -> tuple[str, str]:
    """
    Returns (web_path, keyword_used).
    Downloads locally; falls back through broader keyword → loremflickr.
    """
    specific, broad = KEYWORDS.get(subcategory, _default_kw(subcategory))
    slug     = f"{slugify(subcategory)}-{product_id}"
    local    = IMG_DIR / f"{slug}.jpg"
    web_path = f"/products/{slug}.jpg"

    # Always re-download (removes any stale picsum content)
    local.unlink(missing_ok=True)

    # ── Pixabay: try specific keyword, then broad fallback ───────────────
    if USE_PIXABAY:
        for kw in (specific, broad):
            urls = pixabay_urls(kw)
            if urls:
                url = urls[product_id % len(urls)]
                if _download(url, local):
                    return web_path, kw

    # ── Loremflickr: use first word of specific keyword for best results ─
    lf_kw  = specific.split()[0]
    lf_url = (
        f"https://loremflickr.com/600/760/"
        f"{urllib.parse.quote(lf_kw)}"
        f"?lock={product_id}"
    )
    if _download(lf_url, local):
        return web_path, f"[loremflickr] {lf_kw}"

    # ── Last resort: return the URL directly (no local file) ────────────
    return lf_url, f"[fallback-url] {lf_kw}"

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    bak = DB_PATH.with_suffix(".db.bak")
    shutil.copy2(DB_PATH, bak)
    print(f"DB backed up     : {bak.name}")
    print(f"Image source     : {'Pixabay (key present, length=' + str(len(_KEY)) + ')' if USE_PIXABAY else 'loremflickr only (no key)'}")
    print()
    print(f"  {'Subcategory':<30s} {'Count':>5}  Keyword used")
    print(f"  {'-'*30} {'-'*5}  {'-'*30}")

    with Session(engine) as s:
        products = s.exec(select(Product)).all()

        by_subcat: dict[str, list[Product]] = {}
        for p in products:
            sc = p.subcategory or "Unknown"
            by_subcat.setdefault(sc, []).append(p)

        still_picsum = 0
        keyword_log: dict[str, str] = {}

        for subcat in sorted(by_subcat):
            prods = by_subcat[subcat]
            count = 0
            last_kw = ""
            for p in prods:
                web, kw = resolve_image(p.id, subcat)
                p.image  = web
                p.images = [web]
                s.add(p)
                count += 1
                last_kw = kw
                if "picsum" in web:
                    still_picsum += 1
            keyword_log[subcat] = last_kw
            print(f"  {subcat:<30s} {count:5d}  {last_kw}")

        s.commit()

    total = sum(len(v) for v in by_subcat.values())
    print()
    print(f"Total products updated : {total}")
    print(f"Still picsum.photos    : {still_picsum}  (target: 0)")


if __name__ == "__main__":
    main()
