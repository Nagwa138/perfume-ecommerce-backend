"""
seed_v2.py — wipes shop.db and seeds 60 products, ~500 reviews, 80 orders, 2 coupons.
Run:  python seed_v2.py
WARNING: deletes all existing data.
"""
import re, random
from datetime import datetime, timedelta
from sqlmodel import SQLModel, Session, text
from models import engine, Product, Review, Order, OrderItem, Coupon

random.seed(42)

# ── helpers ──────────────────────────────────────────────────────────────────
def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[\s_]+", "-", s).strip("-")

def img(keyword: str, lock: int, w=600, h=760) -> str:
    return f"https://loremflickr.com/{w}/{h}/{keyword}?lock={lock}"

# ── category metadata ─────────────────────────────────────────────────────────
CAT = {
    "Hoodies":     ("hoodie streetwear",  ["XS","S","M","L","XL","XXL"], "80% Cotton, 20% Polyester Fleece",
                    ["Relaxed fit","Kangaroo pocket","Ribbed cuffs and hem","Brushed fleece lining"]),
    "T-Shirts":    ("tshirt fashion",     ["XS","S","M","L","XL","XXL"], "100% Ring-Spun Cotton",
                    ["Crew neck","Pre-shrunk","Side-seamed","Double-needle hem"]),
    "Jackets":     ("jacket streetwear",  ["XS","S","M","L","XL","XXL"], "Shell: 100% Nylon  |  Lining: 100% Polyester",
                    ["YKK zippers","Interior media pocket","Adjustable hem","Water-resistant DWR coating"]),
    "Pants":       ("streetwear trousers",["28","30","32","34","36","38"], "98% Cotton, 2% Elastane",
                    ["Elasticated waistband","Zippered side pockets","Tapered leg","Reinforced belt loops"]),
    "Sneakers":    ("sneakers shoes",     ["US 7","US 8","US 9","US 10","US 11","US 12"],
                    "Upper: Canvas/Leather  |  Sole: Vulcanised Rubber",
                    ["Padded ankle collar","Cushioned insole","Reinforced toe cap","Non-marking outsole"]),
    "Accessories": ("fashion accessories",["One Size"], "Premium mixed materials",
                    ["Adjustable fitting","Premium hardware","Quality construction"]),
}

