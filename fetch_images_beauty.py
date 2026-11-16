"""
fetch_images_beauty.py
Downloads high-quality representative photos for the seeded real products.
Uses Pixabay API if PIXABAY_API_KEY is in .env, otherwise falls back to loremflickr.
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import httpx
from sqlmodel import Session, select
from models import engine, Product

load_dotenv()

BACKEND_DIR = Path(__file__).parent
FRONTEND_PUBLIC = BACKEND_DIR.parent / "frontend" / "public" / "products"
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "")
USE_PIXABAY = bool(PIXABAY_KEY) and "your-key" not in PIXABAY_KEY.lower()

# Keyword mappings for cosmetic types
TYPE_KEYWORDS = {
    "skincare": "skincare bottle cream serum",
    "haircare": "shampoo bottle hair care",
    "perfume": "perfume bottle luxury",
    "makeup": "makeup cosmetics lipstick",
}

SUBCAT_KEYWORDS = {
    "serum": "serum dropper bottle",
    "moisturiser": "moisturizer cream jar",
    "cleanser": "face wash cleanser bottle",
    "shampoo": "shampoo bottle",
    "oil": "body oil glass bottle",
    "spf": "sunscreen bottle",
}

def _download(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 1000:
                dest.write_bytes(resp.content)
                return True
        except Exception:
            pass
        time.sleep(1.5)
    return False

def _pixabay_url(keyword: str) -> str | None:
    try:
        resp = httpx.get(
            "https://pixabay.com/api/",
            params={"key": PIXABAY_KEY, "q": keyword, "image_type": "photo", "orientation": "vertical", "per_page": 20},
            timeout=15,
        )
        hits = resp.json().get("hits", [])
        if hits:
            return hits[0].get("webformatURL")
    except Exception:
        pass
    return None

def main():
    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)
    
    with Session(engine) as session:
        products = list(session.exec(select(Product)).all())

    print(f"Fetching images for {len(products)} products...")
    
    for idx, p in enumerate(products):
        dest = FRONTEND_PUBLIC / f"{p.slug}.jpg"
        if dest.exists() and dest.stat().st_size > 5000:
            continue
            
        subcat = (p.subcategory or "").lower()
        keyword = SUBCAT_KEYWORDS.get(subcat) or TYPE_KEYWORDS.get(p.product_type, "beauty product")
        
        img_url = None
        if USE_PIXABAY:
            img_url = _pixabay_url(keyword)
            
        if not img_url:
            # Fallback to a clean, minimalist placeholder if Pixabay fails
            img_url = f"https://loremflickr.com/600/760/{keyword.replace(' ', ',')}?lock={p.id}"
            
        if _download(img_url, dest):
            with Session(engine) as session:
                prod = session.get(Product, p.id)
                if prod:
                    prod.images = [f"/products/{p.slug}.jpg"]
                    session.add(prod)
                    session.commit()
            print(f"  OK [{p.brand}] {p.name}")
        else:
            print(f"  WARN: failed for {p.name}")
            
        time.sleep(0.1) # Polite delay

if __name__ == "__main__":
    main()