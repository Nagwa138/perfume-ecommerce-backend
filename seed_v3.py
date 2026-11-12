"""
seed_v3.py — full taxonomy seed for NOVA WEAR
Drops and recreates all tables, seeds ~120 products across Men/Women/Kids,
downloads images from Pixabay (falls back to loremflickr), adds reviews,
and creates a SAVE20 coupon.

Run: python seed_v3.py
"""

import os, re, hashlib, urllib.request
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, select
from models import engine, Product, Review, Order, OrderItem, Coupon

load_dotenv()
IMG_DIR = Path(__file__).parent.parent / "frontend" / "public" / "products"
IMG_DIR.mkdir(parents=True, exist_ok=True)

# ── Deterministic helpers ─────────────────────────────────────────────────────

def _h(s: str) -> int:
    """Short deterministic hash → small integer."""
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)

def _pick(seq, seed_str: str):
    return seq[_h(seed_str) % len(seq)]

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

# ── Image fetching ─────────────────────────────────────────────────────────────

def get_image(query: str, product_id: int) -> str:
    """Download image from picsum.photos → /products/<slug>.jpg and return web path."""
    slug = f"{slugify(query)}-{product_id}"
    local = IMG_DIR / f"{slug}.jpg"
    web_path = f"/products/{slug}.jpg"

    if local.exists():
        return web_path

    # picsum.photos: deterministic seed = product_id, portrait crop
    url = f"https://picsum.photos/seed/nova{product_id}/600/760"
    try:
        urllib.request.urlretrieve(url, local)
        return web_path
    except Exception:
        pass

    # Absolute fallback: return a stable external URL
    return f"https://picsum.photos/seed/nova{product_id}/600/760"


# ── Product catalogue definition ───────────────────────────────────────────────

COLLECTIONS = ["Night City", "Heritage Denim", "Street Archive", "Solar Club", "Arctic Drift"]
FITS        = ["slim", "regular", "relaxed", "oversized"]
SEASONS     = ["all-season", "summer", "winter", "spring-fall"]

COLOR_PALETTE = [
    {"name": "Black",        "hex": "#111111"},
    {"name": "White",        "hex": "#f5f5f5"},
    {"name": "Charcoal",     "hex": "#3d3d3d"},
    {"name": "Navy",         "hex": "#1e3a5f"},
    {"name": "Stone",        "hex": "#a89880"},
    {"name": "Forest",       "hex": "#2d4a3e"},
    {"name": "Burgundy",     "hex": "#6b2737"},
    {"name": "Violet",       "hex": "#5b3fa6"},
    {"name": "Sky Blue",     "hex": "#5ba4cf"},
    {"name": "Sand",         "hex": "#c8b89a"},
    {"name": "Rust",         "hex": "#b55233"},
    {"name": "Olive",        "hex": "#6b6b3a"},
]

SIZE_MAP = {
    "Footwear":    ["UK6", "UK7", "UK8", "UK9", "UK10", "UK11"],
    "Accessories": ["One Size"],
    "default":     ["XS", "S", "M", "L", "XL", "XXL"],
}

FABRICS = {
    "Tops":                  "100% Combed Cotton",
    "Hoodies & Sweatshirts": "80% Cotton, 20% Polyester Fleece",
    "Knitwear":              "55% Merino Wool, 45% Acrylic",
    "Outerwear":             "Shell: 100% Nylon, Lining: 100% Polyester",
    "Bottoms":               "98% Cotton, 2% Elastane",
    "Dresses":               "100% Viscose",
    "Activewear":            "88% Polyester, 12% Elastane",
    "Loungewear":            "60% Cotton, 40% Modal",
    "Footwear":              "Upper: Synthetic Leather, Sole: Vulcanised Rubber",
    "Accessories":           "Various",
}

CARE = "Machine wash cold. Tumble dry low. Do not bleach. Iron on low heat."

REVIEWS_POOL = [
    ("Alex M.", 5, "Perfect fit", "Exactly as described, super comfortable."),
    ("Jordan K.", 4, "Great quality", "Love the material, runs slightly large."),
    ("Sam T.", 5, "My new favourite", "Wearing this every week. Highly recommend."),
    ("Taylor R.", 3, "Decent", "Good but arrived with a loose thread."),
    ("Morgan L.", 5, "Fire 🔥", "The colour is even better in person."),
    ("Casey B.", 4, "Solid piece", "Quality is there. Shipping was fast too."),
    ("Riley D.", 5, "Top tier", "Exactly what I needed for the season."),
    ("Quinn F.", 4, "Very happy", "Second time buying this brand. Never disappoint."),
    ("Avery N.", 2, "Sizing off", "Runs very small, exchange was easy though."),
    ("Dakota S.", 5, "Worth every penny", "Premium feel, looks expensive. 10/10."),
    ("Sage W.", 4, "Love it", "Great everyday piece. Washes well."),
    ("Phoenix G.", 3, "OK", "Nothing special but decent for the price."),
]

