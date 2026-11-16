"""
seed_pharmacy_addon.py
Seeds real skincare, pharmacy, and haircare products from premium brands.
Brands included: La Roche-Posay, Bioderma, NUXE, L'Oréal Elvive.
"""
import re
import random
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlmodel import Session, SQLModel, select
from models import engine, Product, ProductVariant, Review, Order, OrderItem, Coupon

SEED = 42
rng = random.Random(SEED)

print("=" * 60)
print("  HOSSAM Beauty — Real Pharmacy & Cosmetic Seed")
print("  Drops & re-seeds: product, review, order_item, orders")
print("=" * 60)
confirm = input("  Type YES to continue: ").strip()
if confirm != "YES":
    print("Aborted.")
    raise SystemExit(0)

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

# ── Review Pool ───────────────────────────────────────────────────────────────
REVIEW_POOL = [
    (5, "Holy grail", "My dermatologist recommended this and I see why. My skin has never been calmer."),
    (5, "Worth every penny", "Expensive but completely justifies the price. Noticeable results within two weeks."),
    (4, "Very impressive", "Exceeded my expectations. Minor point deducted for packaging, but the formula is flawless."),
    (4, "Sophisticated and effective", "Luxurious feel, beautiful results. The scent is delicate and not overwhelming."),
    (5, "Perfect for sensitive skin", "Finally something that doesn't break me out or cause redness. A staple in my routine."),
    (4, "Grows on you", "At first I wasn't sure, but after a week I was completely won over."),
    (5, "Exceeded expectations", "Ordered based on a recommendation and fell in love immediately."),
    (5, "Sensational", "Applied once and immediately felt the difference. The quality is unmistakable."),
    (4, "Great for the whole family", "Bought one for me, one for my mum. Both of us are sold."),
    (5, "On my third purchase", "Three orders in. That should say everything."),
]

# ── Catalog: Real Products ────────────────────────────────────────────────────
# (name, brand, product_type, subcategory, description, sizes [(ml, price, stock)], tags)
CATALOG = [
    # ═══════════ LA ROCHE-POSAY ═══════════
    ("La Roche-Posay Lipikar Baume AP+", "La Roche-Posay", "skincare", "Moisturiser",
     "Lipid-replenishing balm that soothes atopic eczema-prone skin. Fragrance-free with Shea Butter (20%) and Niacinamide.",
     [(200, 850, 30), (400, 1450, 20)], ["dermatologist-tested", "fragrance-free", "eczema"]),
    
    ("La Roche-Posay Lipikar Syndet AP+", "La Roche-Posay", "skincare", "Cleanser",
     "Cleansing cream for atopic eczema-prone skin. Helps reduce severe dryness starting in the shower.",
     [(200, 450, 35), (400, 750, 25)], ["dermatologist-tested", "fragrance-free", "eczema"]),
    
    ("La Roche-Posay Anthelios UVmune 400 SPF50+", "La Roche-Posay", "skincare", "SPF",
     "Ultimate daily protection against UV rays, including long UVA. Invisible fluid, non-greasy.",
     [(50, 950, 40)], ["spf", "dermatologist-tested", "invisible"]),
    
    ("La Roche-Posay MELA B3 Serum", "La Roche-Posay", "skincare", "Serum",
     "Anti-hyperpigmentation serum with Melasyl and Niacinamide. Visibly reduces dark spots.",
     [(30, 1350, 25)], ["anti-aging", "brightening", "dermatologist-tested"]),

    # ═══════════ BIODERMA ═══════════
    ("Bioderma Sensibio H2O Micellar Water", "Bioderma", "skincare", "Cleanser",
     "Iconic micellar water for sensitive skin. Gently cleanses and removes makeup without irritation.",
     [(250, 350, 50), (500, 550, 40)], ["sensitive-skin", "micellar", "fragrance-free"]),
    
    ("Bioderma Atoderm Intensive Baume", "Bioderma", "skincare", "Moisturiser",
     "Ultra-nourishing balm for very dry, irritated skin. Restores the skin barrier.",
     [(200, 600, 30), (500, 1100, 20)], ["dry-skin", "barrier-repair", "eczema"]),
    
    ("Bioderma Sebium Gel Moussant", "Bioderma", "skincare", "Cleanser",
     "Purifying cleansing gel for combination to oily skin. Limits sebum secretion.",
     [(200, 320, 40)], ["oily-skin", "purifying", "daily-care"]),

    # ═══════════ NUXE ═══════════
    ("NUXE Huile Prodigieuse", "NUXE", "skincare", "Oil",
     "Iconic dry oil with 7 precious 100% plant-based oils. Nourishes, repairs, and beautifies face, body, and hair.",
     [(50, 1200, 25), (100, 1950, 15)], ["multi-use", "dry-oil", "cult-favorite"]),
    
    ("NUXE Rêve de Miel Face Cleansing Gel", "NUXE", "skincare", "Cleanser",
     "Gentle face cleansing gel with Honey and Sunflower. Cleanses without drying.",
     [(200, 650, 20)], ["gentle", "honey", "hydrating"]),
    
    ("NUXE Nuxuriance Gold Serum", "NUXE", "skincare", "Serum",
     "Anti-aging serum for dry, fragile skin (from age 60). Revitalizes and restores radiance.",
     [(30, 2200, 12)], ["anti-aging", "luxury", "regenerating"]),

    # ═══════════ L'ORÉAL ELVIVE ═══════════
    ("L'Oréal Elvive Hydra Hyaluronic Shampoo", "L'Oréal Paris", "haircare", "Shampoo",
     "Moisture-boosting shampoo with Hyaluronic Acid for 72h hydration. For dry, dehydrated hair.",
     [(400, 350, 45)], ["hydrating", "drugstore", "hyaluronic-acid"]),
    
    ("L'Oréal Elvive Dream Lengths Shampoo", "L'Oréal Paris", "haircare", "Shampoo",
     "Restoring shampoo for long, damaged hair. Helps seal split ends.",
     [(400, 350, 50)], ["repairing", "split-ends", "drugstore"]),
    
    ("L'Oréal Elvive Extraordinary Oil Shampoo", "L'Oréal Paris", "haircare", "Shampoo",
     "Nourishing shampoo for dry hair. Infused with 6 precious flower oils.",
     [(400, 350, 40)], ["nourishing", "oils", "drugstore"]),
    
    ("L'Oréal Elvive Color Protect Shampoo", "L'Oréal Paris", "haircare", "Shampoo",
     "Protects and maintains hair color for up to 10 weeks. For colored hair.",
     [(400, 350, 35)], ["color-protect", "drugstore"]),
    
    ("L'Oréal Elvive Bond Repair Leave-In Serum", "L'Oréal Paris", "haircare", "Hair Serum",
     "Repairs and strengthens the hair fiber from within. For damaged, bond-broken hair.",
     [(150, 450, 25)], ["bond-repair", "leave-in", "drugstore"]),
]

