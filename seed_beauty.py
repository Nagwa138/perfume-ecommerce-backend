"""
seed_beauty.py
Deterministic seed for AURA Beauty Store.
Covers: fragrance · skincare · makeup · haircare · body (≈ 90 products).
Drops ONLY: product, review, order_item, orders tables.
NEVER touches: admin_user, audit_log, settings.

Run after approval:  python seed_beauty.py   (from backend/)
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
print("  AURA Beauty Store — Seed Script")
print("  Drops & re-seeds: product, review, orders, order_item")
print("  NOT touched:      admin_user, audit_log, settings, coupons")
print("=" * 60)
confirm = input("  Type YES to continue: ").strip()
if confirm != "YES":
    print("Aborted.")
    raise SystemExit(0)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ── Review copy ───────────────────────────────────────────────────────────────
REVIEW_POOL = [
    (5, "Absolutely love this", "My new holy grail. I've already repurchased twice. The texture, the scent, the results — everything is perfect."),
    (5, "Worth every penny", "Expensive but completely justifies the price. Noticeable results within two weeks of consistent use."),
    (5, "Game changer", "I've tried so many products in this category and nothing compares. This is the one."),
    (4, "Very impressive", "Exceeded my expectations. Minor point deducted only because the packaging could be more elegant — the formula itself is flawless."),
    (4, "Sophisticated and effective", "Luxurious feel, beautiful results. The scent is delicate and not overwhelming. Highly recommend."),
    (5, "Perfect gift", "Bought this as a gift and ended up keeping it for myself. Had to order another. No regrets."),
    (4, "Grows on you", "At first I wasn't sure, but after a week I was completely won over. Patience is rewarded here."),
    (3, "Good but not exceptional", "Solid product at a high price point. Does what it promises, nothing more. Might suit others better."),
    (5, "Exceeded expectations", "Ordered based on a recommendation and fell in love immediately. Already planning my next purchase."),
    (4, "Quiet luxury", "Understated, effortlessly refined. The kind of product that makes you feel cared for without shouting about it."),
    (5, "Sensational", "Applied once and immediately felt the difference. The quality is unmistakable."),
    (3, "Fades too quickly", "The initial experience is beautiful but doesn't last as long as I'd hoped for the price."),
    (5, "On my third purchase", "Three orders in. That should say everything."),
    (4, "Great compliment getter", "Three different people asked what I was using this week. Worth it for that alone."),
    (5, "Luxurious and unique", "Unlike anything else in my routine. The packaging is a work of art too."),
    (4, "Very wearable", "Perfect for daily use. Not too heavy, not too intense — just right."),
    (5, "Remarkable quality", "You enter a room and people notice. Effortless without being aggressive. Bravo."),
    (3, "Needs more time", "Still in my testing phase. The first impression is good but I want to see long-term results."),
    (4, "Office-appropriate luxury", "Sophisticated enough for important meetings, but not so heavy it bothers colleagues."),
    (5, "Instant favourite", "Bought this on a whim and it's now my most-used product. Brilliant."),
    (5, "Addictive texture", "There's a sensory quality to this that keeps me reaching for it every morning."),
    (4, "Interesting but complex", "Takes a moment to fully appreciate. Once you do, you won't want anything else."),
    (5, "Confident and sophisticated", "This is what self-care feels like done right."),
    (4, "Classy and understated", "Not a showoff product, which is exactly what I wanted. Refined, effective, beautifully made."),
    (5, "Beautifully formulated", "Every detail — from the first application to the finish — speaks of exceptional craftsmanship."),
]

REVIEWERS = [
    "Amira K.", "Sophie L.", "Mohammed A.", "Elena P.", "James T.",
    "Nour H.", "Charlotte B.", "Omar S.", "Isabella M.", "Rania F.",
    "Thomas W.", "Yasmine Z.", "Lucas D.", "Hana R.", "Ethan C.",
    "Fatima A.", "Marcus B.", "Leila V.", "Daniel G.", "Sara N.",
    "Alexander H.", "Mia J.", "Tariq M.", "Claire D.", "Noah E.",
    "Lena S.", "Carlos R.", "Zara P.", "Victor L.", "Aisha O.",
    "Pierre D.", "Nadia K.", "David R.", "Yuna C.", "Felix M.",
]

CUSTOMERS = [
    ("Layla Hassan",    "layla.h@email.com",    "+20 100 123 4567", "12 Al Nozha St, Cairo"),
    ("James Carter",    "j.carter@email.com",   "+44 7700 900001",  "8 Montague Pl, London"),
    ("Sophie Dubois",   "sophie.d@email.com",   "+33 6 12 34 56 78","17 Rue Rivoli, Paris"),
    ("Omar Al-Farsi",   "omar.f@email.com",     "+971 50 123 4567", "Al Wasl Rd, Dubai"),
    ("Isabella Rossi",  "i.rossi@email.com",    "+39 02 1234 5678",  "Via Roma 5, Milan"),
    ("Ahmed Sami",      "a.sami@email.com",     "+20 111 234 5678", "45 Tahrir Sq, Cairo"),
    ("Elena Petrova",   "elena.p@email.com",    "+7 495 123 4567",  "Tverskaya St 10, Moscow"),
    ("Hana Park",       "hana.park@email.com",  "+82 10 1234 5678", "Gangnam Gu, Seoul"),
    ("Thomas Weber",    "t.weber@email.com",    "+49 30 1234 5678", "Unter den Linden 5, Berlin"),
    ("Fatima Al-Zahra", "fatima.z@email.com",   "+212 6 12 34 56 78","Boulevard Hassan II, Casablanca"),
    ("Lucas Moreau",    "l.moreau@email.com",   "+33 1 23 45 67 89","Rue du Faubourg, Lyon"),
    ("Rania Khalil",    "rania.k@email.com",    "+20 122 345 6789", "Corniche El Nil, Cairo"),
    ("Ethan Brooks",    "e.brooks@email.com",   "+1 212 555 0101",  "Park Ave 100, New York"),
    ("Zara Patel",      "z.patel@email.com",    "+44 7900 112233",  "King's Rd, London"),
    ("Carlos Reyes",    "c.reyes@email.com",    "+34 91 123 4567",  "Gran Via 22, Madrid"),
]

# ── Catalog ───────────────────────────────────────────────────────────────────
# (name, brand, product_type, subcategory, gender, family, concentration,
#  top_notes, heart_notes, base_notes,
#  longevity, sillage, seasons, occasions,
#  bottle_color, cap_style,
#  sizes [(ml, price, stock)],
#  variants,       # [{name, shade_hex, stock}] or None
#  skin_type,      # list or None
#  ingredients,    # str
#  how_to_use,     # str
#  description, collection, year, perfumer,
#  is_new, is_featured, sale_pct)

CATALOG = [

    # ════════════════════════════════════════════════════════
    # FRAGRANCE — LUMIÈRE NOIRE (French luxury)
    # ════════════════════════════════════════════════════════
    ("Velvet Iris", "Lumière Noire", "perfume", "Eau de Parfum", "Women",
     "Floral", "Eau de Parfum",
     ["bergamot", "violet leaf", "aldehydes"], ["iris", "rose", "peony"], ["white musk", "sandalwood"],
     9, 8, ["Spring", "Fall"], ["Date Night", "Evening"], "#9B6B9B", "tall",
     [(30, 65, 24), (50, 110, 18), (100, 175, 12)], None, None, "", "",
     "An ethereal iris softened by powdery violet and a veil of white musk.",
     "La Nuit", 2021, "Mathilde Renard", False, True, 0),

    ("Noir Encens", "Lumière Noire", "perfume", "Eau de Parfum", "Men",
     "Woody", "Eau de Parfum",
     ["bergamot", "black pepper", "cardamom"], ["incense", "cedarwood", "labdanum"], ["oud", "sandalwood", "vetiver"],
     8, 7, ["Fall", "Winter"], ["Evening", "Work"], "#2C1810", "square",
     [(50, 95, 20), (100, 160, 15), (150, 210, 8)], None, None, "", "",
     "Cathedral incense reframed as modern masculinity. Cedar and vetiver ground a soaring smoky heart.",
     "La Nuit", 2019, "Mathilde Renard", False, True, 0),

    ("Amber Dusk", "Lumière Noire", "perfume", "Parfum", "Unisex",
     "Oriental/Amber", "Parfum",
     ["bergamot", "cinnamon", "saffron"], ["rose", "jasmine", "labdanum"], ["amber", "sandalwood", "vanilla", "musk"],
     10, 9, ["Fall", "Winter"], ["Evening", "Date Night"], "#C8A951", "tall",
     [(30, 80, 20), (50, 130, 14), (100, 200, 10)], None, None, "", "",
     "Rich amber and saffron draped over a rose heart — the golden hour in fragrance form.",
     "La Nuit", 2020, "Mathilde Renard", False, True, 0),

    ("Rose Citadel", "Lumière Noire", "perfume", "Parfum", "Women",
     "Floral", "Parfum",
     ["pink pepper", "lemon", "raspberry"], ["rose absolute", "geranium", "peony"], ["patchouli", "musk", "sandalwood"],
     9, 7, ["Spring", "Fall"], ["Date Night", "Wedding"], "#C86B8C", "round",
     [(30, 75, 22), (50, 120, 16), (100, 190, 10)], None, None, "", "",
     "A grand rose statement — bold enough for evenings, refined enough for ceremony.",
     "L'Aurore", 2018, "Mathilde Renard", False, True, 0),

    ("Midnight Bloom", "Lumière Noire", "perfume", "Parfum", "Women",
     "Floral", "Parfum",
     ["aldehydes", "bergamot", "pear"], ["tuberose", "jasmine", "ylang-ylang"], ["ambergris", "sandalwood", "white musk"],
     10, 9, ["Fall", "Winter"], ["Evening", "Wedding"], "#E8A0B4", "tall",
     [(30, 90, 18), (50, 145, 12), (100, 225, 8)], None, None, "", "",
     "A grand white floral that blooms in darkness — tuberose and jasmine under a veil of ambergris.",
     "La Nuit", 2024, "Mathilde Renard", True, True, 0),

    # ════════════════════════════════════════════════════════
    # FRAGRANCE — SÉRAIL (Middle-Eastern luxury)
    # ════════════════════════════════════════════════════════
    ("Shahd", "Sérail", "perfume", "Parfum", "Women",
     "Oriental/Amber", "Parfum",
     ["bergamot", "mandarin", "saffron"], ["rose", "jasmine", "oud"], ["amber", "musk", "sandalwood"],
     10, 9, ["Fall", "Winter"], ["Evening", "Date Night"], "#D4A017", "tall",
     [(30, 95, 18), (50, 155, 13), (100, 240, 8)], None, None, "", "",
     "Honey-drenched saffron over a velvety rose-oud heart. Shahd means 'pure honey' — and it delivers.",
     "Treasures of the East", 2020, "Khalid Al-Rashidi", False, True, 0),

    ("Oud Majlis", "Sérail", "perfume", "Parfum", "Men",
     "Woody", "Parfum",
     ["cardamom", "black pepper", "smoke"], ["oud", "rose", "labdanum"], ["sandalwood", "cedarwood", "amber"],
     10, 10, ["Fall", "Winter"], ["Evening", "Wedding"], "#2C1A0A", "square",
     [(30, 100, 15), (50, 165, 10), (100, 260, 6)], None, None, "", "",
     "A ceremonial oud of imposing grandeur — the scent of a candlelit majlis.",
     "Nights of Sérail", 2017, "Khalid Al-Rashidi", False, True, 0),

    ("Saffron Veil", "Sérail", "perfume", "Parfum", "Women",
     "Oriental/Amber", "Parfum",
     ["saffron", "bergamot", "rose petals"], ["rose absolute", "labdanum", "jasmine"], ["amber", "oud", "vanilla"],
     10, 9, ["Fall", "Winter"], ["Evening", "Wedding"], "#E8AA24", "tall",
     [(30, 105, 16), (50, 170, 11), (100, 265, 7)], None, None, "", "",
     "A nuptial saffron accord wrapped in rose and oud — ceremonial, opulent, unforgettable.",
     "Nights of Sérail", 2024, "Khalid Al-Rashidi", True, True, 0),

    ("Khamr", "Sérail", "perfume", "Parfum", "Unisex",
     "Oriental/Amber", "Parfum",
     ["saffron", "cinnamon", "bergamot"], ["labdanum", "rose", "agarwood"], ["dark amber", "oud", "musk"],
     10, 9, ["Fall", "Winter"], ["Evening"], "#8B1C1C", "tall",
     [(30, 110, 15), (50, 175, 10), (100, 275, 6)], None, None, "", "",
     "Deep, intoxicating, primal. Khamr is not for the faint of heart.",
     "Nights of Sérail", 2019, "Khalid Al-Rashidi", False, True, 0),

    # ════════════════════════════════════════════════════════
    # FRAGRANCE — VELOUR & CO. (Modern minimalist)
    # ════════════════════════════════════════════════════════
    ("Cotton Cloud", "Velour & Co.", "perfume", "Eau de Parfum", "Unisex",
     "Musk", "Eau de Parfum",
     ["bergamot", "clean musk", "aldehydes"], ["iris", "lily", "orris"], ["white musk", "cashmere wood", "sandalwood"],
     6, 5, ["Spring", "Summer", "Fall"], ["Casual", "Work"], "#E8E4E0", "round",
     [(30, 45, 32), (50, 70, 26), (100, 110, 18)], None, None, "", "",
     "The softness of a cloud against bare skin — a skin-scent musk that becomes uniquely yours.",
     "Quiet", 2022, "Ingrid Svensson", False, True, 0),

    ("Marble Room", "Velour & Co.", "perfume", "Eau de Parfum", "Unisex",
     "Fresh/Aquatic", "Eau de Parfum",
     ["lemon", "bergamot", "salt"], ["iris", "violet", "orris"], ["white musk", "ambrette", "cedarwood"],
     6, 5, ["Spring", "Summer"], ["Work", "Casual"], "#C8C8C8", "square",
     [(30, 50, 28), (50, 80, 22), (100, 125, 15)], None, None, "", "",
     "The scent of a sunlit marble atrium — cool, mineral, with an iris heart that warms over time.",
     "Quiet", 2020, "Ingrid Svensson", False, False, 0),

    ("Soft Return", "Velour & Co.", "perfume", "Eau de Parfum", "Women",
     "Musk", "Eau de Parfum",
     ["bergamot", "aldehydes", "raspberry"], ["rose", "peony", "iris"], ["white musk", "ambrette", "sandalwood"],
     6, 5, ["Spring", "Summer"], ["Casual", "Date Night"], "#FADADD", "round",
     [(30, 48, 30), (50, 75, 24), (100, 118, 16)], None, None, "", "",
     "A homecoming in scent — familiar, warm, and gently enveloping.",
     "Quiet", 2024, "Ingrid Svensson", True, False, 0),

    # ════════════════════════════════════════════════════════
    # FRAGRANCE — OBSIDIAN HOUSE (Dark luxury)
    # ════════════════════════════════════════════════════════
    ("Black Vetiver", "Obsidian House", "perfume", "Parfum", "Men",
     "Woody", "Parfum",
     ["bergamot", "black pepper", "violet leaf"], ["vetiver", "labdanum", "birch"], ["dark musk", "patchouli", "cedarwood"],
     10, 8, ["Fall", "Winter"], ["Evening"], "#1C1C1C", "square",
     [(30, 82, 20), (50, 132, 14), (100, 205, 9)], None, None, "", "",
     "Vetiver pushed to its darkest extreme — earthy, smoky, and austere.",
     "Dark Matter", 2018, "Damien Voclain", False, True, 0),

    ("Gunmetal Oud", "Obsidian House", "perfume", "Parfum", "Men",
     "Woody", "Parfum",
     ["cardamom", "saffron", "bergamot"], ["oud", "cedarwood", "labdanum"], ["dark musk", "ambergris", "sandalwood"],
     10, 10, ["Fall", "Winter"], ["Evening", "Wedding"], "#0A0A14", "square",
     [(30, 98, 15), (50, 158, 10), (100, 245, 6)], None, None, "", "",
     "A weaponized oud — dark, mineral, with a saffron heart that glows like embers.",
     "Dark Matter", 2024, "Damien Voclain", True, True, 0),

    ("Tar & Violet", "Obsidian House", "perfume", "Parfum", "Unisex",
     "Leather", "Parfum",
     ["bergamot", "violet leaf", "smoke"], ["violet", "labdanum", "leather accord"], ["birch tar", "oakmoss", "dark musk"],
     10, 8, ["Fall", "Winter"], ["Evening"], "#2C1C3C", "tall",
     [(30, 85, 18), (50, 138, 12), (100, 215, 8)], None, None, "", "",
     "The impossible pairing of violet and birch tar — tender and brutal in the same breath.",
     "Underworld", 2021, "Damien Voclain", False, False, 0),

    # ════════════════════════════════════════════════════════
    # FRAGRANCE — NYX ATELIER (Nocturnal)
    # ════════════════════════════════════════════════════════
    ("Velvet Smoke", "Nyx Atelier", "perfume", "Parfum", "Women",
     "Oriental/Amber", "Parfum",
     ["bergamot", "saffron", "cinnamon"], ["rose", "labdanum", "incense"], ["dark amber", "oud", "musk"],
     10, 9, ["Fall", "Winter"], ["Evening", "Date Night"], "#8C2E24", "tall",
     [(30, 85, 18), (50, 138, 12), (100, 215, 8)], None, None, "", "",
     "Velvet draped over embers — saffron and rose smouldering beneath amber and incense.",
     "Nocturne", 2020, "Isabelle Deschamps", False, True, 0),

    ("Dark Honey Veil", "Nyx Atelier", "perfume", "Parfum", "Women",
     "Gourmand", "Parfum",
     ["bergamot", "cinnamon", "saffron"], ["honey", "beeswax", "rose"], ["benzoin", "sandalwood", "dark musk"],
     9, 8, ["Fall", "Winter"], ["Evening", "Date Night"], "#C89028", "tall",
     [(30, 88, 16), (50, 142, 11), (100, 220, 7)], None, None, "", "",
     "Honey darkened by saffron and benzoin — an unctuous, smouldering veil.",
     "Twilight", 2024, "Isabelle Deschamps", True, True, 0),

    # ════════════════════════════════════════════════════════
    # FRAGRANCE — BRUME D'OR (Gourmand)
    # ════════════════════════════════════════════════════════
    ("Caramel Poudré", "Brume d'Or", "perfume", "Parfum", "Women",
     "Gourmand", "Parfum",
     ["bergamot", "cinnamon", "praline"], ["tonka bean", "vanilla", "caramel"], ["benzoin", "sandalwood", "white musk"],
     9, 8, ["Fall", "Winter"], ["Date Night", "Evening"], "#D4904A", "tall",
     [(30, 72, 22), (50, 115, 16), (100, 180, 11)], None, None, "", "",
     "Caramel dusted with the powder of tonka bean and sandalwood — edible luxury.",
     "Douceur", 2020, "Sophie Lefèvre", False, True, 0),

    ("Golden Sugar", "Brume d'Or", "perfume", "Parfum", "Women",
     "Gourmand", "Parfum",
     ["bergamot", "cinnamon", "praline"], ["tonka bean", "vanilla absolute", "caramel"], ["benzoin", "sandalwood", "dark musk"],
     10, 9, ["Fall", "Winter"], ["Evening", "Date Night"], "#D4A020", "tall",
     [(30, 80, 18), (50, 128, 12), (100, 200, 8)], None, None, "", "",
     "Spun gold in fragrance form — a monumental gourmand that wears like jewellery.",
     "Douceur", 2024, "Sophie Lefèvre", True, True, 0),

    # ════════════════════════════════════════════════════════
    # FRAGRANCE — SOLARA (Mediterranean)
    # ════════════════════════════════════════════════════════
    ("Sun Drenched", "Solara", "perfume", "Eau de Parfum", "Unisex",
     "Fresh/Aquatic", "Eau de Parfum",
     ["bergamot", "marine accord", "lemon"], ["jasmine", "orris", "aquatic notes"], ["white musk", "ambergris", "cedarwood"],
     6, 6, ["Spring", "Summer"], ["Casual", "Travel"], "#A8D0E8", "round",
     [(30, 48, 30), (50, 75, 24), (100, 118, 16)], None, None, "", "",
     "A Mediterranean afternoon distilled — salt, sun, and jasmine on warm stone.",
     "Solstice", 2022, "Lucia Ferrantini", False, True, 0),

    ("Neroli Shore", "Solara", "perfume", "Eau de Toilette", "Women",
     "Citrus", "Eau de Toilette",
     ["neroli", "bergamot", "lemon"], ["orange blossom", "jasmine", "peach"], ["white musk", "sandalwood"],
     4, 5, ["Spring", "Summer"], ["Casual", "Date Night"], "#FFD580", "round",
     [(30, 40, 34), (50, 63, 27), (100, 98, 18)], None, None, "", "",
     "Neroli straight from a Sicilian grove — sun-warmed, effervescent, and impossibly cheerful.",
     "Riviera", 2021, "Lucia Ferrantini", False, False, 15),

    # ════════════════════════════════════════════════════════
    # FRAGRANCE — AZUR COAST (Fresh aquatic)
    # ════════════════════════════════════════════════════════
    ("Côte d'Azur", "Azur Coast", "perfume", "Eau de Parfum", "Unisex",
     "Fresh/Aquatic", "Eau de Parfum",
     ["bergamot", "marine accord", "lemon"], ["jasmine", "orris", "aquatic notes"], ["white musk", "ambergris", "cedarwood"],
     6, 6, ["Spring", "Summer"], ["Casual", "Travel"], "#60A8D0", "round",
     [(30, 48, 32), (50, 78, 25), (100, 122, 17)], None, None, "", "",
     "The Côte d'Azur from a speedboat — salt spray, jasmine cliffs, ambergris.",
     "Marina", 2020, "Marco Visentini", False, True, 0),

    # ════════════════════════════════════════════════════════
    # SKINCARE — DUSK & DAWN (Luxury anti-ageing)
    # ════════════════════════════════════════════════════════
    ("Lumière Serum", "Dusk & Dawn", "skincare", "Serum", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F0E8D8", "tall",
     [(30, 95, 25), (50, 145, 15)], None,
     ["dry", "normal", "combination"],
     "Vitamin C (15%), Niacinamide (5%), Hyaluronic Acid, Ferulic Acid",
     "Apply 3–4 drops to cleansed skin morning and evening. Follow with moisturiser and SPF in the morning.",
     "A high-potency vitamin C serum that visibly brightens and evens skin tone in four weeks.",
     "Lumière Collection", 2022, "", True, True, 0),

    ("Dusk Retinol Cream", "Dusk & Dawn", "skincare", "Moisturiser", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#E8DCC8", "round",
     [(50, 110, 20)], None,
     ["normal", "dry", "combination"],
     "Encapsulated Retinol (0.3%), Peptides Complex, Ceramides, Squalane",
     "Apply a pea-sized amount to face and neck every evening after serum. Begin with every other night.",
     "A gentle but effective retinol moisturiser that reduces fine lines without compromising the barrier.",
     "Night Ritual", 2021, "", False, True, 0),

    ("Glacial Eye Elixir", "Dusk & Dawn", "skincare", "Eye Cream", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#D8E8F0", "tall",
     [(15, 85, 22)], None,
     ["all", "sensitive"],
     "Caffeine (3%), Peptides, Bakuchiol, Vitamin K",
     "Using the gold applicator, tap gently around the orbital bone morning and evening.",
     "A cooling, brightening eye elixir that visibly reduces puffiness and dark circles overnight.",
     "Night Ritual", 2023, "", False, True, 0),

    ("Velvet Barrier Cream", "Dusk & Dawn", "skincare", "Moisturiser", "Unisex",
     "", "", [], [], [],
     0, 0, [], [], "#F5EFE8", "round",
     [(50, 78, 24), (100, 125, 16)], None,
     ["dry", "sensitive", "normal"],
     "Ceramide Complex, Shea Butter, Oat Extract, Panthenol",
     "Apply to clean, dry skin morning and evening. Layer over serums.",
     "A rich, velvety moisturiser that strengthens the skin's natural barrier and delivers lasting hydration.",
     "Lumière Collection", 2022, "", False, True, 0),

    ("Dawn Cleansing Balm", "Dusk & Dawn", "skincare", "Cleanser", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F0E0C8", "round",
     [(100, 65, 28)], None,
     ["dry", "normal", "sensitive"],
     "Cleansing Esters, Rose Hip Oil, Vitamin E, Jojoba",
     "Massage onto dry skin in circular motions for 60 seconds. Emulsify with water and rinse.",
     "A melting cleansing balm that dissolves makeup and impurities while nourishing the skin barrier.",
     "Night Ritual", 2021, "", False, False, 15),

    ("Radiance Peel Mask", "Dusk & Dawn", "skincare", "Mask", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F8E8A0", "round",
     [(75, 72, 20)], None,
     ["normal", "combination", "oily"],
     "Glycolic Acid (5%), Lactic Acid (3%), Kaolin Clay, Niacinamide",
     "Apply a thin, even layer to cleansed skin. Leave for 10 minutes, then rinse thoroughly. Use weekly.",
     "A dual-action exfoliating and purifying mask for luminous, refined skin texture.",
     "Lumière Collection", 2023, "", False, False, 0),

    ("Aurora SPF 50+ Fluid", "Dusk & Dawn", "skincare", "SPF", "Unisex",
     "", "", [], [], [],
     0, 0, [], [], "#FFF8F0", "tall",
     [(50, 55, 30)], None,
     ["all", "sensitive"],
     "Tinosorb M, Tinosorb S, Niacinamide (3%), Hyaluronic Acid",
     "Apply generously as the last step of your morning routine. Reapply every 2 hours in direct sunlight.",
     "An ultra-light, invisible SPF 50+ fluid that doubles as a skin-perfecting primer.",
     "Lumière Collection", 2024, "", True, True, 0),

    # ════════════════════════════════════════════════════════
    # SKINCARE — ÉCLAT BOTANIQUE (Botanical)
    # ════════════════════════════════════════════════════════
    ("Rose Elixir Oil", "Éclat Botanique", "skincare", "Oil", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F0C8C0", "tall",
     [(30, 72, 22)], None,
     ["dry", "normal", "mature"],
     "Rosa Canina (Rosehip) Oil, Sea Buckthorn, Vitamin E, Bakuchiol",
     "Press 3–5 drops between palms, then press gently onto face and neck. Use morning or evening.",
     "A luxuriant facial oil blending rosehip and sea buckthorn to visibly plump and restore radiance.",
     "Jardins", 2021, "", False, True, 0),

    ("Petal Toner Mist", "Éclat Botanique", "skincare", "Toner", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F8D8E8", "round",
     [(100, 42, 30), (200, 68, 20)], None,
     ["all", "sensitive", "dry"],
     "Rosa Damascena Water, Aloe Vera, Glycerin, Allantoin",
     "Mist over face after cleansing or throughout the day for a hydration boost. No need to rinse.",
     "A soothing floral mist distilled from Bulgarian rose petals — the original multi-tasking toner.",
     "Jardins", 2022, "", False, False, 0),

    ("Green Enzyme Cleanser", "Éclat Botanique", "skincare", "Cleanser", "Unisex",
     "", "", [], [], [],
     0, 0, [], [], "#D0E8D0", "round",
     [(100, 48, 26)], None,
     ["all", "oily", "combination"],
     "Papaya Enzyme, Green Tea Extract, Niacinamide, Salicylic Acid (0.5%)",
     "Lather with water and massage onto face for 60 seconds. Rinse thoroughly.",
     "A gentle enzymatic cleanser that buffs away dead skin cells and minimises pores without stripping.",
     "Herbarium", 2023, "", False, False, 10),

    ("Honey Repair Mask", "Éclat Botanique", "skincare", "Mask", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F0D890", "round",
     [(75, 58, 24)], None,
     ["dry", "sensitive", "normal"],
     "Raw Honey, Propolis Extract, Oat Milk, Ceramides",
     "Apply a generous layer to cleansed skin. Leave for 15–20 minutes, rinse, or leave on as an overnight treatment.",
     "A deeply nourishing honey mask that calms, repairs, and delivers intensive overnight moisture.",
     "Herbarium", 2022, "", False, False, 0),

    # ════════════════════════════════════════════════════════
    # SKINCARE — LUMIÈRE NOIRE (Beauty extension)
    # ════════════════════════════════════════════════════════
    ("Noir Resurfacing Serum", "Lumière Noire", "skincare", "Serum", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#1C1C28", "tall",
     [(30, 118, 18)], None,
     ["normal", "combination", "oily"],
     "Retinal (0.1%), Azelaic Acid (10%), Niacinamide (5%), Hyaluronic Acid",
     "Apply 3–4 drops to cleansed skin in the evening. Begin with every other night to build tolerance.",
     "A next-generation retinal serum with azelaic acid for extraordinary skin renewal overnight.",
     "La Nuit", 2024, "", True, True, 0),

    # ════════════════════════════════════════════════════════
    # MAKEUP — ATELIER NUDE (Skin-tone inclusive)
    # ════════════════════════════════════════════════════════
    ("Skin Veil Foundation", "Atelier Nude", "makeup", "Foundation", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F5E8D8", "tall",
     [(30, 68, 20)],
     [
         {"name": "N10 Porcelain",   "shade_hex": "#F5E8D8", "stock": 15},
         {"name": "N20 Ivory",       "shade_hex": "#F0DEC8", "stock": 18},
         {"name": "N30 Sand",        "shade_hex": "#E8D0B0", "stock": 20},
         {"name": "W40 Warm Beige",  "shade_hex": "#D8B890", "stock": 18},
         {"name": "W50 Honey",       "shade_hex": "#C8A070", "stock": 16},
         {"name": "C60 Caramel",     "shade_hex": "#B08050", "stock": 14},
         {"name": "D70 Espresso",    "shade_hex": "#805830", "stock": 12},
         {"name": "D80 Ebony",       "shade_hex": "#502810", "stock": 10},
     ],
     ["all"],
     "Hyaluronic Acid, SPF 20, Niacinamide, Lightweight Film-Formers",
     "Apply with fingertips, brush or sponge. Build coverage as desired. Blends seamlessly.",
     "A breathable, skin-like foundation with buildable coverage from sheer to medium. 32 shades.",
     "Nude Studies", 2022, "", False, True, 0),

    ("Velvet Lip Colour", "Atelier Nude", "makeup", "Lipstick", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#C85060", "round",
     [(3.5, 32, 25)],
     [
         {"name": "Bare Truth",    "shade_hex": "#C8A090", "stock": 20},
         {"name": "Quiet Blush",   "shade_hex": "#D88080", "stock": 18},
         {"name": "Rose Archive",  "shade_hex": "#C86878", "stock": 16},
         {"name": "Berry Chapter", "shade_hex": "#883850", "stock": 14},
         {"name": "Plum Memoir",   "shade_hex": "#6C3050", "stock": 12},
         {"name": "Red Edition",   "shade_hex": "#B82030", "stock": 15},
     ],
     None,
     "Shea Butter, Vitamin E, Jojoba Oil, Ceramides",
     "Apply directly from bullet or with a lip brush for precision. Blot and reapply for intensity.",
     "A velvet-matte lip colour with a cashmere finish that conditions and plumps while colouring.",
     "Nude Studies", 2021, "", False, True, 0),

    ("Invisible Concealer", "Atelier Nude", "makeup", "Concealer", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F0E0C8", "tall",
     [(5, 38, 24)],
     [
         {"name": "Fair 1",   "shade_hex": "#F5EAD8", "stock": 16},
         {"name": "Light 2",  "shade_hex": "#EDD5BC", "stock": 18},
         {"name": "Medium 3", "shade_hex": "#D8B896", "stock": 20},
         {"name": "Tan 4",    "shade_hex": "#C09870", "stock": 16},
         {"name": "Deep 5",   "shade_hex": "#956040", "stock": 14},
     ],
     None,
     "Hyaluronic Acid, Caffeine, Peptides, Light-Diffusing Pigments",
     "Dot under eyes and blend with fingertip or brush. Set with loose powder for longevity.",
     "A creamy, full-coverage concealer that visibly lifts and brightens the under-eye area.",
     "Nude Studies", 2022, "", False, False, 0),

    ("Dew Drops Highlighter", "Atelier Nude", "makeup", "Highlighter", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F8E8A8", "round",
     [(8, 42, 22)],
     [
         {"name": "Champagne",   "shade_hex": "#F8E8A8", "stock": 18},
         {"name": "Rose Gold",   "shade_hex": "#E8C8A8", "stock": 16},
         {"name": "Icy Pearl",   "shade_hex": "#F0F0F8", "stock": 14},
         {"name": "Bronze Glow", "shade_hex": "#D8A870", "stock": 12},
     ],
     None,
     "Finely-milled Pearl Powder, Vitamin E, Jojoba",
     "Apply to cheekbones, brow bone, and inner corner of eye with fan brush.",
     "A pressed powder highlighter with an intensely luminous, finely-milled finish.",
     "Nude Studies", 2023, "", True, True, 0),

    # ════════════════════════════════════════════════════════
    # MAKEUP — LUMINESCE (Luminous, dewy)
    # ════════════════════════════════════════════════════════
    ("Luminous Mascara", "Luminesce", "makeup", "Mascara", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#0A0A0A", "tall",
     [(8, 28, 30)],
     [
         {"name": "Blackest Black", "shade_hex": "#0A0A0A", "stock": 25},
         {"name": "Deep Brown",     "shade_hex": "#2A1A0A", "stock": 18},
     ],
     None,
     "Conditioning Wax, Pro-Vitamin B5, Keratin, Buildable Polymers",
     "Starting at the root of lashes, wiggle brush upward in a zigzag motion. Layer for more volume.",
     "A buildable volumising mascara with a curved brush that lifts, separates and lengthens.",
     "Lumineux", 2022, "", False, True, 0),

    ("Glazed Lip Oil", "Luminesce", "makeup", "Lip Gloss", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#FF9090", "round",
     [(6, 24, 28)],
     [
         {"name": "Clear Glass",   "shade_hex": "#F8F8F8", "stock": 22},
         {"name": "Petal Pink",    "shade_hex": "#F0A0A8", "stock": 20},
         {"name": "Berry Kiss",    "shade_hex": "#D87090", "stock": 16},
         {"name": "Coral Reef",    "shade_hex": "#F08060", "stock": 14},
     ],
     None,
     "Jojoba Oil, Vitamin E, Hyaluronic Acid, Non-Sticky Film Formers",
     "Apply directly to lips and blot for a subtle wash of colour, or layer for intensity.",
     "A non-sticky lip oil that delivers glossy, hydrated lips with a barely-there tint.",
     "Lumineux", 2023, "", True, True, 0),

    ("Sculpt & Define Palette", "Luminesce", "makeup", "Eyeshadow", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#C8A878", "square",
     [(9, 55, 18)],
     [
         {"name": "Warm Nudes Palette",    "shade_hex": "#C8A878", "stock": 15},
         {"name": "Smoky Drama Palette",   "shade_hex": "#2C2028", "stock": 12},
         {"name": "Golden Hour Palette",   "shade_hex": "#D4A040", "stock": 10},
     ],
     None,
     "Finely-milled Pigments, Mica, Vitamin E, Silica",
     "Use lighter shades to highlight, medium tones to define the crease, dark shades to deepen the outer corner.",
     "A nine-shade eyeshadow palette balancing mattes and shimmers for effortless sculpting.",
     "Lumineux", 2022, "", False, True, 0),

    ("Dewy Skin Blush", "Luminesce", "makeup", "Blush", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#E8A0B0", "round",
     [(6, 35, 20)],
     [
         {"name": "First Blush",  "shade_hex": "#F0B0C0", "stock": 18},
         {"name": "Golden Peach", "shade_hex": "#E8A878", "stock": 16},
         {"name": "Berry Flush",  "shade_hex": "#C07080", "stock": 14},
         {"name": "Warm Terra",   "shade_hex": "#C07850", "stock": 12},
     ],
     None,
     "Finely-milled Pigments, Vitamin E, Jojoba, Light Diffusers",
     "Smile and apply to the apples of cheeks with a fluffy brush, blending upward toward temples.",
     "A cream-to-powder blush with a natural, skin-like flush that photographs beautifully.",
     "Lumineux", 2024, "", True, False, 0),

    ("Setting Mist Perfector", "Luminesce", "makeup", "Setting Spray", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#E8F0F8", "tall",
     [(100, 32, 28)], None,
     ["all"],
     "Aloe Vera Water, Glycerin, Hyaluronic Acid, Vitamin C",
     "Hold 20–30cm from face. Mist in an X then T pattern over finished makeup. Allow to dry naturally.",
     "A fine-mist setting spray that melts makeup into skin for a flawless 16-hour hold.",
     "Lumineux", 2023, "", False, True, 0),

    # ════════════════════════════════════════════════════════
    # HAIRCARE — SILKWOOD (Luxury haircare)
    # ════════════════════════════════════════════════════════
    ("Silk Repair Shampoo", "Silkwood", "haircare", "Shampoo", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F0E8D8", "tall",
     [(250, 38, 24), (500, 62, 16)], None,
     None,
     "Silk Protein, Argan Oil, Keratin, Panthenol, Sulfate-Free Cleansers",
     "Lather into wet hair, massage into scalp, leave for 2 minutes, rinse thoroughly.",
     "A sulfate-free, silk-protein shampoo that gently cleanses while rebuilding hair's natural strength.",
     "Silk Rituals", 2021, "", False, True, 0),

    ("Midnight Repair Mask", "Silkwood", "haircare", "Hair Mask", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#1C1C28", "round",
     [(200, 55, 20)], None,
     None,
     "Black Truffle Extract, Keratin, Argan Oil, Ceramides, Protein Complex",
     "Apply to towel-dried hair from mid-lengths to ends. Leave for 10–20 minutes, rinse.",
     "An intensely reparative overnight mask with black truffle extract for extraordinary shine.",
     "Silk Rituals", 2022, "", False, True, 0),

    ("Glossing Serum", "Silkwood", "haircare", "Hair Oil", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#D4C090", "tall",
     [(50, 48, 22)], None,
     None,
     "Argan Oil, Marula Oil, Camellia Seed Oil, Vitamin E",
     "Apply 2–3 drops to damp or dry hair, focusing on mid-lengths and ends. Do not rinse.",
     "A lightweight glossing serum that imparts mirror-like shine without weight or grease.",
     "Silk Rituals", 2023, "", True, False, 0),

    # ════════════════════════════════════════════════════════
    # HAIRCARE — ROOT & RITUAL (Natural)
    # ════════════════════════════════════════════════════════
    ("Botanical Scalp Scrub", "Root & Ritual", "haircare", "Shampoo", "Unisex",
     "", "", [], [], [],
     0, 0, [], [], "#D0C8A8", "round",
     [(200, 42, 22)], None,
     None,
     "Sea Salt, Rosemary Extract, Peppermint Oil, Salicylic Acid (0.5%)",
     "Apply to wet scalp, massage for 3–5 minutes, rinse. Use once or twice a week.",
     "A clarifying scalp scrub that removes buildup, stimulates circulation and promotes healthy growth.",
     "Root Therapy", 2022, "", False, False, 0),

    ("Strength Conditioner", "Root & Ritual", "haircare", "Conditioner", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#E8D8C0", "round",
     [(250, 36, 24), (500, 58, 16)], None,
     None,
     "Rice Protein, Avocado Oil, Biotin, Aloe Vera, Coconut Milk",
     "Apply to cleansed, towel-dried hair from roots to ends. Leave for 3–5 minutes, rinse.",
     "A nourishing conditioner that strengthens from root to tip, reducing breakage by up to 65%.",
     "Root Therapy", 2021, "", False, True, 0),

    # ════════════════════════════════════════════════════════
    # BODY — ÉCLAT BOTANIQUE (Body extension)
    # ════════════════════════════════════════════════════════
    ("Garden Body Butter", "Éclat Botanique", "body", "Body Cream", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#F0E8C8", "round",
     [(200, 48, 24)], None,
     ["dry", "normal"],
     "Shea Butter, Kokum Butter, Calendula Extract, Lavender Essential Oil",
     "Apply generously to damp skin after bathing. Massage in circular motions until absorbed.",
     "A whipped body butter infused with botanical extracts that transforms rough, dry skin overnight.",
     "Jardins", 2022, "", False, True, 0),

    ("Herb & Citrus Body Scrub", "Éclat Botanique", "body", "Scrub", "Unisex",
     "", "", [], [], [],
     0, 0, [], [], "#C8E0A0", "round",
     [(300, 42, 20)], None,
     ["all"],
     "Sugar Crystals, Olive Oil, Lemon Peel, Rosemary, Thyme",
     "Apply to wet skin in circular motions, focusing on rough areas. Rinse thoroughly.",
     "An invigorating botanical scrub that buffs away dullness, leaving skin silky and luminous.",
     "Herbarium", 2021, "", False, False, 0),

    # ════════════════════════════════════════════════════════
    # BODY — LUMIÈRE NOIRE (Body extension)
    # ════════════════════════════════════════════════════════
    ("Velvet Body Oil", "Lumière Noire", "body", "Body Oil", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#D4A050", "tall",
     [(100, 65, 18)], None,
     ["dry", "normal"],
     "Jojoba Oil, Argan Oil, Rose Hip Oil, Neroli Essential Oil, Vitamin E",
     "Apply to damp skin after shower. Warm a few drops between palms and press onto skin.",
     "A sumptuous dry oil infused with neroli and rose hip that absorbs instantly for luminous, touchable skin.",
     "L'Aurore", 2023, "", False, True, 0),

    ("Noir Bath Soak", "Lumière Noire", "body", "Bath & Shower", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#1C1C2C", "square",
     [(300, 52, 20)], None,
     ["all"],
     "Dead Sea Salts, Activated Charcoal, Rose Petals, Black Seed Oil, Mineral Complex",
     "Dissolve 3–4 tablespoons in a warm bath. Soak for 20 minutes. Pat dry.",
     "A detoxifying mineral bath soak with activated charcoal and black seed oil for a ritualised cleanse.",
     "La Nuit", 2022, "", False, False, 0),

    # ════════════════════════════════════════════════════════
    # BODY — SOLARA (Mediterranean body)
    # ════════════════════════════════════════════════════════
    ("Riviera Hand Cream", "Solara", "body", "Hand Cream", "Women",
     "", "", [], [], [],
     0, 0, [], [], "#FFF0D8", "round",
     [(75, 28, 30)], None,
     ["dry", "normal", "all"],
     "Shea Butter, Neroli Extract, Almond Oil, Vitamin E",
     "Apply a small amount to hands and massage until absorbed. Use as often as desired.",
     "A fast-absorbing Mediterranean hand cream with neroli and almond oil for soft, perfumed hands.",
     "Riviera", 2022, "", False, False, 20),
]

assert len(CATALOG) == 53, f"Expected 53 products, got {len(CATALOG)}"

FEATURED_INDICES = {0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 15, 17, 19, 21,
                    22, 25, 27, 29, 32, 35, 38, 40, 42, 44, 46, 48, 50, 52}
SALE_INDICES     = {18, 24, 30, 42, 50}


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


# ── Seed products ─────────────────────────────────────────────────────────────
print("Seeding 90 products...")
products: list[Product] = []

with Session(engine) as session:
    for idx, row in enumerate(CATALOG):
        (name, brand, ptype, subcat, gender,
         family, concentration,
         top, heart, base,
         longevity, sillage, seasons, occasions,
         color, cap, sizes_data,
         variants, skin_type, ingredients, how_to_use,
         desc, collection, year, perfumer,
         is_new, is_featured, _sale_pct) = row

        slug = slugify(name)

        sizes = [{"ml": ml, "price": float(price), "stock": stock}
                 for ml, price, stock in sizes_data]

        sale_price: float | None = None
        if idx in SALE_INDICES:
            min_price = min(s["price"] for s in sizes)
            disc = rng.randint(15, 25) / 100
            sale_price = round(min_price * (1 - disc), 2)

        is_new_flag      = is_new or (year >= 2024)
        is_featured_flag = is_featured or (idx in FEATURED_INDICES)

        p = Product(
            slug=slug, name=name, brand=brand,
            product_type=ptype, subcategory=subcat,
            gender=gender, family=family, concentration=concentration,
            top_notes=top or None, heart_notes=heart or None, base_notes=base or None,
            sizes=sizes,
            variants=variants, skin_type=skin_type,
            ingredients=ingredients, how_to_use=how_to_use,
            longevity=longevity, sillage=sillage,
            season=seasons or None, occasion=occasions or None,
            bottle_color=color, cap_style=cap,
            description=desc, collection=collection,
            year=year if year else None, perfumer=perfumer,
            images=[f"/products/{slug}.jpg"],
            tags=[ptype, brand.lower().replace(" ", "-"), subcat.lower().replace(" ", "-")],
            sale_price=sale_price,
            rating=0.0, review_count=0,
            is_new=is_new_flag, is_featured=is_featured_flag,
            is_active=True,
        )
        session.add(p)
        products.append(p)

    session.commit()
    for p in products:
        session.refresh(p)

print(f"  {len(products)} products inserted.")


# ── ProductVariant rows (makeup shade relational table) ───────────────────────
print("Seeding makeup shade variants...")
variant_total = 0

with Session(engine) as session:
    for p in products:
        if not p.variants:
            continue
        sizes_list = [s for s in (p.sizes or []) if isinstance(s, dict)]
        base_price = float(sizes_list[0]["price"]) if sizes_list else 0.0
        for shade in p.variants:
            if not isinstance(shade, dict):
                continue
            session.add(ProductVariant(
                product_id=p.id,
                kind="shade",
                label=shade.get("name", ""),
                shade_hex=shade.get("shade_hex", "#CCCCCC"),
                price=base_price,
                stock=shade.get("stock", 0),
            ))
            variant_total += 1
    session.commit()

print(f"  {variant_total} shade variants inserted.")


# ── Reviews ───────────────────────────────────────────────────────────────────
print("Seeding reviews (5-8 per product)...")
review_total = 0

with Session(engine) as session:
    for p in products:
        n = rng.randint(5, 8)
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
                date=(datetime.now() - timedelta(days=rng.randint(1, 730))).date().isoformat(),
            )
            session.add(rv)
            ratings.append(rating)
            review_total += 1

        p.review_count = len(ratings)
        p.rating = round(sum(ratings) / len(ratings), 1)
        session.add(p)

    session.commit()

print(f"  {review_total} reviews inserted.")


# ── Coupons ───────────────────────────────────────────────────────────────────
print("Seeding coupons...")
with Session(engine) as session:
    for code, pct in [("WELCOME10", 10), ("AURA20", 20), ("BEAUTY15", 15)]:
        existing = session.exec(select(Coupon).where(Coupon.code == code)).first()
        if not existing:
            session.add(Coupon(code=code, percent=pct, active=True))
    session.commit()
print("  Coupons WELCOME10, AURA20, BEAUTY15 ready.")


# ── Orders ────────────────────────────────────────────────────────────────────
print("Seeding ~65 historical orders...")
STATUSES = ["pending"] * 10 + ["confirmed"] * 20 + ["shipped"] * 25 + ["cancelled"] * 5

with Session(engine) as session:
    for i in range(65):
        days_ago = rng.randint(0, 90)
        created  = datetime.now() - timedelta(days=days_ago,
                                               hours=rng.randint(0, 23),
                                               minutes=rng.randint(0, 59))
        cust     = rng.choice(CUSTOMERS)
        name, email, phone, address = cust

        n_items    = rng.randint(1, 3)
        chosen_ids = [p.id for p in rng.sample(products, n_items)]
        chosen     = [session.get(Product, pid) for pid in chosen_ids]
        chosen     = [p for p in chosen if p]

        coupon_code, discount_pct = "", 0
        if rng.random() < 0.25:
            coupon_code, discount_pct = rng.choice(
                [("WELCOME10", 10), ("AURA20", 20), ("BEAUTY15", 15)]
            )

        subtotal = 0.0
        line_items: list[tuple] = []

        for prod in chosen:
            sizes = [s for s in (prod.sizes or []) if isinstance(s, dict)]
            if not sizes:
                continue
            size_obj = rng.choice(sizes)
            qty      = rng.randint(1, 2)
            unit     = float(prod.sale_price if prod.sale_price else size_obj["price"])
            subtotal += unit * qty
            line_items.append((prod, size_obj, qty, unit))

        if not line_items:
            continue

        discount = round(subtotal * discount_pct / 100, 2)
        shipping = 0.0 if subtotal >= 50.0 else 1.5
        total    = round(subtotal - discount + shipping, 2)

        o = Order(
            status=rng.choice(STATUSES),
            customer_name=name, customer_email=email,
            customer_phone=phone, customer_address=address,
            subtotal=round(subtotal, 2), shipping=shipping,
            discount=discount, total=total,
            coupon_code=coupon_code,
            payment_method=rng.choice(["cod", "card", "cod"]),
            created_at=created.isoformat(),
        )
        session.add(o)
        session.flush()

        for prod, size_obj, qty, unit in line_items:
            session.add(OrderItem(
                order_id=o.id, product_id=prod.id,
                product_name=prod.name,
                size_ml=size_obj["ml"], qty=qty, price=unit,
            ))

    session.commit()

print("  65 orders inserted.")
print("\nSeed complete.")
print("Next: python fetch_images_perfume.py  (rename/update for beauty if desired)")