# ── compact catalog: (name, cat, price, sale_price, stock, is_new, is_featured, colors, desc) ──
CATALOG = [
    # HOODIES
    ("Classic Zip Hoodie","Hoodies",89,None,24,False,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Ash Gray","hex":"#a8a8a8"},{"name":"Navy","hex":"#1e3a5f"}],
     "A timeless zip-up cut from heavyweight French terry."),
    ("Oversized Pullover Hoodie","Hoodies",95,None,18,True,False,
     [{"name":"Stone","hex":"#c2b9a7"},{"name":"Olive","hex":"#4a4a2a"},{"name":"Ecru","hex":"#f5f0e8"}],
     "Relaxed drop-shoulder silhouette with a kangaroo pocket."),
    ("Tech Fleece Hoodie","Hoodies",129,99,12,False,True,
     [{"name":"Charcoal","hex":"#2a2a2a"},{"name":"Black","hex":"#1a1a1a"}],
     "Engineered fleece that regulates temperature without bulk."),
    ("Vintage Wash Hoodie","Hoodies",85,None,20,True,False,
     [{"name":"Faded Blue","hex":"#4a6a9a"},{"name":"Faded Black","hex":"#3a3a3a"},{"name":"Rust","hex":"#8b4513"}],
     "Garment-dyed for a lived-in look that only gets better."),
    ("Essential Slim Hoodie","Hoodies",75,59,30,False,False,
     [{"name":"White","hex":"#f5f5f5"},{"name":"Black","hex":"#1a1a1a"},{"name":"Heather Gray","hex":"#9a9a9a"}],
     "Slim-cut everyday hoodie in a medium-weight cotton blend."),
    ("Heavyweight Crop Hoodie","Hoodies",79,None,14,True,False,
     [{"name":"Cream","hex":"#f0ead6"},{"name":"Pink","hex":"#e8a0b0"},{"name":"Sage","hex":"#7a9a7a"}],
     "Cropped boxy cut, heavyweight fleece, ribbed hem."),
    ("Performance Half-Zip","Hoodies",110,None,16,False,True,
     [{"name":"Deep Navy","hex":"#162040"},{"name":"Forest","hex":"#1e3a2a"}],
     "Moisture-wicking four-way stretch with a half-zip placket."),
    ("Relaxed Logo Hoodie","Hoodies",85,None,22,False,False,
     [{"name":"Mushroom","hex":"#b5a898"},{"name":"Faded Black","hex":"#3a3a3a"}],
     "Embroidered logo on a relaxed-fit heavyweight pullover."),
    ("Quilted Hoodie","Hoodies",99,79,10,False,False,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Navy","hex":"#1e3a5f"},{"name":"Olive","hex":"#4a4a2a"}],
     "Lightweight quilted construction with an interior storm placket."),
    ("Gradient Tie-Dye Hoodie","Hoodies",95,None,8,True,True,
     [{"name":"Sunset","hex":"#e05020"},{"name":"Ocean","hex":"#204080"}],
     "Hand-dyed gradient — no two are exactly the same."),
    # T-SHIRTS
    ("Essential Tee","T-Shirts",35,None,50,False,True,
     [{"name":"White","hex":"#f5f5f5"},{"name":"Black","hex":"#1a1a1a"},{"name":"Slate","hex":"#6a7a8a"},{"name":"Navy","hex":"#1e3a5f"}],
     "180gsm Pima cotton. The only tee you need."),
    ("Oversized Graphic Tee","T-Shirts",45,None,35,True,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"White","hex":"#f5f5f5"}],
     "Drop-shoulder with an archival screen print."),
    ("Premium Cotton Tee","T-Shirts",55,None,28,False,False,
     [{"name":"Ecru","hex":"#f5f0e8"},{"name":"Mist","hex":"#c8d0d8"},{"name":"Black","hex":"#1a1a1a"}],
     "220gsm ring-spun cotton with a slight boxy cut."),
    ("Cropped Pocket Tee","T-Shirts",40,29,25,False,False,
     [{"name":"White","hex":"#f5f5f5"},{"name":"Sage","hex":"#7a9a7a"},{"name":"Peach","hex":"#e8b090"}],
     "Relaxed crop with a utility chest pocket."),
    ("Long Sleeve Tee","T-Shirts",50,None,22,False,False,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Oatmeal","hex":"#d4c8b0"},{"name":"Burgundy","hex":"#5a1a2a"}],
     "Lightweight long-sleeve in a slim athletic fit."),
    ("Striped Tee","T-Shirts",45,None,20,True,False,
     [{"name":"Navy/White","hex":"#1e3a5f"},{"name":"Black/White","hex":"#1a1a1a"}],
     "Classic breton stripes in a relaxed cut."),
    ("Logo Tee","T-Shirts",39,None,40,False,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"White","hex":"#f5f5f5"},{"name":"Forest","hex":"#1e3a2a"}],
     "Minimal rubberized logo on a classic crew neck."),
    ("V-Neck Tee","T-Shirts",38,29,18,False,False,
     [{"name":"White","hex":"#f5f5f5"},{"name":"Black","hex":"#1a1a1a"},{"name":"Gray","hex":"#8a8a8a"}],
     "Slim-fit V-neck in a soft cotton-modal blend."),
    ("Mesh Panel Tee","T-Shirts",55,None,14,True,False,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"White","hex":"#f5f5f5"}],
     "Contrast mesh panels for ventilation and visual interest."),
    ("Vintage Wash Tee","T-Shirts",42,None,24,False,False,
     [{"name":"Faded Black","hex":"#3a3a3a"},{"name":"Faded Blue","hex":"#4a6a9a"},{"name":"Dusty Rose","hex":"#c0808a"}],
     "Garment-dyed for a soft, broken-in feel."),
    # JACKETS
    ("Coach Jacket","Jackets",149,None,15,False,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Navy","hex":"#1e3a5f"},{"name":"Forest","hex":"#1e3a2a"}],
     "Lightweight woven shell with snap buttons and an inner mesh lining."),
    ("Bomber Jacket","Jackets",189,149,10,False,True,
     [{"name":"Olive","hex":"#4a4a2a"},{"name":"Black","hex":"#1a1a1a"},{"name":"Tan","hex":"#c8a870"}],
     "MA-1 silhouette in a water-resistant ripstop nylon."),
    ("Track Jacket","Jackets",119,None,20,True,False,
     [{"name":"Black/Gold","hex":"#1a1a1a"},{"name":"Navy/White","hex":"#1e3a5f"}],
     "Retro-inspired with contrast tape and zip pockets."),
    ("Utility Jacket","Jackets",199,None,8,False,True,
     [{"name":"Olive","hex":"#4a4a2a"},{"name":"Black","hex":"#1a1a1a"}],
     "Multi-pocket utility in a heavy canvas."),
    ("Denim Jacket","Jackets",139,109,12,False,False,
     [{"name":"Mid Wash","hex":"#5a7090"},{"name":"Black Wash","hex":"#2a2a3a"},{"name":"Light Wash","hex":"#8aa0c0"}],
     "Classic trucker cut in a rigid 12oz denim."),
    ("Windbreaker","Jackets",109,None,18,True,False,
     [{"name":"Cobalt","hex":"#1848c8"},{"name":"Orange","hex":"#d05010"},{"name":"Black","hex":"#1a1a1a"}],
     "Packable anorak with DWR coating and stowaway hood."),
    ("Puffer Jacket","Jackets",229,179,10,False,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Ecru","hex":"#f5f0e8"},{"name":"Forest","hex":"#1e3a2a"}],
     "900-fill RDS down in a boxy channel-quilt silhouette."),
    ("Leather Look Jacket","Jackets",249,None,6,True,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Tan","hex":"#c8a870"}],
     "Vegan leather moto jacket with YKK zippers and biker hardware."),
    ("Sherpa Jacket","Jackets",159,129,14,False,False,
     [{"name":"Cream","hex":"#f0ead6"},{"name":"Caramel","hex":"#b07840"}],
     "Double-sided sherpa fleece with a snap placket."),
    ("Quilted Jacket","Jackets",169,None,10,False,False,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Khaki","hex":"#a0906a"},{"name":"Navy","hex":"#1e3a5f"}],
     "Diamond-quilted liner jacket in a midweight nylon shell."),
    # PANTS
    ("Slim Fit Joggers","Pants",69,None,30,False,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Charcoal","hex":"#2a2a2a"},{"name":"Navy","hex":"#1e3a5f"}],
     "Tapered leg, elasticated waist, zippered pockets."),
    ("Wide-Leg Trousers","Pants",89,None,20,True,True,
     [{"name":"Stone","hex":"#c2b9a7"},{"name":"Black","hex":"#1a1a1a"},{"name":"Ecru","hex":"#f5f0e8"}],
     "Fluid wide-leg cut in a lightweight twill."),
    ("Cargo Pants","Pants",99,None,22,True,False,
     [{"name":"Olive","hex":"#4a4a2a"},{"name":"Black","hex":"#1a1a1a"},{"name":"Khaki","hex":"#a0906a"}],
     "Six-pocket cargo in a cotton-ripstop canvas."),
    ("Track Pants","Pants",75,59,25,False,False,
     [{"name":"Black/White","hex":"#1a1a1a"},{"name":"Navy/White","hex":"#1e3a5f"}],
     "Retro track pants with contrast side stripes."),
    ("Relaxed Fit Jeans","Pants",109,None,18,False,True,
     [{"name":"Mid Wash","hex":"#5a7090"},{"name":"Rinse Wash","hex":"#2a3a4a"},{"name":"Bleach Wash","hex":"#90a0c0"}],
     "90s-inspired relaxed cut in a Japanese selvedge denim."),
    ("Straight-Leg Denim","Pants",119,89,15,False,False,
     [{"name":"Black Wash","hex":"#2a2a3a"},{"name":"Mid Wash","hex":"#5a7090"}],
     "Classic 5-pocket straight in an 11oz stretch denim."),
    ("Sweatpants","Pants",65,None,35,False,False,
     [{"name":"Gray Marl","hex":"#9a9a9a"},{"name":"Black","hex":"#1a1a1a"},{"name":"Navy","hex":"#1e3a5f"}],
     "French terry with a brushed inner and ribbed cuff."),
    ("Nylon Shorts","Pants",55,39,28,True,False,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Olive","hex":"#4a4a2a"},{"name":"Cobalt","hex":"#1848c8"}],
     "4-inch inseam nylon shorts with a mesh liner."),
    ("Linen Pants","Pants",85,None,16,False,False,
     [{"name":"Ecru","hex":"#f5f0e8"},{"name":"Stone","hex":"#c2b9a7"},{"name":"Sage","hex":"#7a9a7a"}],
     "Loose wide-cut linen trousers, perfect for warm days."),
    ("Tech Pants","Pants",129,99,12,True,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Charcoal","hex":"#2a2a2a"}],
     "Four-way stretch with articulated knees and zippered thigh pockets."),
    # SNEAKERS
    ("Classic Low-Top","Sneakers",95,None,20,False,True,
     [{"name":"White/White","hex":"#f5f5f5"},{"name":"Black/Black","hex":"#1a1a1a"},{"name":"White/Navy","hex":"#eef0f8"}],
     "Vulcanised canvas low-top — the shoe that started it all."),
    ("High-Top Street Sneaker","Sneakers",129,None,14,True,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"White","hex":"#f5f5f5"},{"name":"Olive","hex":"#4a4a2a"}],
     "High ankle collar with a chunky EVA cupsole."),
    ("Chunky Platform Sneaker","Sneakers",149,119,10,False,True,
     [{"name":"Triple White","hex":"#f5f5f5"},{"name":"Triple Black","hex":"#1a1a1a"}],
     "2-inch platform sole with exaggerated proportions."),
    ("Running Silhouette","Sneakers",119,None,18,True,False,
     [{"name":"White/Gray","hex":"#f0f0f0"},{"name":"Black/Neon","hex":"#1a1a1a"},{"name":"Cobalt/White","hex":"#1848c8"}],
     "Retro running aesthetic with a modern cushioned midsole."),
    ("Canvas Slip-On","Sneakers",65,49,24,False,False,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Ecru","hex":"#f5f0e8"},{"name":"Navy","hex":"#1e3a5f"}],
     "Elasticated canvas slip-on with a padded collar."),
    ("Leather Minimal Sneaker","Sneakers",155,None,12,False,True,
     [{"name":"White","hex":"#f5f5f5"},{"name":"Black","hex":"#1a1a1a"},{"name":"Tan","hex":"#c8a870"}],
     "Clean leather upper with a cup sole and minimal branding."),
    ("Retro Basketball Shoe","Sneakers",139,109,10,False,False,
     [{"name":"White/Red","hex":"#f5f5f5"},{"name":"Black/Gold","hex":"#1a1a1a"},{"name":"Navy/White","hex":"#1e3a5f"}],
     "80s basketball DNA with modern fit and cushioning."),
    ("Mesh Trainer","Sneakers",99,None,20,True,False,
     [{"name":"White/Gray","hex":"#f0f0f0"},{"name":"Black/White","hex":"#1a1a1a"}],
     "Engineered mesh upper for breathability with a padded tongue."),
    ("Suede Casual","Sneakers",125,None,15,False,False,
     [{"name":"Tan","hex":"#c8a870"},{"name":"Forest","hex":"#1e3a2a"},{"name":"Rust","hex":"#8b4513"}],
     "Premium nubuck upper on a classic vulcanised sole."),
    ("Limited Edition Collab","Sneakers",219,None,5,True,True,
     [{"name":"Special Edition","hex":"#c084fc"}],
     "A limited drop with an artist collective — only 100 pairs."),
    # ACCESSORIES
    ("Embroidered Bucket Hat","Accessories",39,None,30,False,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Khaki","hex":"#a0906a"},{"name":"Navy","hex":"#1e3a5f"}],
     "Structured bucket hat with tonal embroidery on the crown."),
    ("Ribbed Beanie","Accessories",29,None,40,False,False,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Gray Marl","hex":"#9a9a9a"},{"name":"Cream","hex":"#f0ead6"}],
     "Fine-knit ribbed beanie with a subtle cuffed turn-up."),
    ("NOVA Dad Cap","Accessories",35,None,35,True,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"White","hex":"#f5f5f5"},{"name":"Washed Green","hex":"#5a7a5a"}],
     "Unstructured six-panel cap with a tonal embroidered logo."),
    ("Canvas Tote Bag","Accessories",45,None,25,False,False,
     [{"name":"Natural","hex":"#d4c8a0"},{"name":"Black","hex":"#1a1a1a"}],
     "12oz canvas with long handles and an internal slip pocket."),
    ("Crossbody Bag","Accessories",69,55,15,True,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Tan","hex":"#c8a870"}],
     "Compact crossbody in water-resistant ripstop with adjustable strap."),
    ("Chain Necklace","Accessories",49,None,20,False,False,
     [{"name":"Gold","hex":"#c8a000"},{"name":"Silver","hex":"#c0c0c0"},{"name":"Black","hex":"#1a1a1a"}],
     "Cuban-link chain in PVD-coated stainless steel."),
    ("Stacked Bracelet Set","Accessories",35,25,25,True,False,
     [{"name":"Gold Mix","hex":"#c8a000"},{"name":"Silver Mix","hex":"#c0c0c0"}],
     "Three stackable bracelets in mixed materials."),
    ("Waist Bag","Accessories",55,None,18,False,True,
     [{"name":"Black","hex":"#1a1a1a"},{"name":"Olive","hex":"#4a4a2a"}],
     "Minimal waist bag with two zippered compartments."),
    ("Knit Scarf","Accessories",45,35,20,False,False,
     [{"name":"Cream","hex":"#f0ead6"},{"name":"Charcoal","hex":"#2a2a2a"},{"name":"Rust","hex":"#8b4513"}],
     "Oversized ribbed knit in a lambswool blend."),
    ("Shield Sunglasses","Accessories",59,None,22,True,True,
     [{"name":"Black/Black","hex":"#1a1a1a"},{"name":"Tortoise/Brown","hex":"#704214"},{"name":"Gold/Green","hex":"#c8a000"}],
     "Oversized shield frames with UV400 polycarbonate lenses."),
]

