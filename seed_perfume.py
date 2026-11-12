"""
seed_perfume.py
Deterministic seed for AURA perfume store.
Drops ONLY: product, review, order_item, orders tables.
NEVER touches: admin_user, audit_log, settings, coupons.

Run after approval:  python seed_perfume.py   (from backend/)
PHP equivalent:      database/seeders/DatabaseSeeder.php  +  php artisan db:seed
Key concept:         SQLModel / SQLAlchemy sessions replace Laravel's Eloquent factories.
"""
import re
import random
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlmodel import Session, SQLModel
from models import engine, Product, Review, Order, OrderItem, Coupon

SEED = 42
rng = random.Random(SEED)

# ── Safety guard ──────────────────────────────────────────────────────────────
print("=" * 60)
print("  AURA Perfume Store — Seed Script")
print("  Drops & re-seeds: product, review, orders, order_item")
print("  NOT touched:      admin_user, audit_log, settings, coupons")
print("=" * 60)
confirm = input("  Type YES to continue: ").strip()
if confirm != "YES":
    print("Aborted.")
    raise SystemExit(0)


# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def ago(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).isoformat()


# ── Review copy ───────────────────────────────────────────────────────────────
REVIEW_POOL = [
    (5, "Absolutely stunning",         "My new signature scent. Longevity is incredible — still present 10 hours later. I've received three compliments today alone."),
    (5, "A true masterpiece",           "Complex, evolving, utterly captivating. The dry-down is where it truly shines. Worth every last penny."),
    (5, "My new obsession",             "I've tested hundreds of fragrances and this ranks among the very best. Sillage is noticeable without being overwhelming."),
    (4, "Very impressive",              "Beautiful composition, though the opening feels slightly sharp on my skin. The heart and base more than make up for it."),
    (4, "Sophisticated and long-lasting","Lasts about 7 hours on me. The flacon design is exquisite and matches the quality of the juice inside."),
    (5, "Perfect for evenings",         "An instant classic. Rich and seductive. My partner asked what I was wearing within minutes."),
    (4, "Grows on you",                 "At first I was unsure, but after 20 minutes it transformed into something truly special. Patience rewarded."),
    (3, "Decent but not for me",        "The quality is undeniable, but this family of scents is not really my thing. Might suit others better."),
    (5, "Exceeded expectations",        "Ordered a sample first and immediately bought the full bottle. Absolutely worth the investment."),
    (4, "Quiet luxury",                 "Sits in the category of quiet elegance — not screaming for attention, just effortlessly refined. Perfect for work."),
    (5, "Sensational longevity",        "Applied in the morning, still going strong at midnight. The base notes deepen beautifully over time."),
    (3, "Pleasant but expected more",   "For this price point, I expected more originality. Nice, but I've smelled similar compositions elsewhere."),
    (5, "On my third bottle",           "My third bottle. Enough said."),
    (4, "Great compliment getter",      "Three different people asked what I was wearing this week. That alone justifies the price."),
    (5, "Luxurious and unique",         "Unlike anything else in my collection. The bottle is a work of art too."),
    (4, "Very wearable daily",          "Perfect for daily use. Not too heavy, not too light — just right for all occasions."),
    (5, "Remarkable sillage",           "You enter a room and people know you're there. Powerful without being aggressive. Bravo."),
    (3, "Fades too quickly on me",      "The scent is beautiful but lasts only about 3 hours on my dry skin. Would love an extrait version."),
    (4, "Office-appropriate luxury",    "Sophisticated enough for important meetings, but not so loud it bothers colleagues. Ideal balance."),
    (5, "Bought a second as a gift",    "Bought this for myself, then immediately ordered another as a gift. No regrets whatsoever."),
    (5, "Addictive warmth",             "There's a warmth to this fragrance that feels like a cashmere blanket. I wear it every weekend."),
    (4, "Interesting opening",          "The opening is bold and distinctive. It settles into something more wearable after 30 minutes — and I love it."),
    (5, "Confident and sophisticated",  "This is what confidence smells like. I wear it on important days and it never lets me down."),
    (4, "Classy and understated",       "Not a showoff scent, which is exactly what I wanted. Refined, long-lasting, beautifully balanced."),
    (5, "Instant favourite",            "Bought based on a friend's recommendation and fell in love immediately. Already planning my next bottle."),
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

# ── Customer names / addresses (for seeded orders) ───────────────────────────
CUSTOMERS = [
    ("Layla Hassan",    "layla.hassan@email.com",    "+20 100 123 4567", "12 Al Nozha St, Cairo"),
    ("James Carter",    "j.carter@email.com",         "+44 7700 900001",  "8 Montague Pl, London"),
    ("Sophie Dubois",   "sophie.d@email.com",         "+33 6 12 34 56 78","17 Rue Rivoli, Paris"),
    ("Omar Al-Farsi",   "omar.farsi@email.com",       "+971 50 123 4567", "Al Wasl Rd, Dubai"),
    ("Isabella Rossi",  "i.rossi@email.com",          "+39 02 1234 5678",  "Via Roma 5, Milan"),
    ("Ahmed Sami",      "a.sami@email.com",           "+20 111 234 5678", "45 Tahrir Sq, Cairo"),
    ("Elena Petrova",   "elena.p@email.com",          "+7 495 123 4567",  "Tverskaya St 10, Moscow"),
    ("Carlos Reyes",    "c.reyes@email.com",          "+34 91 123 4567",  "Gran Via 22, Madrid"),
    ("Amina Bouzid",    "amina.b@email.com",          "+213 55 123 4567", "Rue Didouche, Algiers"),
    ("Hana Park",       "hana.park@email.com",        "+82 10 1234 5678", "Gangnam Gu, Seoul"),
    ("Thomas Weber",    "t.weber@email.com",          "+49 30 1234 5678", "Unter den Linden 5, Berlin"),
    ("Fatima Al-Zahra", "fatima.z@email.com",         "+212 6 12 34 56 78","Boulevard Hassan II, Casablanca"),
    ("Lucas Moreau",    "l.moreau@email.com",         "+33 1 23 45 67 89","Rue du Faubourg, Lyon"),
    ("Rania Khalil",    "rania.k@email.com",          "+20 122 345 6789", "Corniche El Nil, Cairo"),
    ("Ethan Brooks",    "e.brooks@email.com",         "+1 212 555 0101",  "Park Ave 100, New York"),
]

# ── Product catalog ───────────────────────────────────────────────────────────
# (name, brand, gender, family, concentration,
#  top_notes, heart_notes, base_notes,
#  longevity, sillage, seasons, occasions,
#  bottle_color, cap_style,
#  sizes [(ml, price, stock)],
#  description, collection, year, perfumer,
#  is_new, is_featured, sale_pct)

CATALOG = [

    # ════════════════════════════════════════════════════════
    # LUMIÈRE NOIRE  –  French luxury, Floral & Oriental
    # ════════════════════════════════════════════════════════
    ("Velvet Iris", "Lumière Noire", "Women", "Floral", "Parfum",
     ["bergamot", "violet leaf", "aldehydes"],
     ["iris", "rose", "peony", "violet"],
     ["white musk", "sandalwood", "cedarwood"],
     9, 8, ["Spring", "Fall"], ["Date Night", "Evening"],
     "#9B6B9B", "tall",
     [(30, 65, 24), (50, 110, 18), (100, 175, 12)],
     "An ethereal iris softened by powdery violet and a veil of white musk. Whispers of twilight captured in a flacon.",
     "La Nuit", 2021, "Mathilde Renard", False, True, 0),

    ("Noir Encens", "Lumière Noire", "Men", "Woody", "Eau de Parfum",
     ["bergamot", "black pepper", "cardamom"],
     ["incense", "cedarwood", "labdanum"],
     ["oud", "sandalwood", "vetiver"],
     8, 7, ["Fall", "Winter"], ["Evening", "Work"],
     "#2C1810", "square",
     [(50, 95, 20), (100, 160, 15), (150, 210, 8)],
     "Cathedral incense reframed as modern masculinity. Cedar and vetiver ground a soaring smoky heart.",
     "La Nuit", 2019, "Mathilde Renard", False, True, 0),

    ("Blossom Rift", "Lumière Noire", "Women", "Floral", "Eau de Toilette",
     ["lemon", "neroli", "peach"],
     ["magnolia", "jasmine", "rose"],
     ["white musk", "cedarwood"],
     5, 5, ["Spring", "Summer"], ["Casual", "Work"],
     "#F5B8C0", "round",
     [(30, 45, 30), (50, 70, 25), (100, 110, 18)],
     "A daytime floral as bright and effortless as an open window on a spring morning.",
     "L'Aurore", 2022, "Mathilde Renard", False, False, 15),

    ("Amber Dusk", "Lumière Noire", "Unisex", "Oriental/Amber", "Parfum",
     ["bergamot", "cinnamon", "saffron"],
     ["rose", "jasmine", "labdanum"],
     ["amber", "sandalwood", "vanilla", "musk"],
     10, 9, ["Fall", "Winter"], ["Evening", "Date Night"],
     "#C8A951", "tall",
     [(30, 80, 20), (50, 130, 14), (100, 200, 10)],
     "Rich amber and saffron draped over a rose heart — the golden hour in fragrance form.",
     "La Nuit", 2020, "Mathilde Renard", False, True, 0),

    ("Rose Citadel", "Lumière Noire", "Women", "Floral", "Parfum",
     ["pink pepper", "lemon", "raspberry"],
     ["rose absolute", "geranium", "peony"],
     ["patchouli", "musk", "sandalwood"],
     9, 7, ["Spring", "Fall"], ["Date Night", "Wedding"],
     "#C86B8C", "round",
     [(30, 75, 22), (50, 120, 16), (100, 190, 10)],
     "A grand rose statement — bold enough for evenings, refined enough for ceremony.",
     "L'Aurore", 2018, "Mathilde Renard", False, True, 0),

    ("Smoky Petal", "Lumière Noire", "Unisex", "Floral", "Eau de Parfum",
     ["pink pepper", "bergamot"],
     ["rose", "orris", "wood smoke"],
     ["vetiver", "oakmoss", "labdanum"],
     7, 6, ["Fall", "Winter"], ["Evening", "Casual"],
     "#8B6B6B", "square",
     [(50, 85, 22), (100, 140, 15), (150, 185, 9)],
     "A rose pierced by woodsmoke — tender yet untamed, a study in beautiful contradictions.",
     "La Nuit", 2023, "Mathilde Renard", True, False, 0),

    ("Midnight Bloom", "Lumière Noire", "Women", "Floral", "Parfum",
     ["aldehydes", "bergamot", "pear"],
     ["tuberose", "jasmine", "ylang-ylang", "lily"],
     ["ambergris", "sandalwood", "white musk"],
     10, 9, ["Fall", "Winter"], ["Evening", "Wedding"],
     "#E8A0B4", "tall",
     [(30, 90, 18), (50, 145, 12), (100, 225, 8)],
     "A grand white floral that blooms in darkness — tuberose and jasmine united under a veil of ambergris.",
     "La Nuit", 2024, "Mathilde Renard", True, True, 0),

    ("Cedar Throne", "Lumière Noire", "Men", "Woody", "Eau de Parfum",
     ["bergamot", "coriander", "lavender"],
     ["cedarwood", "orris", "rose"],
     ["vetiver", "oakmoss", "ambergris"],
     7, 7, ["Fall", "Spring"], ["Work", "Casual"],
     "#8B6946", "square",
     [(50, 80, 24), (100, 130, 18), (150, 175, 11)],
     "Stately cedarwood with the grace of orris and the depth of vetiver. A fragrance that commands quiet authority.",
     "L'Aurore", 2020, "Mathilde Renard", False, False, 20),

    # ════════════════════════════════════════════════════════
    # SÉRAIL  –  Middle-Eastern luxury, Oriental & Woody
    # ════════════════════════════════════════════════════════
    ("Shahd", "Sérail", "Women", "Oriental/Amber", "Parfum",
     ["bergamot", "mandarin", "saffron"],
     ["rose", "jasmine", "oud"],
     ["amber", "musk", "sandalwood"],
     10, 9, ["Fall", "Winter"], ["Evening", "Date Night"],
     "#D4A017", "tall",
     [(30, 95, 18), (50, 155, 13), (100, 240, 8)],
     "Honey-drenched saffron over a velvety rose-oud heart. Shahd means 'pure honey' — and it delivers.",
     "Treasures of the East", 2020, "Khalid Al-Rashidi", False, True, 0),

    ("Oud Majlis", "Sérail", "Men", "Woody", "Parfum",
     ["cardamom", "black pepper", "smoke"],
     ["oud", "rose", "labdanum"],
     ["sandalwood", "cedarwood", "amber", "musk"],
     10, 10, ["Fall", "Winter"], ["Evening", "Wedding"],
     "#2C1A0A", "square",
     [(30, 100, 15), (50, 165, 10), (100, 260, 6)],
     "A ceremonial oud of imposing grandeur — the scent of a candlelit majlis before an important occasion.",
     "Nights of Sérail", 2017, "Khalid Al-Rashidi", False, True, 0),

    ("Reem", "Sérail", "Women", "Floral", "Eau de Parfum",
     ["neroli", "bergamot", "lemon"],
     ["white rose", "jasmine", "peony"],
     ["musk", "sandalwood", "ambergris"],
     7, 7, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#F0D8D0", "round",
     [(30, 60, 28), (50, 95, 22), (100, 150, 15)],
     "Named for the graceful white gazelle — a luminous floral as pure and delicate as first light.",
     "Treasures of the East", 2022, "Khalid Al-Rashidi", False, False, 0),

    ("Khamr", "Sérail", "Unisex", "Oriental/Amber", "Parfum",
     ["saffron", "cinnamon", "bergamot"],
     ["labdanum", "rose", "agarwood"],
     ["dark amber", "oud", "musk", "sandalwood"],
     10, 9, ["Fall", "Winter"], ["Evening"],
     "#8B1C1C", "tall",
     [(30, 110, 15), (50, 175, 10), (100, 275, 6)],
     "Deep, intoxicating, primal. Khamr is not for the faint of heart — a resinous labyrinth that demands patience.",
     "Nights of Sérail", 2019, "Khalid Al-Rashidi", False, True, 0),

    ("Desert Wind", "Sérail", "Men", "Aromatic", "Eau de Parfum",
     ["lavender", "bergamot", "cardamom"],
     ["dry wood", "vetiver", "labdanum"],
     ["amber", "sandalwood", "musk"],
     7, 7, ["Spring", "Fall"], ["Casual", "Work"],
     "#C8A97A", "round",
     [(50, 70, 25), (100, 115, 18), (150, 155, 11)],
     "The dry warmth of Arabian deserts carried by a Mediterranean breeze — herbs and amber in perfect balance.",
     "Treasures of the East", 2021, "Khalid Al-Rashidi", False, False, 0),

    ("Pearl of Suhar", "Sérail", "Women", "Musk", "Eau de Parfum",
     ["bergamot", "aldehydes", "clean musk"],
     ["iris", "violet", "peach blossom"],
     ["white musk", "ambrette", "sandalwood"],
     6, 5, ["Spring", "Summer"], ["Casual", "Work"],
     "#E8E4DF", "round",
     [(30, 55, 30), (50, 85, 24), (100, 135, 16)],
     "Effortlessly clean with a powdery iris heart — the quiet elegance of a pearl, worn close to the skin.",
     "Treasures of the East", 2023, "Khalid Al-Rashidi", False, False, 10),

    ("Saffron Veil", "Sérail", "Women", "Oriental/Amber", "Parfum",
     ["saffron", "bergamot", "rose petals"],
     ["rose absolute", "labdanum", "jasmine"],
     ["amber", "oud", "sandalwood", "vanilla"],
     10, 9, ["Fall", "Winter"], ["Evening", "Wedding"],
     "#E8AA24", "tall",
     [(30, 105, 16), (50, 170, 11), (100, 265, 7)],
     "A nuptial saffron accord wrapped in rose and oud — ceremonial, opulent, unforgettable.",
     "Nights of Sérail", 2024, "Khalid Al-Rashidi", True, True, 0),

    ("Black Leather Souk", "Sérail", "Men", "Leather", "Parfum",
     ["cardamom", "black pepper", "smoke"],
     ["birch tar", "labdanum", "rose"],
     ["leather", "castoreum", "sandalwood", "musk"],
     9, 8, ["Fall", "Winter"], ["Evening"],
     "#1A0A00", "square",
     [(30, 90, 18), (50, 145, 12), (100, 225, 8)],
     "Raw, smoky leather softened by a whisper of rose. The scent of an ancient spice market at dusk.",
     "Nights of Sérail", 2020, "Khalid Al-Rashidi", False, True, 0),

    # ════════════════════════════════════════════════════════
    # VELOUR & CO.  –  Modern minimalist, Fresh & Clean
    # ════════════════════════════════════════════════════════
    ("Blanc Propre", "Velour & Co.", "Unisex", "Fresh/Aquatic", "Eau de Toilette",
     ["bergamot", "marine accord", "cucumber"],
     ["white tea", "violet", "aquatic notes"],
     ["white musk", "cedarwood"],
     4, 4, ["Spring", "Summer"], ["Casual", "Work"],
     "#F0F0F0", "round",
     [(30, 35, 35), (50, 55, 28), (100, 85, 20)],
     "A breath of fresh linen hung out to dry in a sea breeze. Clean, honest, and effortlessly modern.",
     "Essentials", 2021, "Ingrid Svensson", False, False, 0),

    ("Cotton Cloud", "Velour & Co.", "Unisex", "Musk", "Eau de Parfum",
     ["bergamot", "clean musk", "aldehydes"],
     ["iris", "lily", "orris"],
     ["white musk", "cashmere wood", "sandalwood"],
     6, 5, ["Spring", "Summer", "Fall"], ["Casual", "Work"],
     "#E8E4E0", "round",
     [(30, 45, 32), (50, 70, 26), (100, 110, 18)],
     "The softness of a cloud against bare skin — a skin-scent musk that becomes uniquely yours.",
     "Quiet", 2022, "Ingrid Svensson", False, True, 0),

    ("Zest Theory", "Velour & Co.", "Men", "Citrus", "Eau de Toilette",
     ["bergamot", "lemon", "grapefruit"],
     ["petitgrain", "rosemary", "geranium"],
     ["white musk", "cedarwood", "vetiver"],
     4, 4, ["Spring", "Summer"], ["Casual", "Sport"],
     "#F5D020", "round",
     [(50, 50, 30), (100, 80, 22), (150, 110, 14)],
     "A geometric citrus study: clean angles of lemon and grapefruit, grounded by dry woods and rosemary.",
     "Essentials", 2023, "Ingrid Svensson", False, False, 0),

    ("Marble Room", "Velour & Co.", "Unisex", "Fresh/Aquatic", "Eau de Parfum",
     ["lemon", "bergamot", "salt"],
     ["iris", "violet", "orris"],
     ["white musk", "ambrette", "cedarwood"],
     6, 5, ["Spring", "Summer"], ["Work", "Casual"],
     "#C8C8C8", "square",
     [(30, 50, 28), (50, 80, 22), (100, 125, 15)],
     "The scent of a sunlit marble atrium — cool, mineral, with an iris heart that warms over time.",
     "Quiet", 2020, "Ingrid Svensson", False, False, 0),

    ("Linen Mist", "Velour & Co.", "Women", "Fresh/Aquatic", "Eau de Toilette",
     ["bergamot", "ozonic accord", "peach"],
     ["rose", "violet", "lily"],
     ["white musk", "cedarwood"],
     4, 4, ["Spring", "Summer"], ["Casual"],
     "#E0EEF4", "round",
     [(30, 38, 34), (50, 60, 27), (100, 92, 19)],
     "Fresh-washed linen lifted by a soft ozonic accord and a hint of peach — effortless everyday luxury.",
     "Essentials", 2022, "Ingrid Svensson", False, False, 20),

    ("Static", "Velour & Co.", "Men", "Aromatic", "Eau de Toilette",
     ["lavender", "bergamot", "pink pepper"],
     ["sage", "rosemary", "orris"],
     ["cedarwood", "vetiver", "clean musk"],
     5, 5, ["Spring", "Fall"], ["Work", "Casual"],
     "#708090", "square",
     [(50, 55, 28), (100, 88, 20), (150, 118, 12)],
     "Electricity and herbs: a charged aromatic that sparks on the skin before settling into calm sophistication.",
     "Quiet", 2021, "Ingrid Svensson", False, False, 0),

    ("Soft Return", "Velour & Co.", "Women", "Musk", "Eau de Parfum",
     ["bergamot", "aldehydes", "raspberry"],
     ["rose", "peony", "iris"],
     ["white musk", "ambrette", "sandalwood"],
     6, 5, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#FADADD", "round",
     [(30, 48, 30), (50, 75, 24), (100, 118, 16)],
     "A homecoming in scent — familiar, warm, and gently enveloping, like returning to a place you love.",
     "Quiet", 2024, "Ingrid Svensson", True, False, 0),

    ("Glass Citron", "Velour & Co.", "Unisex", "Citrus", "Eau de Cologne",
     ["lemon", "bergamot", "lime"],
     ["neroli", "petitgrain"],
     ["white musk", "cedarwood"],
     3, 3, ["Spring", "Summer"], ["Casual", "Sport", "Travel"],
     "#E8F5A0", "round",
     [(50, 40, 35), (100, 65, 26), (150, 88, 17)],
     "Pure citrus distilled to its transparent essence — bright, clean, gone in a flash of light.",
     "Essentials", 2023, "Ingrid Svensson", False, False, 0),

    # ════════════════════════════════════════════════════════
    # ÉCLAT BOTANIQUE  –  Garden botanicals, Floral & Aromatic
    # ════════════════════════════════════════════════════════
    ("Peony Manuscript", "Éclat Botanique", "Women", "Floral", "Parfum",
     ["bergamot", "lemon", "pink pepper"],
     ["peony", "rose", "magnolia", "lily"],
     ["white musk", "sandalwood", "cedarwood"],
     9, 8, ["Spring", "Summer"], ["Wedding", "Date Night"],
     "#FFAEC9", "tall",
     [(30, 70, 22), (50, 115, 16), (100, 180, 11)],
     "A lush peony in full bloom — luminous, generous, and impossible not to adore. The garden at its peak.",
     "Jardins", 2020, "Céleste Dumont", False, True, 0),

    ("Herb Garden", "Éclat Botanique", "Unisex", "Aromatic", "Eau de Toilette",
     ["bergamot", "basil", "lemon verbena"],
     ["lavender", "rosemary", "thyme"],
     ["cedarwood", "oakmoss", "clean musk"],
     5, 5, ["Spring", "Summer"], ["Casual", "Sport"],
     "#7EC8A0", "round",
     [(50, 55, 28), (100, 88, 20), (150, 118, 13)],
     "A morning walk through a Provençal herb garden — lavender, thyme, and rosemary in dew-wet air.",
     "Herbarium", 2021, "Céleste Dumont", False, False, 0),

    ("Magnolia Atlas", "Éclat Botanique", "Women", "Floral", "Eau de Parfum",
     ["bergamot", "yuzu", "neroli"],
     ["magnolia", "rose", "jasmine"],
     ["white musk", "sandalwood"],
     7, 7, ["Spring"], ["Casual", "Date Night"],
     "#F5E6D0", "round",
     [(30, 55, 26), (50, 88, 20), (100, 138, 14)],
     "Creamy magnolia lit by a sharp yuzu top — fresh, floral, and endlessly wearable in spring.",
     "Jardins", 2022, "Céleste Dumont", False, False, 0),

    ("Thyme & Honey", "Éclat Botanique", "Unisex", "Gourmand", "Eau de Parfum",
     ["bergamot", "cinnamon", "cardamom"],
     ["thyme", "beeswax", "chamomile"],
     ["honey", "benzoin", "sandalwood"],
     7, 6, ["Fall", "Spring"], ["Casual", "Date Night"],
     "#D4A44C", "round",
     [(30, 58, 26), (50, 92, 20), (100, 145, 13)],
     "Herbs and honey from a terraced apiary — earthy, sweet, and unexpectedly addictive.",
     "Herbarium", 2021, "Céleste Dumont", False, False, 15),

    ("Violet Letter", "Éclat Botanique", "Women", "Floral", "Parfum",
     ["aldehydes", "bergamot", "lemon"],
     ["violet absolute", "iris", "rose"],
     ["orris root", "sandalwood", "musk"],
     9, 7, ["Spring", "Fall"], ["Work", "Date Night"],
     "#8E6FAE", "tall",
     [(30, 72, 20), (50, 118, 15), (100, 185, 10)],
     "A love letter written in violet ink — powdery, tender, and tinged with the nostalgia of soft aldehydes.",
     "Jardins", 2019, "Céleste Dumont", False, True, 0),

    ("Basil Clove", "Éclat Botanique", "Men", "Aromatic", "Eau de Toilette",
     ["bergamot", "black pepper", "cardamom"],
     ["basil", "clove", "orris"],
     ["cedarwood", "vetiver", "leather accord"],
     6, 6, ["Fall", "Winter"], ["Casual", "Work"],
     "#5C4A2A", "square",
     [(50, 60, 26), (100, 95, 19), (150, 128, 12)],
     "Bold botanicals on a dry woody base — a kitchen-garden spice raid in fragrance form.",
     "Herbarium", 2022, "Céleste Dumont", False, False, 0),

    ("Wisteria Path", "Éclat Botanique", "Women", "Floral", "Eau de Parfum",
     ["bergamot", "lemon", "peach"],
     ["wisteria", "rose", "peony"],
     ["white musk", "cedarwood", "sandalwood"],
     7, 6, ["Spring"], ["Casual", "Wedding"],
     "#C8A8D0", "round",
     [(30, 52, 28), (50, 82, 22), (100, 128, 15)],
     "Walking beneath a wisteria archway in full bloom — dreamy, purple-tinted, impossibly romantic.",
     "Jardins", 2023, "Céleste Dumont", False, False, 0),

    ("Lavender Opus", "Éclat Botanique", "Unisex", "Aromatic", "Eau de Parfum",
     ["bergamot", "lemon", "lavender"],
     ["lavender absolute", "orris", "geranium"],
     ["tonka bean", "cedarwood", "white musk"],
     6, 6, ["Spring", "Summer", "Fall"], ["Casual", "Work"],
     "#9B8FC8", "round",
     [(30, 50, 30), (50, 80, 24), (100, 125, 16)],
     "Lavender elevated from functional to lyrical — a full composition that earns its name: Opus.",
     "Herbarium", 2024, "Céleste Dumont", True, False, 0),

    # ════════════════════════════════════════════════════════
    # OBSIDIAN HOUSE  –  Dark luxury, Woody & Leather
    # ════════════════════════════════════════════════════════
    ("Black Vetiver", "Obsidian House", "Men", "Woody", "Parfum",
     ["bergamot", "black pepper", "violet leaf"],
     ["vetiver", "labdanum", "birch"],
     ["dark musk", "patchouli", "cedarwood"],
     10, 8, ["Fall", "Winter"], ["Evening"],
     "#1C1C1C", "square",
     [(30, 82, 20), (50, 132, 14), (100, 205, 9)],
     "Vetiver pushed to its darkest extreme — earthy, smoky, and austere. For those who prefer shadows.",
     "Dark Matter", 2018, "Damien Voclain", False, True, 0),

    ("Ash & Birch", "Obsidian House", "Unisex", "Woody", "Eau de Parfum",
     ["bergamot", "smoke", "aldehydes"],
     ["birch", "orris", "labdanum"],
     ["vetiver", "cedarwood", "dark musk"],
     8, 7, ["Fall", "Winter"], ["Casual", "Evening"],
     "#3C3C3C", "square",
     [(30, 68, 22), (50, 108, 16), (100, 168, 11)],
     "The aftermath of a fire in a birch forest — melancholy, beautiful, with an orris heart of unexpected tenderness.",
     "Underworld", 2021, "Damien Voclain", False, False, 0),

    ("Iron Patchouli", "Obsidian House", "Men", "Leather", "Parfum",
     ["cardamom", "smoke", "bergamot"],
     ["patchouli", "labdanum", "rose"],
     ["leather", "sandalwood", "dark musk"],
     10, 9, ["Fall", "Winter"], ["Evening"],
     "#2A1810", "tall",
     [(30, 88, 18), (50, 142, 12), (100, 220, 8)],
     "Patchouli stripped of its sweetness and given the weight of iron and smoked leather. Uncompromising.",
     "Dark Matter", 2019, "Damien Voclain", False, True, 0),

    ("Smoked Labdanum", "Obsidian House", "Unisex", "Oriental/Amber", "Parfum",
     ["bergamot", "cinnamon", "smoke"],
     ["labdanum", "rose", "incense"],
     ["dark amber", "oud", "sandalwood"],
     10, 9, ["Fall", "Winter"], ["Evening"],
     "#5C2800", "tall",
     [(30, 92, 18), (50, 148, 12), (100, 230, 8)],
     "Labdanum smoked over sacred woods — a resinous, meditative fragrance that exists outside of time.",
     "Underworld", 2020, "Damien Voclain", False, True, 0),

    ("Dark Resin", "Obsidian House", "Men", "Woody", "Eau de Parfum",
     ["black pepper", "bergamot", "galbanum"],
     ["labdanum", "birch tar", "cedarwood"],
     ["dark resin", "vetiver", "patchouli"],
     8, 7, ["Fall", "Winter"], ["Casual", "Evening"],
     "#2E1A0A", "square",
     [(50, 90, 20), (100, 145, 14), (150, 192, 9)],
     "A resinous forest after winter rain — raw, balsamic, and deeply grounding.",
     "Dark Matter", 2022, "Damien Voclain", False, False, 0),

    ("Tar & Violet", "Obsidian House", "Unisex", "Leather", "Parfum",
     ["bergamot", "violet leaf", "smoke"],
     ["violet", "labdanum", "leather accord"],
     ["birch tar", "oakmoss", "dark musk"],
     10, 8, ["Fall", "Winter"], ["Evening"],
     "#2C1C3C", "tall",
     [(30, 85, 18), (50, 138, 12), (100, 215, 8)],
     "The impossible pairing of violet and birch tar — tender and brutal in the same breath.",
     "Underworld", 2021, "Damien Voclain", False, False, 0),

    ("Gunmetal Oud", "Obsidian House", "Men", "Woody", "Parfum",
     ["cardamom", "saffron", "bergamot"],
     ["oud", "cedarwood", "labdanum"],
     ["dark musk", "ambergris", "sandalwood"],
     10, 10, ["Fall", "Winter"], ["Evening", "Wedding"],
     "#0A0A14", "square",
     [(30, 98, 15), (50, 158, 10), (100, 245, 6)],
     "A weaponized oud — dark, mineral, with a saffron heart that glows like embers in the abyss.",
     "Dark Matter", 2024, "Damien Voclain", True, True, 0),

    ("Rusted Fig", "Obsidian House", "Unisex", "Woody", "Eau de Parfum",
     ["fig leaf", "bergamot", "green notes"],
     ["orris", "cedarwood", "birch"],
     ["vetiver", "dark musk", "patchouli"],
     7, 6, ["Fall"], ["Casual", "Date Night"],
     "#6B3A28", "round",
     [(30, 65, 22), (50, 105, 16), (100, 162, 11)],
     "Fig harvested too late — overripe, earthy, and tinged with the iron of autumn soil.",
     "Underworld", 2023, "Damien Voclain", False, False, 10),

    # ════════════════════════════════════════════════════════
    # SOLARA  –  Mediterranean sun, Citrus & Fresh
    # ════════════════════════════════════════════════════════
    ("Neroli Shore", "Solara", "Women", "Citrus", "Eau de Toilette",
     ["neroli", "bergamot", "lemon"],
     ["orange blossom", "jasmine", "peach"],
     ["white musk", "sandalwood"],
     4, 5, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#FFD580", "round",
     [(30, 40, 34), (50, 63, 27), (100, 98, 18)],
     "Neroli straight from a Sicilian grove — sun-warmed, effervescent, and impossibly cheerful.",
     "Riviera", 2021, "Lucia Ferrantini", False, False, 0),

    ("Sun Drenched", "Solara", "Unisex", "Fresh/Aquatic", "Eau de Parfum",
     ["bergamot", "marine accord", "lemon"],
     ["jasmine", "orris", "aquatic notes"],
     ["white musk", "ambergris", "cedarwood"],
     6, 6, ["Spring", "Summer"], ["Casual", "Travel"],
     "#A8D0E8", "round",
     [(30, 48, 30), (50, 75, 24), (100, 118, 16)],
     "A Mediterranean afternoon distilled — salt, sun, and the distant scent of jasmine on warm stone.",
     "Solstice", 2022, "Lucia Ferrantini", False, True, 0),

    ("Bergamot Garden", "Solara", "Unisex", "Citrus", "Eau de Cologne",
     ["bergamot", "lemon", "orange"],
     ["neroli", "petitgrain", "lavender"],
     ["cedarwood", "white musk"],
     3, 4, ["Spring", "Summer"], ["Sport", "Casual", "Travel"],
     "#C8E060", "round",
     [(50, 38, 36), (100, 62, 27), (150, 84, 17)],
     "The bergamot garden at dawn — a cologne as refreshing and uncomplicated as morning air.",
     "Riviera", 2020, "Lucia Ferrantini", False, False, 0),

    ("Sorrento Fig", "Solara", "Women", "Citrus", "Eau de Parfum",
     ["lemon", "fig", "bergamot"],
     ["fig leaf", "rose", "jasmine"],
     ["white musk", "sandalwood", "cedarwood"],
     5, 5, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#90C865", "round",
     [(30, 45, 30), (50, 72, 24), (100, 112, 16)],
     "A fig tree reaching over a terracotta wall — green, sun-drenched, with a floral jasmine heart.",
     "Riviera", 2022, "Lucia Ferrantini", False, False, 0),

    ("Amalfi Breeze", "Solara", "Unisex", "Fresh/Aquatic", "Eau de Toilette",
     ["lemon", "marine accord", "bergamot"],
     ["rosemary", "violet", "aquatic notes"],
     ["white musk", "cedarwood"],
     4, 4, ["Spring", "Summer"], ["Casual", "Sport", "Travel"],
     "#70C8E0", "round",
     [(30, 38, 36), (50, 60, 29), (100, 92, 19)],
     "Wind off the Tyrrhenian Sea carrying lemon, rosemary, and salt. A holiday in a bottle.",
     "Solstice", 2021, "Lucia Ferrantini", False, False, 20),

    ("Sicilian Blood", "Solara", "Men", "Citrus", "Eau de Toilette",
     ["blood orange", "bergamot", "black pepper"],
     ["petitgrain", "geranium", "rosemary"],
     ["vetiver", "cedarwood", "white musk"],
     4, 5, ["Spring", "Summer"], ["Casual", "Sport"],
     "#E84820", "round",
     [(50, 55, 28), (100, 88, 20), (150, 118, 12)],
     "Blood orange with a bite of black pepper — vivid, masculine, and unapologetically vibrant.",
     "Riviera", 2022, "Lucia Ferrantini", False, False, 0),

    ("Capri Flora", "Solara", "Women", "Floral", "Eau de Parfum",
     ["bergamot", "neroli", "lemon"],
     ["rose", "jasmine", "freesia"],
     ["white musk", "sandalwood"],
     6, 6, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#FFB8D0", "round",
     [(30, 50, 30), (50, 80, 24), (100, 125, 16)],
     "Island florals kissed by the Mediterranean — airy, sun-bright, and utterly carefree.",
     "Solstice", 2023, "Lucia Ferrantini", False, False, 0),

    ("Lemon Vaulted", "Solara", "Men", "Citrus", "Eau de Cologne",
     ["lemon", "bergamot", "lime"],
     ["rosemary", "basil", "lavender"],
     ["white musk", "cedarwood"],
     3, 4, ["Spring", "Summer"], ["Sport", "Casual", "Travel"],
     "#FFF068", "round",
     [(50, 42, 34), (100, 68, 25), (150, 92, 16)],
     "Architecture in citrus: a vaulted lemon accord supported by aromatic herbs and clean cedar.",
     "Riviera", 2024, "Lucia Ferrantini", True, False, 0),

    # ════════════════════════════════════════════════════════
    # NYX ATELIER  –  Nocturnal luxury, Oriental & Gourmand
    # ════════════════════════════════════════════════════════
    ("Velvet Smoke", "Nyx Atelier", "Women", "Oriental/Amber", "Parfum",
     ["bergamot", "saffron", "cinnamon"],
     ["rose", "labdanum", "incense"],
     ["dark amber", "oud", "musk"],
     10, 9, ["Fall", "Winter"], ["Evening", "Date Night"],
     "#8C2E24", "tall",
     [(30, 85, 18), (50, 138, 12), (100, 215, 8)],
     "Velvet draped over embers — saffron and rose smouldering beneath a canopy of amber and incense.",
     "Nocturne", 2020, "Isabelle Deschamps", False, True, 0),

    ("Nuit Profonde", "Nyx Atelier", "Unisex", "Musk", "Eau de Parfum",
     ["bergamot", "aldehydes", "clean musk"],
     ["iris", "violet", "orris"],
     ["dark musk", "ambrette", "tonka bean"],
     7, 6, ["Fall", "Winter"], ["Evening"],
     "#2C2C4C", "tall",
     [(30, 62, 24), (50, 98, 18), (100, 152, 12)],
     "Deep night distilled — an iris-musk for those who prefer the quiet hours after midnight.",
     "Twilight", 2022, "Isabelle Deschamps", False, False, 0),

    ("Cardamom Reverie", "Nyx Atelier", "Women", "Gourmand", "Eau de Parfum",
     ["cardamom", "bergamot", "cinnamon"],
     ["tonka bean", "vanilla", "rose"],
     ["sandalwood", "benzoin", "musk"],
     8, 7, ["Fall", "Winter"], ["Date Night", "Evening"],
     "#A05A28", "round",
     [(30, 60, 26), (50, 95, 20), (100, 148, 13)],
     "A spiced reverie: cardamom and cinnamon dissolve into tonka bean and vanilla like a half-remembered dream.",
     "Nocturne", 2021, "Isabelle Deschamps", False, False, 0),

    ("Incense & Iris", "Nyx Atelier", "Unisex", "Oriental/Amber", "Parfum",
     ["bergamot", "cinnamon", "labdanum"],
     ["incense", "iris", "rose", "labdanum"],
     ["amber", "oud", "sandalwood", "dark musk"],
     10, 9, ["Fall", "Winter"], ["Evening"],
     "#6B3878", "tall",
     [(30, 88, 18), (50, 142, 12), (100, 220, 8)],
     "Sacred incense meeting a cold iris heart — spiritual and earthly at once, profound and beautiful.",
     "Twilight", 2019, "Isabelle Deschamps", False, True, 0),

    ("Black Violet", "Nyx Atelier", "Women", "Floral", "Parfum",
     ["bergamot", "violet leaf", "aldehydes"],
     ["violet absolute", "iris", "orris"],
     ["dark musk", "patchouli", "sandalwood"],
     9, 7, ["Fall", "Winter"], ["Evening", "Date Night"],
     "#3C2060", "tall",
     [(30, 78, 20), (50, 125, 14), (100, 195, 9)],
     "Violet taken to its darkest possible expression — brooding, powdery, and deeply alluring.",
     "Nocturne", 2021, "Isabelle Deschamps", False, False, 0),

    ("Heliotrope Dreams", "Nyx Atelier", "Women", "Floral", "Eau de Parfum",
     ["bergamot", "almond", "cherry blossom"],
     ["heliotrope", "peony", "rose"],
     ["white musk", "vanilla", "sandalwood"],
     7, 7, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#D4A8C8", "round",
     [(30, 58, 26), (50, 92, 20), (100, 142, 14)],
     "Heliotrope — the sun-following flower — rendered as a warm, powdery dream of almond and peony.",
     "Twilight", 2022, "Isabelle Deschamps", False, False, 0),

    ("Amber Cloak", "Nyx Atelier", "Men", "Oriental/Amber", "Eau de Parfum",
     ["bergamot", "cinnamon", "black pepper"],
     ["labdanum", "amber", "rose"],
     ["dark amber", "sandalwood", "vetiver"],
     8, 8, ["Fall", "Winter"], ["Evening", "Work"],
     "#B87820", "square",
     [(50, 78, 22), (100, 125, 16), (150, 168, 10)],
     "An amber of quiet gravitas — warm, masculine, and impossible to ignore once you've smelled it.",
     "Nocturne", 2020, "Isabelle Deschamps", False, False, 0),

    ("Dark Honey Veil", "Nyx Atelier", "Women", "Gourmand", "Parfum",
     ["bergamot", "cinnamon", "saffron"],
     ["honey", "beeswax", "rose"],
     ["benzoin", "sandalwood", "dark musk", "tonka bean"],
     9, 8, ["Fall", "Winter"], ["Evening", "Date Night"],
     "#C89028", "tall",
     [(30, 88, 16), (50, 142, 11), (100, 220, 7)],
     "Honey darkened by saffron and benzoin — an unctuous, smouldering veil between you and the world.",
     "Twilight", 2024, "Isabelle Deschamps", True, True, 0),

    # ════════════════════════════════════════════════════════
    # BRUME D'OR  –  Gourmand indulgence & Musk
    # ════════════════════════════════════════════════════════
    ("Caramel Poudré", "Brume d'Or", "Women", "Gourmand", "Parfum",
     ["bergamot", "cinnamon", "praline"],
     ["tonka bean", "vanilla", "caramel", "rose"],
     ["benzoin", "sandalwood", "white musk"],
     9, 8, ["Fall", "Winter"], ["Date Night", "Evening"],
     "#D4904A", "tall",
     [(30, 72, 22), (50, 115, 16), (100, 180, 11)],
     "Caramel dusted with the powder of tonka bean and sandalwood — edible luxury at its most refined.",
     "Douceur", 2020, "Sophie Lefèvre", False, True, 0),

    ("Vanilla Reverie", "Brume d'Or", "Unisex", "Gourmand", "Eau de Parfum",
     ["bergamot", "cinnamon", "tonka"],
     ["vanilla absolute", "caramel", "orris"],
     ["sandalwood", "benzoin", "white musk"],
     8, 7, ["Fall", "Winter"], ["Casual", "Date Night"],
     "#F0D090", "round",
     [(30, 55, 28), (50, 88, 22), (100, 138, 15)],
     "Vanilla stripped of sweetness, rebuilt with orris and sandalwood into something deeply sophisticated.",
     "Plaisir", 2021, "Sophie Lefèvre", False, False, 0),

    ("Praline Kiss", "Brume d'Or", "Women", "Gourmand", "Eau de Parfum",
     ["bergamot", "raspberry", "almond"],
     ["praline", "rose", "violet"],
     ["tonka bean", "sandalwood", "white musk"],
     7, 7, ["Fall", "Winter"], ["Date Night", "Casual"],
     "#C87878", "round",
     [(30, 52, 28), (50, 82, 22), (100, 128, 15)],
     "A flirtatious praline accord softened by rose and violet — irresistible without being cloying.",
     "Douceur", 2022, "Sophie Lefèvre", False, False, 0),

    ("White Cocoa", "Brume d'Or", "Unisex", "Gourmand", "Eau de Parfum",
     ["bergamot", "cardamom", "cinnamon"],
     ["cocoa absolute", "vanilla", "orris"],
     ["sandalwood", "benzoin", "white musk"],
     7, 7, ["Fall", "Winter"], ["Casual", "Date Night"],
     "#F0E0D0", "round",
     [(30, 55, 28), (50, 88, 22), (100, 138, 15)],
     "White cocoa — the paler, creamier cousin of dark chocolate — blended with orris and warm spice.",
     "Plaisir", 2022, "Sophie Lefèvre", False, False, 10),

    ("Musc Délice", "Brume d'Or", "Women", "Musk", "Parfum",
     ["bergamot", "aldehydes", "raspberry"],
     ["rose", "peony", "lily"],
     ["white musk", "ambrette", "sandalwood", "benzoin"],
     8, 7, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#FAEAEA", "tall",
     [(30, 70, 22), (50, 112, 16), (100, 175, 11)],
     "A musk fantasy in white — sheer, floral, and gossamer-thin against the skin.",
     "Douceur", 2021, "Sophie Lefèvre", False, False, 0),

    ("Peach Dew", "Brume d'Or", "Women", "Floral", "Eau de Toilette",
     ["peach", "bergamot", "raspberry"],
     ["rose", "peony", "freesia"],
     ["white musk", "cedarwood"],
     5, 5, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#FFB878", "round",
     [(30, 42, 32), (50, 66, 26), (100, 102, 18)],
     "Morning dew on ripe peaches — luminous, innocent, and unashamedly pretty.",
     "Plaisir", 2023, "Sophie Lefèvre", False, False, 25),

    ("Golden Sugar", "Brume d'Or", "Women", "Gourmand", "Parfum",
     ["bergamot", "cinnamon", "praline"],
     ["tonka bean", "vanilla absolute", "caramel"],
     ["benzoin", "sandalwood", "dark musk"],
     10, 9, ["Fall", "Winter"], ["Evening", "Date Night"],
     "#D4A020", "tall",
     [(30, 80, 18), (50, 128, 12), (100, 200, 8)],
     "Spun gold in fragrance form — a monumental gourmand that wears like jewellery.",
     "Douceur", 2024, "Sophie Lefèvre", True, True, 0),

    ("Fleur de Coton", "Brume d'Or", "Unisex", "Musk", "Eau de Toilette",
     ["bergamot", "clean musk", "aldehydes"],
     ["white cotton accord", "iris", "violet"],
     ["white musk", "ambrette", "cedarwood"],
     5, 4, ["Spring", "Summer"], ["Casual", "Work"],
     "#F5F0EA", "round",
     [(50, 48, 32), (100, 78, 24), (150, 105, 15)],
     "The clean comfort of cotton sheets, warmed by iris and a barely-there white musk.",
     "Plaisir", 2022, "Sophie Lefèvre", False, False, 0),

    # ════════════════════════════════════════════════════════
    # TERROIR  –  Earth, fern & bark, Woody & Aromatic
    # ════════════════════════════════════════════════════════
    ("Forest Floor", "Terroir", "Unisex", "Woody", "Eau de Parfum",
     ["bergamot", "pine", "violet leaf"],
     ["orris", "cedarwood", "oakmoss"],
     ["vetiver", "dark musk", "patchouli"],
     8, 7, ["Fall", "Winter"], ["Casual", "Date Night"],
     "#3D5A28", "square",
     [(30, 58, 26), (50, 92, 20), (100, 142, 14)],
     "The forest floor in autumn — damp earth, pine resin, and oakmoss in a composition of quiet wonder.",
     "Terroir Series", 2019, "Jean-Baptiste Moreau", False, True, 0),

    ("Sage & Salt", "Terroir", "Unisex", "Aromatic", "Eau de Toilette",
     ["bergamot", "marine accord", "lemon"],
     ["sage", "rosemary", "violet"],
     ["cedarwood", "clean musk"],
     5, 5, ["Spring", "Summer"], ["Casual", "Sport"],
     "#9AB898", "round",
     [(50, 52, 30), (100, 84, 22), (150, 112, 14)],
     "Cliffside herbs above a salt-spray sea — untamed, bracing, and wonderfully alive.",
     "Reserve", 2021, "Jean-Baptiste Moreau", False, False, 0),

    ("Tobacco Leaf", "Terroir", "Men", "Leather", "Eau de Parfum",
     ["bergamot", "black pepper", "cardamom"],
     ["tobacco", "labdanum", "rose"],
     ["leather", "sandalwood", "vetiver"],
     8, 7, ["Fall", "Winter"], ["Evening", "Casual"],
     "#7A5230", "square",
     [(30, 60, 24), (50, 95, 18), (100, 148, 12)],
     "Sun-dried tobacco leaf over a rose-labdanum heart and a foundation of leather and sandalwood.",
     "Terroir Series", 2020, "Jean-Baptiste Moreau", False, False, 0),

    ("Moss & Cedar", "Terroir", "Men", "Woody", "Eau de Parfum",
     ["bergamot", "coriander", "lavender"],
     ["cedarwood", "orris", "oakmoss"],
     ["vetiver", "dark musk", "patchouli"],
     7, 7, ["Fall", "Winter", "Spring"], ["Casual", "Work"],
     "#4A6C3C", "square",
     [(50, 65, 26), (100, 105, 19), (150, 140, 12)],
     "Ancient cedar and living oakmoss — a masculine fougère of enduring character.",
     "Reserve", 2018, "Jean-Baptiste Moreau", False, False, 0),

    ("Vetiver Earth", "Terroir", "Men", "Woody", "Parfum",
     ["bergamot", "black pepper", "violet leaf"],
     ["vetiver", "orris", "labdanum"],
     ["vetiver absolute", "dark musk", "cedarwood"],
     10, 8, ["Fall", "Winter"], ["Work", "Evening"],
     "#2C3C1A", "tall",
     [(30, 70, 20), (50, 112, 15), (100, 175, 10)],
     "Vetiver at its most elemental — a parfum that distils the living earth into a single, arresting statement.",
     "Terroir Series", 2019, "Jean-Baptiste Moreau", False, True, 0),

    ("Smoky Fern", "Terroir", "Unisex", "Aromatic", "Eau de Parfum",
     ["bergamot", "smoke", "pine"],
     ["fern accord", "labdanum", "orris"],
     ["cedarwood", "vetiver", "clean musk"],
     7, 6, ["Fall"], ["Casual"],
     "#5C6A3C", "square",
     [(30, 55, 26), (50, 88, 20), (100, 138, 13)],
     "Fern fronds curling over smouldering pine — elemental and hypnotically green.",
     "Reserve", 2022, "Jean-Baptiste Moreau", False, False, 0),

    ("Bay & Leather", "Terroir", "Men", "Leather", "Parfum",
     ["bergamot", "cardamom", "bay rum"],
     ["leather accord", "labdanum", "birch"],
     ["dark musk", "sandalwood", "oakmoss"],
     9, 8, ["Fall", "Winter"], ["Evening"],
     "#3A2010", "tall",
     [(30, 78, 20), (50, 125, 14), (100, 195, 9)],
     "Bay rum and cracked leather — a gentleman's fragrance with the soul of an adventurer.",
     "Terroir Series", 2021, "Jean-Baptiste Moreau", False, False, 0),

    ("Clay Dusk", "Terroir", "Unisex", "Aromatic", "Eau de Toilette",
     ["bergamot", "mineral accord", "orris"],
     ["clay accord", "orris", "violet"],
     ["white musk", "cedarwood", "ambrette"],
     5, 5, ["Fall", "Winter"], ["Casual", "Work"],
     "#B09080", "round",
     [(50, 58, 28), (100, 92, 20), (150, 122, 13)],
     "Wet clay thrown on a wheel — mineral, earthy, and unexpectedly beautiful in its rawness.",
     "Reserve", 2024, "Jean-Baptiste Moreau", True, False, 0),

    # ════════════════════════════════════════════════════════
    # AZUR COAST  –  Mediterranean sea, Fresh & Aquatic
    # ════════════════════════════════════════════════════════
    ("Sea Glass", "Azur Coast", "Unisex", "Fresh/Aquatic", "Eau de Toilette",
     ["bergamot", "marine accord", "cucumber"],
     ["violet", "iris", "aquatic notes"],
     ["white musk", "ambergris"],
     4, 4, ["Spring", "Summer"], ["Casual", "Sport", "Travel"],
     "#A0D8D8", "round",
     [(30, 38, 36), (50, 60, 29), (100, 92, 19)],
     "Sea glass smoothed over decades on the ocean floor — cool, mineral, and effortlessly serene.",
     "Côte", 2021, "Marco Visentini", False, False, 0),

    ("Côte d'Azur", "Azur Coast", "Unisex", "Fresh/Aquatic", "Eau de Parfum",
     ["bergamot", "marine accord", "lemon"],
     ["jasmine", "orris", "aquatic notes"],
     ["white musk", "ambergris", "cedarwood"],
     6, 6, ["Spring", "Summer"], ["Casual", "Travel"],
     "#60A8D0", "round",
     [(30, 48, 32), (50, 78, 25), (100, 122, 17)],
     "The Côte d'Azur from a speedboat — salt spray, jasmine cliffs, and the warmth of ambergris.",
     "Marina", 2020, "Marco Visentini", False, True, 0),

    ("Coral Mist", "Azur Coast", "Women", "Fresh/Aquatic", "Eau de Toilette",
     ["grapefruit", "bergamot", "marine accord"],
     ["rose", "violet", "aquatic notes"],
     ["white musk", "cedarwood"],
     4, 4, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#F0A0A0", "round",
     [(30, 38, 34), (50, 60, 27), (100, 92, 18)],
     "Coral-pink marine air softened by violet and rose — feminine, fresh, and perfectly weightless.",
     "Côte", 2022, "Marco Visentini", False, False, 0),

    ("Mediterranean Salt", "Azur Coast", "Men", "Fresh/Aquatic", "Eau de Cologne",
     ["marine accord", "bergamot", "lemon"],
     ["rosemary", "lavender", "aquatic notes"],
     ["white musk", "cedarwood"],
     3, 4, ["Spring", "Summer"], ["Sport", "Casual", "Travel"],
     "#A8C0D8", "round",
     [(50, 38, 36), (100, 62, 27), (150, 84, 17)],
     "The elemental scent of Mediterranean salt — clean, honest, and deeply refreshing.",
     "Marina", 2021, "Marco Visentini", False, False, 0),

    ("Riviera Rose", "Azur Coast", "Women", "Floral", "Eau de Parfum",
     ["bergamot", "neroli", "lemon"],
     ["rose", "jasmine", "ylang-ylang"],
     ["white musk", "sandalwood"],
     6, 6, ["Spring", "Summer"], ["Casual", "Date Night"],
     "#FFB0C0", "round",
     [(30, 50, 30), (50, 80, 24), (100, 125, 16)],
     "A rose garden above a sunlit bay — the floral heart of the Riviera captured at golden hour.",
     "Côte", 2022, "Marco Visentini", False, False, 0),

    ("Aqua Iris", "Azur Coast", "Unisex", "Fresh/Aquatic", "Eau de Cologne",
     ["bergamot", "marine accord", "violet leaf"],
     ["iris", "violet", "aquatic notes"],
     ["white musk", "ambrette"],
     3, 4, ["Spring", "Summer"], ["Sport", "Casual"],
     "#9898E8", "round",
     [(50, 38, 34), (100, 62, 25), (150, 84, 16)],
     "Iris dissolved in sea water — an aquatic cologne of crystalline clarity.",
     "Marina", 2023, "Marco Visentini", False, False, 0),

    ("Seaside Verbena", "Azur Coast", "Unisex", "Citrus", "Eau de Toilette",
     ["lemon verbena", "bergamot", "lemon"],
     ["petitgrain", "geranium", "rose"],
     ["white musk", "cedarwood"],
     4, 4, ["Spring", "Summer"], ["Casual", "Sport"],
     "#C8E8A0", "round",
     [(30, 40, 34), (50, 63, 27), (100, 98, 18)],
     "Lemon verbena crushed between the fingers above the sea — green, luminous, and instantly uplifting.",
     "Côte", 2024, "Marco Visentini", True, False, 0),

    ("Mistral Blue", "Azur Coast", "Men", "Fresh/Aquatic", "Eau de Toilette",
     ["bergamot", "marine accord", "grapefruit"],
     ["rosemary", "lavender", "violet"],
     ["white musk", "cedarwood", "ambergris"],
     5, 5, ["Spring", "Summer"], ["Casual", "Sport"],
     "#4870B0", "round",
     [(50, 55, 28), (100, 88, 20), (150, 118, 12)],
     "The mistral wind off the Provençal coast — powerful, clean, and carrying the scent of open water.",
     "Marina", 2022, "Marco Visentini", False, False, 0),
]

assert len(CATALOG) == 80, f"Expected 80 products, got {len(CATALOG)}"

# Products that have a sale_price (index-based, deterministic)
SALE_INDICES = {2, 7, 11, 14, 19, 23, 27, 31, 37, 44, 51, 56, 59, 62, 65, 68}

# Featured products
FEATURED_INDICES = {0, 1, 3, 4, 8, 9, 11, 12, 16, 17, 24, 28, 32, 34, 35, 38,
                    40, 41, 48, 55, 56, 63, 64, 68, 70, 73}


# ── Drop & recreate tables ────────────────────────────────────────────────────
print("\nDropping tables...")
with engine.connect() as conn:
    conn.execute(text("PRAGMA foreign_keys = OFF"))
    for tbl in ("order_item", "orders", "review", "product"):
        conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
    conn.execute(text("PRAGMA foreign_keys = ON"))
    conn.commit()

SQLModel.metadata.create_all(engine)
print("Tables recreated.")


# ── Seed products ─────────────────────────────────────────────────────────────
print("Seeding 80 products...")
products: list[Product] = []

with Session(engine) as session:
    for idx, row in enumerate(CATALOG):
        (name, brand, gender, family, concentration,
         top, heart, base,
         longevity, sillage, seasons, occasions,
         color, cap, sizes_data,
         desc, collection, year, perfumer,
         is_new, is_featured, _sale_pct) = row

        slug = slugify(name)

        # Build sizes list
        sizes = [{"ml": ml, "price": float(price), "stock": stock}
                 for ml, price, stock in sizes_data]

        # sale_price: use smallest-size price with 15-25% discount
        sale_price: float | None = None
        if idx in SALE_INDICES:
            min_price = min(s["price"] for s in sizes)
            disc = rng.randint(15, 25) / 100
            sale_price = round(min_price * (1 - disc), 2)

        # Determine is_new flag: either explicitly marked or debut year >= 2024
        is_new_flag = is_new or (year >= 2024)
        # is_featured: from FEATURED_INDICES or explicit
        is_featured_flag = is_featured or (idx in FEATURED_INDICES)

        p = Product(
            slug=slug, name=name, brand=brand,
            gender=gender, family=family, concentration=concentration,
            top_notes=top, heart_notes=heart, base_notes=base,
            sizes=sizes,
            longevity=longevity, sillage=sillage,
            season=seasons, occasion=occasions,
            bottle_color=color, cap_style=cap,
            description=desc, collection=collection,
            year=year, perfumer=perfumer,
            images=[f"/products/{slug}.jpg"],
            tags=[family.lower().split("/")[0], brand.lower().replace(" ", "-"),
                  concentration.lower().replace(" ", "-")],
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


# ── Seed reviews ──────────────────────────────────────────────────────────────
print("Seeding reviews (5-8 per product)...")
review_count_total = 0

with Session(engine) as session:
    for p in products:
        n_reviews = rng.randint(5, 8)
        ratings: list[int] = []
        used_reviewers: set[str] = set()

        for _ in range(n_reviews):
            reviewer = rng.choice(REVIEWERS)
            # avoid duplicate reviewer per product
            for _ in range(10):
                if reviewer not in used_reviewers:
                    break
                reviewer = rng.choice(REVIEWERS)
            used_reviewers.add(reviewer)

            tpl = rng.choice(REVIEW_POOL)
            rating, title, body = tpl
            days_ago = rng.randint(1, 730)

            rv = Review(
                product_id=p.id,
                author=reviewer,
                rating=rating,
                title=title,
                body=body,
                date=(datetime.now() - timedelta(days=days_ago)).date().isoformat(),
            )
            session.add(rv)
            ratings.append(rating)
            review_count_total += 1

        # Update product aggregate
        p.review_count = len(ratings)
        p.rating = round(sum(ratings) / len(ratings), 1)
        session.add(p)

    session.commit()

print(f"  {review_count_total} reviews inserted.")


# ── Seed coupons ──────────────────────────────────────────────────────────────
print("Seeding coupons...")
with Session(engine) as session:
    for code, pct in [("WELCOME10", 10), ("AURA20", 20)]:
        existing = session.exec(
            __import__("sqlmodel").select(Coupon).where(Coupon.code == code)
        ).first()
        if not existing:
            session.add(Coupon(code=code, percent=pct, active=True))
    session.commit()
print("  Coupons WELCOME10 and AURA20 ready.")


# ── Seed orders (~60 over 90 days) ───────────────────────────────────────────
print("Seeding ~60 historical orders...")
STATUSES = ["pending"] * 10 + ["confirmed"] * 20 + ["shipped"] * 20 + ["cancelled"] * 5
ORDER_COUNT = 60

with Session(engine) as session:
    for i in range(ORDER_COUNT):
        days_ago = rng.randint(0, 90)
        created = datetime.now() - timedelta(days=days_ago,
                                              hours=rng.randint(0, 23),
                                              minutes=rng.randint(0, 59))
        cust = rng.choice(CUSTOMERS)
        name, email, phone, address = cust

        # 1-3 line items
        n_items = rng.randint(1, 3)
        chosen_products = rng.sample(products, n_items)

        # Optional coupon
        coupon_code = ""
        discount_pct = 0
        if rng.random() < 0.25:
            coupon_code, discount_pct = rng.choice([("WELCOME10", 10), ("AURA20", 20)])

        subtotal = 0.0
        line_items: list[tuple[Product, dict, int]] = []

        for prod in chosen_products:
            sizes = [s for s in (prod.sizes or []) if isinstance(s, dict) and s.get("stock", 0) > 0]
            if not sizes:
                sizes = [s for s in (prod.sizes or []) if isinstance(s, dict)]
            if not sizes:
                continue
            size_obj = rng.choice(sizes)
            qty = rng.randint(1, 2)
            unit_price = float(prod.sale_price if prod.sale_price else size_obj["price"])
            subtotal += unit_price * qty
            line_items.append((prod, size_obj, qty))

        if not line_items:
            continue

        discount = round(subtotal * discount_pct / 100, 2)
        shipping = 0.0 if subtotal >= 50.0 else 1.5
        total = round(subtotal - discount + shipping, 2)
        status = rng.choice(STATUSES)

        o = Order(
            status=status,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            customer_address=address,
            subtotal=round(subtotal, 2),
            shipping=shipping,
            discount=discount,
            total=total,
            coupon_code=coupon_code,
            payment_method=rng.choice(["cod", "card", "cod"]),
            created_at=created.isoformat(),
        )
        session.add(o)
        session.flush()

        for prod, size_obj, qty in line_items:
            session.add(OrderItem(
                order_id=o.id,
                product_id=prod.id,
                product_name=prod.name,
                size_ml=size_obj["ml"],
                qty=qty,
                price=float(prod.sale_price if prod.sale_price else size_obj["price"]),
            ))

    session.commit()

print(f"  {ORDER_COUNT} orders inserted.")
print("\nSeed complete. Run `python fetch_images_perfume.py` to download product images.")
