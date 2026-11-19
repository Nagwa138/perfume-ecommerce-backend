"""
seed_pharmacy_append.py
Appends real pharmacy-brand products to existing DB — does NOT drop any tables.
Adds: La Roche-Posay, Bioderma, NUXE, Vichy (product_type="pharmacy")
"""
import re, random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from models import engine, Product, Review

SEED = 99
rng = random.Random(SEED)

REVIEW_POOL = [
    (5, "Dermatologist recommended", "My derm sent me here and I see why. Skin has never been calmer."),
    (5, "Holy grail SPF", "Finally an SPF I actually enjoy wearing. No white cast, no greasy film."),
    (4, "Very impressive", "Exceeded expectations. Minor point for packaging — formula is flawless."),
    (5, "Perfect for sensitive skin", "Doesn't break me out or cause redness. A staple in my routine."),
    (4, "Grows on you", "At first I wasn't sure, but after a week I was completely won over."),
    (5, "Exceeded expectations", "Ordered on a recommendation and fell in love immediately."),
    (5, "On my third purchase", "Three orders in. That should say everything."),
    (4, "Great compliment getter", "Three different people asked what I was using this week."),
    (5, "Remarkable quality", "Clinical-grade without the clinical smell. Genuinely impressive."),
    (4, "Office staple", "Morning routine — apply, done. No fuss, no shine, great coverage."),
]

REVIEWERS = [
    "Nour Al-Rashid", "Lina Khalil", "Mariam Farouk", "Sara Osman", "Dina Haddad",
    "Yasmine Nassar", "Rania Aziz", "Hana Shafi", "Mona Elwy", "Layla Ibrahim",
    "Omar Fahmy", "Khaled Nasser", "Tarek Mansour", "Amir Saleh", "Yusuf Qasim",
]

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

PHARMACY_CATALOG = [
    # La Roche-Posay
    ("La Roche-Posay Lipikar Baume AP+", "La Roche-Posay", "Moisturiser",
     "Lipid-replenishing balm that soothes atopic eczema-prone skin. Fragrance-free with Shea Butter (20%) and Niacinamide.",
     [(200, 850, 30), (400, 1450, 20)], ["dermatologist-tested", "fragrance-free", "eczema"],
     "Unisex", False, False, None),
    ("La Roche-Posay Anthelios UVmune 400 SPF50+", "La Roche-Posay", "SPF",
     "Ultimate daily protection against UV rays including long UVA. Invisible fluid, non-greasy.",
     [(50, 950, 40)], ["spf", "dermatologist-tested", "invisible"],
     "Unisex", True, True, None),
    ("La Roche-Posay MELA B3 Serum", "La Roche-Posay", "Serum",
     "Anti-hyperpigmentation serum with Melasyl and Niacinamide. Visibly reduces dark spots in 2 weeks.",
     [(30, 1350, 25)], ["anti-aging", "brightening", "dermatologist-tested"],
     "Female", False, False, None),
    ("La Roche-Posay Effaclar Duo+", "La Roche-Posay", "Moisturiser",
     "Anti-acne moisturiser combining Niacinamide and LHA to unclog pores and reduce breakouts.",
     [(40, 750, 35)], ["acne", "pores", "dermatologist-tested"],
     "Unisex", False, False, None),
    # Bioderma
    ("Bioderma Sensibio H2O Micellar Water", "Bioderma", "Cleanser",
     "Iconic micellar water for sensitive skin. Gently cleanses and removes makeup without irritation.",
     [(250, 350, 50), (500, 550, 40)], ["sensitive-skin", "micellar", "fragrance-free"],
     "Female", True, True, None),
    ("Bioderma Atoderm Intensive Baume", "Bioderma", "Moisturiser",
     "Ultra-nourishing balm for very dry and irritated skin. Clinically restores the skin barrier.",
     [(200, 600, 30), (500, 1100, 20)], ["dry-skin", "barrier-repair", "eczema"],
     "Unisex", False, False, None),
    # NUXE
    ("NUXE Huile Prodigieuse", "NUXE", "Oil",
     "Iconic dry oil with 7 precious 100% plant-based oils. Nourishes face, body, and hair.",
     [(50, 1200, 25), (100, 1950, 15)], ["multi-use", "dry-oil", "cult-favorite"],
     "Female", False, True, None),
    ("NUXE Nuxuriance Gold Serum", "NUXE", "Serum",
     "Anti-aging revitalizing serum for dry, fragile skin. Restores radiance from within.",
     [(30, 2200, 12)], ["anti-aging", "luxury", "regenerating"],
     "Female", True, True, None),
]

def slugify_unique(name: str, existing_slugs: set) -> str:
    base = slugify(name)
    slug = base
    n = 1
    while slug in existing_slugs:
        slug = f"{base}-{n}"
        n += 1
    return slug

with Session(engine) as session:
    existing_slugs = set(session.exec(select(Product.slug)).all())
    added: list[Product] = []

    for (name, brand, subcat, desc, sizes_data, tags, gender, is_new, is_featured, sale_price) in PHARMACY_CATALOG:
        sizes = [{"ml": ml, "price": float(price), "stock": stock} for ml, price, stock in sizes_data]
        slug = slugify_unique(name, existing_slugs)
        existing_slugs.add(slug)

        p = Product(
            slug=slug, name=name, brand=brand,
            product_type="pharmacy", subcategory=subcat,
            gender=gender, family="", concentration="",
            top_notes=None, heart_notes=None, base_notes=None,
            sizes=sizes, variants=None, skin_type=None,
            ingredients="", how_to_use="",
            longevity=0, sillage=0,
            season=None, occasion=None,
            bottle_color="#C8A951", cap_style="round",
            description=desc, collection="", year=None, perfumer="",
            images=[f"/products/{slug}.jpg"],
            tags=tags,
            sale_price=sale_price,
            rating=0.0, review_count=0,
            is_new=is_new, is_featured=is_featured, is_active=True,
        )
        session.add(p)
        added.append(p)

    session.commit()
    for p in added:
        session.refresh(p)

    pharmacy_ids = [p.id for p in added]
    print(f"Inserted {len(added)} pharmacy products.")

    # Seed reviews
    rev_total = 0
    for p in added:
        n = rng.randint(4, 7)
        ratings: list[int] = []
        used: set[str] = set()
        for _ in range(n):
            reviewer = rng.choice(REVIEWERS)
            for _ in range(10):
                if reviewer not in used:
                    break
                reviewer = rng.choice(REVIEWERS)
            used.add(reviewer)
            tpl = rng.choice(REVIEW_POOL)
            rating, title, body = tpl
            rv = Review(
                product_id=p.id, author=reviewer, rating=rating,
                title=title, body=body,
                date=(datetime.now() - timedelta(days=rng.randint(1, 365))).date().isoformat(),
            )
            session.add(rv)
            ratings.append(rating)
            rev_total += 1
        p.review_count = len(ratings)
        p.rating = round(sum(ratings) / len(ratings), 1)
        session.add(p)

    session.commit()
    print(f"Seeded {rev_total} reviews for pharmacy products.")

print("Done. DB untouched for existing products.")