# (department, category, subcategory, name, search_query)
PRODUCTS: list[tuple] = [
    # ── MEN ──────────────────────────────────────────────────────────────────
    # Tops
    ("Men", "Tops", "T-Shirts",    "Night City Oversized Tee",        "streetwear oversized tshirt men"),
    ("Men", "Tops", "T-Shirts",    "Archive Washed Tee",              "vintage wash tshirt men fashion"),
    ("Men", "Tops", "T-Shirts",    "Solar Graphic Tee",               "graphic tshirt men urban"),
    ("Men", "Tops", "Polos",       "Heritage Piqué Polo",             "polo shirt men fashion"),
    ("Men", "Tops", "Shirts",      "Linen Overshirt",                 "linen overshirt men summer"),
    ("Men", "Tops", "Tank Tops",   "Ribbed Tank",                     "ribbed tank top men gym"),
    ("Men", "Tops", "Long Sleeves","Thermal Long Sleeve",             "thermal long sleeve top men"),
    # Hoodies
    ("Men", "Hoodies & Sweatshirts", "Pullover",   "Classic Pullover Hoodie",    "pullover hoodie men streetwear"),
    ("Men", "Hoodies & Sweatshirts", "Zip Hoodie", "Full-Zip Tech Hoodie",       "zip hoodie men street style"),
    ("Men", "Hoodies & Sweatshirts", "Crewneck",   "Heavyweight Crewneck",       "crewneck sweatshirt men fashion"),
    ("Men", "Hoodies & Sweatshirts", "Oversized",  "Dropped Shoulder Hoodie",    "oversized hoodie men drop shoulder"),
    # Knitwear
    ("Men", "Knitwear", "Sweaters",    "Merino Knit Sweater",        "merino wool sweater men"),
    ("Men", "Knitwear", "Cardigans",   "Open-Front Cardigan",        "cardigan men street style"),
    ("Men", "Knitwear", "Turtlenecks", "Slim Turtleneck",            "turtleneck sweater men"),
    # Outerwear
    ("Men", "Outerwear", "Bomber",         "Satin Flight Bomber",        "bomber jacket men fashion"),
    ("Men", "Outerwear", "Denim Jacket",   "Acid-Wash Denim Jacket",     "denim jacket men vintage"),
    ("Men", "Outerwear", "Puffer",         "Arctic Puffer Jacket",       "puffer jacket men winter"),
    ("Men", "Outerwear", "Leather Jacket", "Moto Leather Jacket",        "leather jacket men biker"),
    ("Men", "Outerwear", "Windbreaker",    "Packable Windbreaker",       "windbreaker jacket men"),
    ("Men", "Outerwear", "Trench",         "Classic Trench Coat",        "trench coat men fashion"),
    # Bottoms
    ("Men", "Bottoms", "Jeans",       "Slim Raw Denim Jeans",       "slim jeans men denim"),
    ("Men", "Bottoms", "Cargo Pants", "Tactical Cargo Pants",       "cargo pants men streetwear"),
    ("Men", "Bottoms", "Joggers",     "French Terry Joggers",       "jogger pants men fashion"),
    ("Men", "Bottoms", "Chinos",      "Slim Stretch Chinos",        "chino pants men slim"),
    ("Men", "Bottoms", "Shorts",      "Nylon Cargo Shorts",         "cargo shorts men summer"),
    # Activewear
    ("Men", "Activewear", "Track Pants",   "Side-Stripe Track Pants",  "track pants men sport"),
    ("Men", "Activewear", "Training Tees", "Dry-Fit Training Tee",     "training tshirt men gym"),
    # Footwear
    ("Men", "Footwear", "Sneakers", "Court Low Sneakers",         "sneakers men white court"),
    ("Men", "Footwear", "Sneakers", "Chunky Sole Trainers",       "chunky sneakers men fashion"),
    ("Men", "Footwear", "Boots",    "Lace-Up Combat Boots",       "combat boots men fashion"),
    ("Men", "Footwear", "Loafers",  "Penny Loafers",              "loafers men leather"),
    ("Men", "Footwear", "Slides",   "Foam Slides",                "slides sandals men summer"),
    # Accessories
    ("Men", "Accessories", "Caps",             "6-Panel Snapback",         "snapback cap men streetwear"),
    ("Men", "Accessories", "Beanies",          "Ribbed Knit Beanie",       "beanie hat men winter"),
    ("Men", "Accessories", "Bags & Backpacks", "30L Rolltop Backpack",     "backpack men street urban"),
    ("Men", "Accessories", "Belts",            "Tactical Webbing Belt",    "belt men tactical"),
    ("Men", "Accessories", "Sunglasses",       "Wraparound Sunglasses",    "sunglasses men fashion"),
    ("Men", "Accessories", "Socks",            "Quarter Ankle Sock 3-Pack","socks men pack"),

    # ── WOMEN ────────────────────────────────────────────────────────────────
    # Tops
    ("Women", "Tops", "T-Shirts",    "Boyfriend Fit Tee",          "tshirt women oversized fashion"),
    ("Women", "Tops", "Crop Tops",   "Ribbed Crop Top",            "crop top women ribbed"),
    ("Women", "Tops", "Shirts",      "Tie-Front Shirt",            "tie front shirt women"),
    ("Women", "Tops", "Tank Tops",   "Satin Cami Top",             "cami top women satin"),
    ("Women", "Tops", "Long Sleeves","Thermal Long Sleeve",        "long sleeve top women tight"),
    # Hoodies
    ("Women", "Hoodies & Sweatshirts", "Pullover",   "Soft-Wash Hoodie",      "hoodie women soft pastel"),
    ("Women", "Hoodies & Sweatshirts", "Zip Hoodie", "Cropped Zip Hoodie",    "crop zip hoodie women"),
    ("Women", "Hoodies & Sweatshirts", "Crewneck",   "Vintage Crewneck",      "crewneck sweatshirt women vintage"),
    ("Women", "Hoodies & Sweatshirts", "Oversized",  "Oversized Logo Hoodie", "oversized hoodie women logo"),
    # Knitwear
    ("Women", "Knitwear", "Sweaters",    "Mohair Blend Sweater",    "mohair sweater women fashion"),
    ("Women", "Knitwear", "Cardigans",   "Longline Cardigan",       "longline cardigan women"),
    ("Women", "Knitwear", "Turtlenecks", "Chunky Knit Turtleneck",  "chunky turtleneck women winter"),
    # Outerwear
    ("Women", "Outerwear", "Bomber",       "Floral Embroidered Bomber","bomber jacket women floral"),
    ("Women", "Outerwear", "Puffer",       "Short Puffer Jacket",      "puffer jacket women short"),
    ("Women", "Outerwear", "Leather Jacket","Belted Leather Jacket",   "leather jacket women belted"),
    ("Women", "Outerwear", "Windbreaker",  "Colour-Block Windbreaker", "windbreaker women colourblock"),
    ("Women", "Outerwear", "Trench",       "Double-Breasted Trench",   "trench coat women fashion"),
    ("Women", "Outerwear", "Wool Coat",    "Longline Wool Coat",       "wool coat women long"),
    ("Women", "Outerwear", "Blazer",       "Oversized Blazer",         "blazer women oversized"),
    # Bottoms
    ("Women", "Bottoms", "Jeans",       "High-Rise Straight Jeans", "jeans women high waist"),
    ("Women", "Bottoms", "Cargo Pants", "Wide-Leg Cargo Pants",     "cargo pants women wide leg"),
    ("Women", "Bottoms", "Joggers",     "Velour Joggers",           "velour joggers women"),
    ("Women", "Bottoms", "Shorts",      "Linen Shorts",             "linen shorts women summer"),
    ("Women", "Bottoms", "Skirts",      "Mini Denim Skirt",         "denim skirt women mini"),
    # Dresses
    ("Women", "Dresses", "Mini",   "Slip Mini Dress",          "slip dress women mini"),
    ("Women", "Dresses", "Midi",   "Floral Midi Dress",        "midi dress women floral"),
    ("Women", "Dresses", "Maxi",   "Linen Maxi Dress",         "maxi dress women linen summer"),
    # Activewear
    ("Women", "Activewear", "Leggings",      "High-Waist Seamless Leggings","leggings women seamless"),
    ("Women", "Activewear", "Sports Bras",   "Medium-Support Sports Bra",   "sports bra women"),
    ("Women", "Activewear", "Track Pants",   "Wide-Leg Track Pants",        "track pants women fashion"),
    ("Women", "Activewear", "Training Tees", "Mesh-Panel Training Tee",     "training top women gym"),
    # Loungewear
    ("Women", "Loungewear", "Loungewear Sets", "Matching Loungewear Set",   "loungewear set women matching"),
    # Footwear
    ("Women", "Footwear", "Sneakers", "Platform Low-Tops",         "platform sneakers women fashion"),
    ("Women", "Footwear", "Boots",    "Ankle Chelsea Boots",        "chelsea boots women ankle"),
    ("Women", "Footwear", "Sandals",  "Strappy Heeled Sandals",     "heeled sandals women strappy"),
    ("Women", "Footwear", "Slides",   "Quilted Slides",             "quilted slides women"),
    ("Women", "Footwear", "Loafers",  "Patent Loafers",             "loafers women patent"),
    # Accessories
    ("Women", "Accessories", "Caps",             "Corduroy Bucket Hat",      "bucket hat women fashion"),
    ("Women", "Accessories", "Beanies",          "Pom-Pom Beanie",           "beanie women pom pom"),
    ("Women", "Accessories", "Bags & Backpacks", "Mini Crossbody Bag",       "crossbody bag women mini"),
    ("Women", "Accessories", "Belts",            "Chain Link Belt",           "chain belt women fashion"),
    ("Women", "Accessories", "Sunglasses",       "Butterfly Sunglasses",      "butterfly sunglasses women"),
    ("Women", "Accessories", "Socks",            "Sheer Ankle Socks 3-Pack",  "sheer socks women pack"),
    ("Women", "Accessories", "Scarves",          "Cashmere Feel Scarf",       "scarf women winter"),
    ("Women", "Accessories", "Watches",          "Minimalist Mesh Watch",     "minimalist watch women"),

    # ── KIDS ─────────────────────────────────────────────────────────────────
    # Tops
    ("Kids", "Tops", "T-Shirts",    "Dino Graphic Tee",           "kids tshirt graphic fun"),
    ("Kids", "Tops", "T-Shirts",    "Colourblock Tee",            "kids colourblock tshirt"),
    ("Kids", "Tops", "Long Sleeves","Stripe Long Sleeve",         "kids long sleeve stripe top"),
    # Hoodies
    ("Kids", "Hoodies & Sweatshirts", "Pullover",   "Fleece Pullover Hoodie",  "kids hoodie fleece"),
    ("Kids", "Hoodies & Sweatshirts", "Zip Hoodie", "Full-Zip Hoodie",         "kids zip hoodie"),
    # Outerwear
    ("Kids", "Outerwear", "Puffer",      "Lightweight Puffer",    "kids puffer jacket light"),
    ("Kids", "Outerwear", "Windbreaker", "Rain-Resistant Shell",  "kids windbreaker jacket"),
    # Bottoms
    ("Kids", "Bottoms", "Jeans",   "Slim Stretch Jeans",         "kids jeans slim"),
    ("Kids", "Bottoms", "Joggers", "Elastic Waist Joggers",      "kids jogger pants"),
    ("Kids", "Bottoms", "Shorts",  "Pull-On Shorts",             "kids shorts casual"),
    # Footwear
    ("Kids", "Footwear", "Sneakers", "Velcro Trainers",          "kids sneakers velcro"),
    ("Kids", "Footwear", "Boots",    "Waterproof Rain Boots",    "kids rain boots waterproof"),
    # Accessories
    ("Kids", "Accessories", "Caps",    "Trucker Cap",             "kids cap trucker"),
    ("Kids", "Accessories", "Beanies", "Fun Pom Beanie",          "kids beanie winter"),
    ("Kids", "Accessories", "Socks",   "Colourful Sock 5-Pack",   "kids socks colourful"),
]