# ── Drop & recreate tables ────────────────────────────────────────────────────
print("\nDropping tables...")
with engine.connect() as conn:
    conn.execute(text("PRAGMA foreign_keys = OFF"))
    for tbl in ("order_item", "orders", "review", "product_variant", "product"):
        conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
    conn.execute(text("PRAGMA foreign_keys = ON"))
    conn.commit()

SQLModel.metadata.create_all(engine)
print("Tables recreated.")

# ── Seed Products ─────────────────────────────────────────────────────────────
print("Seeding real products...")
products: list[Product] = []

with Session(engine) as session:
    for idx, row in enumerate(CATALOG):
        (name, brand, ptype, subcat, desc, sizes_data, tags) = row
        slug = slugify(name)
        
        # Format sizes for the JSON field
        sizes = [{"ml": ml, "price": float(price), "stock": stock} for ml, price, stock in sizes_data]
        base_price = float(sizes_data[0][1]) if sizes_data else 0.0

        p = Product(
            slug=slug, name=name, brand=brand,
            product_type=ptype, subcategory=subcat,
            description=desc,
            sizes=sizes,
            tags=tags,
            is_new=rng.random() > 0.8,
            is_featured=rng.random() > 0.7,
            is_active=True,
            images=[f"/products/{slug}.jpg"], # Path for the image script
            rating=0.0, review_count=0,
            price=base_price # Added for compatibility with some views
        )
        session.add(p)
        products.append(p)

    session.commit()
    for p in products:
        session.refresh(p)

print(f"  {len(products)} real products inserted.")

# ── Reviews ───────────────────────────────────────────────────────────────────
print("Seeding reviews...")
review_total = 0
with Session(engine) as session:
    for p in products:
        n = rng.randint(3, 6)
        ratings = []
        for _ in range(n):
            tpl = rng.choice(REVIEW_POOL)
            rating, title, body = tpl
            rv = Review(
                product_id=p.id, author=rng.choice(["Verified Buyer", "A. Hassan", "S. Kamal", "M. Adel"]),
                rating=rating, title=title, body=body,
                date=(datetime.now() - timedelta(days=rng.randint(1, 365))).date().isoformat(),
            )
            session.add(rv)
            ratings.append(rating)
            review_total += 1

        p.review_count = len(ratings)
        p.rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0
        session.add(p)

    session.commit()
print(f"  {review_total} reviews inserted.")
print("\nSeed complete.")