# ── review pool ───────────────────────────────────────────────────────────────
REVIEWS = [
    (5,"Perfect fit","Exactly what I expected. Great quality and fast shipping."),
    (5,"Love this piece","The fabric feels premium. Definitely buying again."),
    (5,"Exceeded expectations","Better in person than in photos. Worth every penny."),
    (4,"Really good","Great quality, runs slightly large but still a solid 4 stars."),
    (4,"Solid quality","Good construction. Sizing was accurate for me."),
    (4,"Great value","Quality feels more expensive than the price point."),
    (3,"Good but not great","Quality is average for the price. Decent though."),
    (5,"LOVE IT","Bought two colours already. The fit is incredible."),
    (5,"Must buy","Best thing I ordered this year. Highly recommend."),
    (4,"Very happy","Arrived quickly, nice packaging. Great product."),
    (5,"Perfect","Exactly as described. The colour in person is stunning."),
    (5,"10/10","Honestly this is the best purchase I made all year."),
    (4,"Good stuff","Well made and stylish. Would recommend."),
    (5,"Absolutely love","My go-to piece now. Already got compliments."),
    (4,"Worth it","Pricey but you get what you pay for."),
    (3,"Average","Nothing special but does the job. Shipping was fast."),
    (5,"Fire","This goes with everything in my wardrobe."),
    (4,"Nice quality","Really happy with this. Fast delivery too."),
    (5,"Obsessed","Wore it twice already the week it arrived."),
    (3,"Decent","It's ok. Expected slightly better for the price."),
]