# ── Pricing helpers ────────────────────────────────────────────────────────────

PRICE_RANGES = {
    "Tops":                  (25,  65),
    "Hoodies & Sweatshirts": (55,  110),
    "Knitwear":              (70,  140),
    "Outerwear":             (110, 320),
    "Bottoms":               (45,  120),
    "Dresses":               (55,  130),
    "Activewear":            (30,  80),
    "Loungewear":            (55,  90),
    "Footwear":              (60,  180),
    "Accessories":           (15,  60),
}

def _price(dep: str, cat: str, name: str) -> tuple[float, float | None]:
    lo, hi = PRICE_RANGES.get(cat, (40, 120))
    seed = _h(dep + cat + name)
    base = round(lo + (seed % (hi - lo + 1)), 2)
    # ~30 % chance of sale
    sale = None
    if (seed // 100) % 10 < 3:
        pct = 10 + ((seed // 10) % 3) * 5   # 10, 15, or 20 % off
        sale = round(base * (1 - pct / 100), 2)
    return base, sale


# ── Main seed ─────────────────────────────────────────────────────────────────

def seed():
    print(">> Dropping and recreating all tables...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    from datetime import date, timedelta
    today = date.today()

    products_created = 0
    reviews_created  = 0

    with Session(engine) as s:

        for idx, (dep, cat, subcat, name, query) in enumerate(PRODUCTS, start=1):
            price, sale_price = _price(dep, cat, name)
            h = _h(f"{dep}{cat}{subcat}{name}")

            # Colors: pick 2–3
            n_colors = 2 + (h % 2)
            colors = COLOR_PALETTE[(h % len(COLOR_PALETTE)):(h % len(COLOR_PALETTE)) + n_colors]
            if len(colors) < n_colors:
                colors += COLOR_PALETTE[:n_colors - len(colors)]

            # Sizes
            if cat in SIZE_MAP:
                sizes = SIZE_MAP[cat]
            elif subcat in SIZE_MAP:
                sizes = SIZE_MAP[subcat]
            else:
                sizes = SIZE_MAP["default"]

            fit     = _pick(FITS, f"{dep}{cat}{name}fit")
            season  = _pick(SEASONS, f"{dep}{cat}{name}season")
            coll    = _pick(COLLECTIONS, f"{dep}{cat}{name}coll")
            fabric  = FABRICS.get(cat, "Mixed materials")
            stock   = 5 + (h % 50)
            is_new  = (h % 7) == 0
            is_feat = (h % 11) == 0

            # Slug: must be unique
            base_slug = slugify(f"{dep}-{name}")
            slug = base_slug

            # Description
            desc = (
                f"The {name} is a staple for any {dep.lower()}'s wardrobe. "
                f"Cut in a {fit} fit from {fabric.lower()}, "
                f"it's designed for {season.replace('-', ' ')} wear. "
                f"Part of the {coll} collection."
            )

            details = [
                f"Fit: {fit.title()}",
                f"Fabric: {fabric}",
                f"Season: {season.replace('-', ' ').title()}",
                "Model wears size M / UK9 (Footwear)",
            ]

            print(f"  [{idx:03d}/{len(PRODUCTS)}] {dep} › {cat} › {subcat} — {name}")
            img = get_image(query, idx)

            p = Product(
                slug=slug,
                name=name,
                brand="NOVA WEAR",
                department=dep,
                category=cat,
                subcategory=subcat,
                price=price,
                sale_price=sale_price,
                stock=stock,
                description=desc,
                details=details,
                fit=fit,
                fabric=fabric,
                season=season,
                collection=coll,
                care_instructions=CARE,
                sizes=sizes,
                colors=colors,
                images=[img],
                image=img,
                color=colors[0]["hex"],
                is_new=is_new,
                is_featured=is_feat,
                rating=0.0,
                review_count=0,
            )
            s.add(p)
            s.flush()   # get p.id

            # Reviews: 5–8 per product
            n_reviews = 5 + (h % 4)
            all_ratings = []
            for ri in range(n_reviews):
                author, rating, title, body = REVIEWS_POOL[
                    (_h(f"{p.id}{ri}") % len(REVIEWS_POOL))
                ]
                # Stagger dates: up to 90 days ago, deterministic
                days_ago = int(_h(f"{p.id}{ri}date") % 90)
                rv_date = (today - timedelta(days=days_ago)).isoformat()
                s.add(Review(
                    product_id=p.id, author=author, rating=rating,
                    title=title, body=body, date=rv_date,
                ))
                all_ratings.append(rating)
                reviews_created += 1

            p.review_count = len(all_ratings)
            p.rating       = round(sum(all_ratings) / len(all_ratings), 1)
            s.add(p)
            products_created += 1

        # Coupon
        s.add(Coupon(code="SAVE20", percent=20, active=True))
        s.add(Coupon(code="WELCOME10", percent=10, active=True))

        s.commit()

    print()
    print("DONE! Seed complete!")
    print(f"   Products : {products_created}")
    print(f"   Reviews  : {reviews_created}")
    print(f"   Coupons  : SAVE20 (20%), WELCOME10 (10%)")
    print(f"   Images   : {IMG_DIR}")


if __name__ == "__main__":
    seed()