AUTHORS = [
    "Alex M.","Jamie K.","Morgan T.","Riley P.","Taylor S.",
    "Jordan B.","Casey H.","Avery R.","Quinn D.","Sam L.",
    "Drew W.","Peyton N.","Blake E.","Cameron F.","Logan C.",
    "Mason A.","Harper J.","Skyler V.","Reese G.","Finley O.",
    "Charlie B.","Emery T.","Rowan S.","Sage P.","Kai L.",
]

CUSTOMER_NAMES = [
    "Emma Johnson","Liam Smith","Olivia Williams","Noah Brown","Ava Davis",
    "William Miller","Sophia Wilson","James Moore","Isabella Taylor","Oliver Anderson",
    "Mia Thomas","Elijah Jackson","Charlotte Harris","Lucas Martin","Amelia Garcia",
    "Mason Martinez","Harper Robinson","Ethan Clark","Evelyn Rodriguez","Aiden Lewis",
]

STATUSES = ["pending","paid","shipped","delivered","delivered","delivered","cancelled"]

def run():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print("Tables reset.")

    with Session(engine) as s:
        # ── products ─────────────────────────────────────────────────────────
        products: list[Product] = []
        slug_seen: set[str] = set()
        for idx, row in enumerate(CATALOG):
            name, cat, price, sale_price, stock, is_new, is_featured, colors, desc = row
            meta_kw, sizes, materials, details = CAT[cat]
            base_slug = slugify(name)
            sl = base_slug
            n = 2
            while sl in slug_seen:
                sl = f"{base_slug}-{n}"; n += 1
            slug_seen.add(sl)
            kw = meta_kw.split()[0]
            images = [img(kw, idx * 10 + i) for i in range(4)]
            p = Product(
                slug=sl, name=name, brand="NOVA WEAR", category=cat,
                price=float(price), sale_price=float(sale_price) if sale_price else None,
                stock=stock, description=desc, details=details, materials=materials,
                sizes=sizes, colors=colors, images=images, tags=[cat.lower(), kw],
                rating=0.0, review_count=0, is_new=is_new, is_featured=is_featured,
                image=images[0], color=colors[0]["hex"],
            )
            s.add(p); products.append(p)
        s.commit()
        for p in products:
            s.refresh(p)
        print(f"  {len(products)} products inserted.")

        # ── reviews ───────────────────────────────────────────────────────────
        base_date = datetime.now()
        total_reviews = 0
        for p in products:
            count = random.randint(5, 15)
            ratings = []
            for i in range(count):
                rv_rating, rv_title, rv_body = random.choice(REVIEWS)
                days_ago = random.randint(1, 180)
                rv = Review(
                    product_id=p.id,
                    author=random.choice(AUTHORS),
                    rating=rv_rating,
                    title=rv_title,
                    body=rv_body,
                    date=(base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
                )
                s.add(rv)
                ratings.append(rv_rating)
            p.review_count = count
            p.rating = round(sum(ratings) / count, 1)
            s.add(p)
            total_reviews += count
        s.commit()
        print(f"  {total_reviews} reviews inserted.")

        # ── orders ────────────────────────────────────────────────────────────
        for i in range(80):
            days_ago = random.randint(0, 90)
            created = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S")
            cname = random.choice(CUSTOMER_NAMES)
            email = cname.lower().replace(" ", ".") + "@example.com"
            status = random.choice(STATUSES)
            n_items = random.randint(1, 4)
            chosen = random.sample(products, min(n_items, len(products)))
            subtotal = 0.0
            o = Order(
                status=status, customer_name=cname, customer_email=email,
                subtotal=0.0, shipping=5.99, discount=0.0, total=0.0,
                created_at=created,
            )
            s.add(o); s.flush()
            for prod in chosen:
                qty = random.randint(1, 3)
                line_price = float(prod.sale_price or prod.price)
                s.add(OrderItem(
                    order_id=o.id, product_id=prod.id,
                    product_name=prod.name, qty=qty, price=line_price,
                ))
                subtotal += line_price * qty
            o.subtotal = round(subtotal, 2)
            o.total = round(subtotal + 5.99, 2)
            s.add(o)
        s.commit()
        print("  80 orders inserted.")

        # ── coupons ───────────────────────────────────────────────────────────
        s.add(Coupon(code="WELCOME10", percent=10, active=True))
        s.add(Coupon(code="NOVA20",    percent=20, active=True))
        s.commit()
        print("  Coupons WELCOME10 (10%) and NOVA20 (20%) inserted.")

    print("\nDone. seed_v2 complete.")

if __name__ == "__main__":
    confirm = input("This will WIPE shop.db. Type YES to continue: ")
    if confirm.strip() == "YES":
        run()
    else:
        print("Aborted.")
