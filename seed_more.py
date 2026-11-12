"""Add 2 more products per subcategory to fill the catalog."""
import re, hashlib
from models import engine, Product
from sqlmodel import Session, select

PALETTE = [
    [{"name": "Obsidian",   "hex": "#1a1a1a"}, {"name": "Chalk",      "hex": "#f5f5f0"}, {"name": "Navy",      "hex": "#1b2a4a"}],
    [{"name": "Charcoal",   "hex": "#36454f"}, {"name": "Stone",      "hex": "#8a8a8a"}, {"name": "Forest",    "hex": "#2d4a3e"}],
    [{"name": "Rust",       "hex": "#8b4513"}, {"name": "Sand",       "hex": "#c2a87c"}, {"name": "Cream",     "hex": "#fffdd0"}],
    [{"name": "Slate Blue", "hex": "#4a6fa5"}, {"name": "Burgundy",   "hex": "#722f37"}, {"name": "Olive",     "hex": "#6b6b2a"}],
    [{"name": "Midnight",   "hex": "#191970"}, {"name": "Ash",        "hex": "#b2beb5"}, {"name": "Caramel",   "hex": "#c68642"}],
    [{"name": "Ink",        "hex": "#0d0d0d"}, {"name": "Pearl",      "hex": "#fafafa"}, {"name": "Sage",      "hex": "#77815c"}],
    [{"name": "Teal",       "hex": "#008080"}, {"name": "Blush",      "hex": "#ffb6c1"}, {"name": "Espresso",  "hex": "#4b2f2f"}],
    [{"name": "Cobalt",     "hex": "#0047ab"}, {"name": "Ivory",      "hex": "#fffff0"}, {"name": "Mahogany",  "hex": "#4a0000"}],
]

SIZES_DEFAULT  = ["XS", "S", "M", "L", "XL", "XXL"]
SIZES_FOOTWEAR = ["38", "39", "40", "41", "42", "43", "44", "45"]
SIZES_KIDS     = ["4Y", "6Y", "8Y", "10Y", "12Y", "14Y"]
SIZES_KIDS_FT  = ["30", "31", "32", "33", "34", "35", "36", "37"]
SIZES_ONE      = ["One Size"]

FABRICS = {
    "T-Shirts": "100% Cotton", "Polos": "95% Cotton, 5% Elastane",
    "Shirts": "100% Cotton", "Tank Tops": "95% Cotton, 5% Elastane",
    "Long Sleeves": "60% Cotton, 40% Polyester",
    "Pullover": "80% Cotton, 20% Polyester", "Zip Hoodie": "80% Cotton, 20% Polyester",
    "Crewneck": "80% Cotton, 20% Polyester", "Oversized": "80% Cotton, 20% Polyester",
    "Sweaters": "60% Wool, 40% Acrylic", "Cardigans": "60% Wool, 40% Acrylic",
    "Turtlenecks": "50% Merino Wool, 50% Cotton",
    "Bomber": "100% Nylon", "Denim Jacket": "100% Cotton Denim",
    "Puffer": "Shell: 100% Polyester, Fill: 90% Down", "Leather Jacket": "100% Genuine Leather",
    "Windbreaker": "100% Nylon", "Trench": "65% Cotton, 35% Polyester",
    "Wool Coat": "90% Wool, 10% Nylon", "Blazer": "60% Polyester, 35% Viscose, 5% Elastane",
    "Jeans": "99% Cotton, 1% Elastane", "Cargo Pants": "100% Cotton",
    "Joggers": "60% Cotton, 40% Polyester", "Chinos": "98% Cotton, 2% Elastane",
    "Shorts": "100% Cotton", "Skirts": "100% Cotton",
    "Leggings": "80% Nylon, 20% Spandex", "Sports Bras": "75% Nylon, 25% Spandex",
    "Track Pants": "80% Cotton, 20% Polyester", "Training Tees": "90% Polyester, 10% Spandex",
    "Loungewear Sets": "95% Cotton, 5% Elastane",
    "Mini": "100% Polyester", "Midi": "60% Viscose, 40% Polyester", "Maxi": "100% Linen",
    "Crop Tops": "95% Cotton, 5% Elastane",
    "Sneakers": "Upper: Leather/Mesh, Sole: Rubber",
    "Boots": "Upper: Full-grain Leather, Sole: Rubber",
    "Loafers": "Upper: Calfskin, Sole: Leather",
    "Slides": "Upper: EVA/Leather, Sole: Rubber",
    "Sandals": "Upper: Leather, Sole: Rubber",
    "Caps": "100% Cotton", "Beanies": "100% Acrylic",
    "Bags & Backpacks": "100% Canvas", "Belts": "100% Leather",
    "Sunglasses": "Acetate/Polycarbonate", "Socks": "75% Cotton, 20% Polyester, 5% Elastane",
    "Scarves": "100% Wool", "Watches": "Stainless Steel Case",
}

def sizes_for(dept, cat, sub):
    if cat == "Footwear":
        return SIZES_KIDS_FT if dept == "Kids" else SIZES_FOOTWEAR
    if dept == "Kids":
        return SIZES_KIDS
    if sub in ("Caps", "Beanies", "Socks", "Belts", "Sunglasses", "Scarves", "Watches", "Bags & Backpacks"):
        return SIZES_ONE
    return SIZES_DEFAULT

def colors_for(name):
    idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(PALETTE)
    return PALETTE[idx]

def images_for(slug):
    return [
        f"https://picsum.photos/seed/{slug}/600/760",
        f"https://picsum.photos/seed/{slug}-b/600/760",
        f"https://picsum.photos/seed/{slug}-c/600/760",
    ]

def to_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

# (dept, cat, sub, name, price, sale_price|None, stock, fit, season, collection, description)
EXTRAS = [
    # ── Men Tops ──────────────────────────────────────────────────────────────
    ("Men","Tops","T-Shirts","Void Oversized Tee",45,None,25,"oversized","all-season","Street Archive","Dropped shoulders, heavyweight cotton, raw hem."),
    ("Men","Tops","T-Shirts","Carbon Core Tee",38,30,30,"regular","all-season","Night City","Classic regular fit in 220gsm ringspun cotton."),
    ("Men","Tops","Polos","Flux Tech Polo",65,None,20,"slim","spring-fall","Heritage Denim","Performance piqué with subtle contrast tipping."),
    ("Men","Tops","Polos","Archive Stripe Polo",55,44,18,"regular","spring-fall","Street Archive","Striped collar polo in breathable cotton."),
    ("Men","Tops","Shirts","Ghost Oxford Shirt",72,None,15,"relaxed","all-season","Night City","Stonewashed oxford cotton for a lived-in feel."),
    ("Men","Tops","Shirts","Edge Utility Shirt",85,None,12,"oversized","spring-fall","Street Archive","Four-pocket utility shirt in ripstop fabric."),
    ("Men","Tops","Tank Tops","Prism Muscle Tank",32,None,35,"slim","summer","Night City","Lightweight muscle cut in breathable cotton blend."),
    ("Men","Tops","Tank Tops","Raw Racer Tank",28,22,40,"slim","summer","Street Archive","Minimal racer cut with dropped armhole."),
    ("Men","Tops","Long Sleeves","Trace Thermal LS",48,None,20,"slim","winter","Heritage Denim","Slim thermal knit for layering or standalone wear."),
    ("Men","Tops","Long Sleeves","Echo Waffle LS",52,42,18,"regular","winter","Night City","Waffle-knit long sleeve in cozy cotton blend."),
    # ── Men Hoodies ───────────────────────────────────────────────────────────
    ("Men","Hoodies & Sweatshirts","Pullover","Arc Heavy Hoodie",95,None,15,"oversized","winter","Street Archive","400gsm heavyweight French terry pullover."),
    ("Men","Hoodies & Sweatshirts","Pullover","Flux Washed Hoodie",85,70,18,"regular","winter","Night City","Garment-washed hoodie for a broken-in texture."),
    ("Men","Hoodies & Sweatshirts","Zip Hoodie","Core Full-Zip",88,None,14,"regular","winter","Heritage Denim","Full-zip in heavyweight brushed fleece."),
    ("Men","Hoodies & Sweatshirts","Zip Hoodie","Mast Zip Hoodie",95,80,12,"slim","winter","Street Archive","Slim zip hoodie with contrast pull."),
    ("Men","Hoodies & Sweatshirts","Crewneck","Void Crewneck",75,None,20,"oversized","winter","Night City","Boxy crewneck in 350gsm French terry."),
    ("Men","Hoodies & Sweatshirts","Crewneck","Edge Fleece Crew",80,65,16,"regular","winter","Street Archive","Classic crewneck in mid-weight fleece."),
    ("Men","Hoodies & Sweatshirts","Oversized","Ghost Drop Sweat",85,None,14,"oversized","winter","Night City","Drop-shoulder oversized sweatshirt."),
    ("Men","Hoodies & Sweatshirts","Oversized","Lux Plush Fleece",90,72,12,"oversized","winter","Heritage Denim","Premium brushed fleece in an oversized silhouette."),
    # ── Men Knitwear ──────────────────────────────────────────────────────────
    ("Men","Knitwear","Sweaters","Carbon Knit Sweater",88,None,14,"regular","winter","Night City","Medium-gauge knit in a wool-acrylic blend."),
    ("Men","Knitwear","Sweaters","Heritage Cable Sweater",95,78,12,"relaxed","winter","Heritage Denim","Classic cable-knit in a natural wool blend."),
    ("Men","Knitwear","Cardigans","Void Open Cardigan",92,None,10,"relaxed","fall","Street Archive","Open-front long cardigan in textured knit."),
    ("Men","Knitwear","Cardigans","Arc Button Cardigan",85,68,12,"regular","fall","Night City","Button-front chunky cardigan."),
    ("Men","Knitwear","Turtlenecks","Flux Ribbed Turtleneck",72,None,15,"slim","winter","Street Archive","Fine-gauge ribbed turtleneck in merino blend."),
    ("Men","Knitwear","Turtlenecks","Core Mock Neck",65,52,18,"regular","winter","Night City","Mock-neck pullover in soft cotton-modal blend."),
    # ── Men Outerwear ─────────────────────────────────────────────────────────
    ("Men","Outerwear","Bomber","Flux Alpha Bomber",145,None,10,"regular","spring-fall","Night City","MA-1 inspired bomber in nylon ripstop."),
    ("Men","Outerwear","Bomber","Arc Satin Bomber",165,130,8,"oversized","spring-fall","Street Archive","Satin finish oversized bomber."),
    ("Men","Outerwear","Denim Jacket","Carbon Raw Denim Jacket",120,None,12,"regular","spring-fall","Heritage Denim","Raw indigo denim trucker jacket."),
    ("Men","Outerwear","Denim Jacket","Ghost Washed Denim Jacket",110,88,10,"relaxed","spring-fall","Heritage Denim","Heavily washed denim in a relaxed fit."),
    ("Men","Outerwear","Puffer","Void Puffer Jacket",175,None,8,"regular","winter","Night City","Recycled polyester fill puffer."),
    ("Men","Outerwear","Puffer","Arc Lightweight Puffer",155,128,10,"slim","winter","Street Archive","Packable lightweight down puffer."),
    ("Men","Outerwear","Leather Jacket","Edge Moto Jacket",245,None,6,"slim","fall","Night City","Genuine lamb leather moto jacket."),
    ("Men","Outerwear","Leather Jacket","Lux Racer Jacket",265,220,5,"slim","fall","Street Archive","Vegan leather racer jacket."),
    ("Men","Outerwear","Windbreaker","Flux Shell Jacket",125,None,12,"regular","spring-fall","Night City","Lightweight shell windbreaker with packable hood."),
    ("Men","Outerwear","Windbreaker","Prism Tech Windbreaker",135,108,10,"oversized","spring-fall","Street Archive","Technical nylon windbreaker."),
    ("Men","Outerwear","Trench","Carbon Trench Coat",195,None,8,"regular","spring-fall","Night City","Classic double-breasted trench in cotton gabardine."),
    ("Men","Outerwear","Trench","Arc Modern Trench",215,172,6,"relaxed","spring-fall","Heritage Denim","Oversized modern trench in a relaxed fit."),
    # ── Men Bottoms ───────────────────────────────────────────────────────────
    ("Men","Bottoms","Jeans","Carbon Raw Jeans",95,None,20,"slim","all-season","Heritage Denim","Raw selvedge denim in slim fit."),
    ("Men","Bottoms","Jeans","Void Distressed Jeans",88,72,15,"regular","all-season","Street Archive","Lightly distressed straight-leg jeans."),
    ("Men","Bottoms","Cargo Pants","Arc Tech Cargo",110,None,12,"regular","all-season","Night City","Multi-pocket cargo in ripstop nylon."),
    ("Men","Bottoms","Cargo Pants","Edge Wide Cargo",98,80,14,"relaxed","all-season","Street Archive","Wide-leg cargo with utility pockets."),
    ("Men","Bottoms","Joggers","Flux Fleece Jogger",75,None,20,"regular","winter","Night City","Heavyweight fleece jogger with cuffed hem."),
    ("Men","Bottoms","Joggers","Core Tech Jogger",82,66,18,"slim","all-season","Street Archive","Slim technical jogger."),
    ("Men","Bottoms","Chinos","Ghost Slim Chino",88,None,15,"slim","spring-fall","Heritage Denim","Classic slim chino in stretch cotton."),
    ("Men","Bottoms","Chinos","Arc Relaxed Chino",92,74,12,"relaxed","spring-fall","Night City","Relaxed-fit chino in cotton-linen blend."),
    ("Men","Bottoms","Shorts","Void Tech Shorts",58,None,25,"regular","summer","Street Archive","Quick-dry performance shorts."),
    ("Men","Bottoms","Shorts","Carbon Cargo Shorts",65,52,20,"regular","summer","Night City","Cargo shorts in ripstop fabric."),
    # ── Men Activewear ────────────────────────────────────────────────────────
    ("Men","Activewear","Track Pants","Surge Track Pant",78,None,20,"regular","all-season","Street Archive","Performance track pant with side stripe."),
    ("Men","Activewear","Track Pants","Arc Athletic Pant",85,68,15,"slim","all-season","Night City","Slim athletic pant in stretch fabric."),
    ("Men","Activewear","Training Tees","Flux Dry-Fit Tee",42,None,30,"regular","all-season","Street Archive","Moisture-wicking training tee."),
    ("Men","Activewear","Training Tees","Core Compression Tee",48,38,25,"slim","all-season","Night City","Compression-fit training shirt."),
    # ── Men Footwear ──────────────────────────────────────────────────────────
    ("Men","Footwear","Sneakers","Void Low Trainer",125,None,15,"","all-season","Night City","Minimalist low-top leather trainer."),
    ("Men","Footwear","Sneakers","Arc Runner Pro",145,118,12,"","all-season","Street Archive","Chunky sole runner in mesh and leather."),
    ("Men","Footwear","Boots","Carbon Chelsea Boot",165,None,10,"","fall","Heritage Denim","Classic Chelsea boot in full-grain leather."),
    ("Men","Footwear","Boots","Edge Combat Boot",185,150,8,"","winter","Night City","Lace-up combat boot with lug sole."),
    ("Men","Footwear","Loafers","Ghost Penny Loafer",155,None,10,"","spring-fall","Heritage Denim","Classic penny loafer in calfskin."),
    ("Men","Footwear","Loafers","Lux Suede Loafer",165,132,8,"","spring-fall","Street Archive","Suede penny loafer with leather sole."),
    ("Men","Footwear","Slides","Core Molded Slide",55,None,25,"","summer","Night City","Contoured footbed slide in EVA foam."),
    ("Men","Footwear","Slides","Arc Leather Slide",85,68,18,"","summer","Street Archive","Full-grain leather slide sandal."),
    # ── Men Accessories ───────────────────────────────────────────────────────
    ("Men","Accessories","Caps","Void 6-Panel Cap",45,None,30,"","all-season","Street Archive","Unstructured 6-panel in heavy-washed cotton."),
    ("Men","Accessories","Caps","Arc Snapback Cap",55,44,25,"","all-season","Night City","Flat-brim snapback with woven patch."),
    ("Men","Accessories","Beanies","Carbon Ribbed Beanie",35,None,35,"","winter","Night City","Tight-rib merino wool beanie."),
    ("Men","Accessories","Beanies","Flux Pom Beanie",38,30,30,"","winter","Street Archive","Oversized pom-pom beanie in soft knit."),
    ("Men","Accessories","Bags & Backpacks","Ghost Utility Tote",75,None,20,"","all-season","Street Archive","Heavy canvas utility tote with laptop sleeve."),
    ("Men","Accessories","Bags & Backpacks","Arc Daypack",125,98,15,"","all-season","Night City","Minimalist daypack in waxed canvas."),
    ("Men","Accessories","Belts","Carbon Tactical Belt",48,None,25,"","all-season","Street Archive","Nylon tactical belt with quick-release buckle."),
    ("Men","Accessories","Belts","Lux Leather Belt",65,52,20,"","all-season","Night City","Full-grain leather belt with brushed hardware."),
    ("Men","Accessories","Sunglasses","Void Wraparound",85,None,20,"","summer","Night City","Sporty wraparound with UV400 protection."),
    ("Men","Accessories","Sunglasses","Edge Square Frame",95,76,15,"","all-season","Street Archive","Oversized square frame in acetate."),
    ("Men","Accessories","Socks","Arc 3-Pack Crew Socks",25,None,40,"","all-season","Night City","Three-pack cushioned crew socks in cotton blend."),
    ("Men","Accessories","Socks","Carbon No-Show Socks",22,18,45,"","all-season","Street Archive","Six-pack no-show socks with silicone grip."),
    # ── Women Tops ────────────────────────────────────────────────────────────
    ("Women","Tops","T-Shirts","Drift Oversized Tee",42,None,25,"oversized","all-season","Street Archive","Relaxed oversized tee in premium cotton."),
    ("Women","Tops","T-Shirts","Lux Baby Tee",35,28,30,"slim","all-season","Night City","Cropped baby tee in ribbed cotton."),
    ("Women","Tops","Crop Tops","Carbon Tie-Front Crop",38,None,25,"regular","summer","Street Archive","Tie-front crop top in breathable cotton."),
    ("Women","Tops","Crop Tops","Void Mesh Crop",45,36,20,"slim","summer","Night City","Semi-sheer mesh crop with bralette lining."),
    ("Women","Tops","Shirts","Ghost Linen Shirt",72,None,15,"relaxed","spring-fall","Heritage Denim","Oversized linen shirt for effortless layering."),
    ("Women","Tops","Shirts","Arc Western Shirt",85,68,12,"regular","spring-fall","Street Archive","Classic western shirt with pearl snaps."),
    ("Women","Tops","Tank Tops","Core Ribbed Tank",28,None,35,"slim","summer","Night City","Fine-rib fitted tank in stretch cotton."),
    ("Women","Tops","Tank Tops","Flux Satin Tank",45,36,25,"slim","summer","Street Archive","Lightweight satin cami top."),
    ("Women","Tops","Long Sleeves","Prism Ribbed LS",48,None,20,"slim","winter","Night City","Ribbed long sleeve in stretch-cotton blend."),
    ("Women","Tops","Long Sleeves","Edge Boat Neck LS",55,44,18,"regular","winter","Street Archive","Boat neck long sleeve in soft modal blend."),
    # ── Women Hoodies ─────────────────────────────────────────────────────────
    ("Women","Hoodies & Sweatshirts","Pullover","Carbon Cozy Hoodie",88,None,15,"oversized","winter","Night City","Ultra-soft 400gsm French terry hoodie."),
    ("Women","Hoodies & Sweatshirts","Pullover","Void Cropped Hoodie",75,60,18,"regular","winter","Street Archive","Cropped pullover hoodie in fleece."),
    ("Women","Hoodies & Sweatshirts","Zip Hoodie","Arc Cropped Zip",82,None,14,"regular","winter","Night City","Cropped zip hoodie in heavyweight fleece."),
    ("Women","Hoodies & Sweatshirts","Zip Hoodie","Lux Half-Zip",88,70,12,"slim","winter","Heritage Denim","Quarter-zip in soft brushed jersey."),
    ("Women","Hoodies & Sweatshirts","Crewneck","Flux Boxy Crewneck",78,None,16,"oversized","winter","Street Archive","Boxy-fit crewneck in mid-weight fleece."),
    ("Women","Hoodies & Sweatshirts","Crewneck","Edge Graphic Crew",85,68,14,"regular","winter","Night City","Graphic print crewneck in soft cotton blend."),
    ("Women","Hoodies & Sweatshirts","Oversized","Prism Drop Sweat",88,None,12,"oversized","winter","Night City","Drop-shoulder oversized sweatshirt."),
    ("Women","Hoodies & Sweatshirts","Oversized","Ghost Plush Fleece",92,74,10,"oversized","winter","Street Archive","Plush oversized fleece pullover."),
    # ── Women Knitwear ────────────────────────────────────────────────────────
    ("Women","Knitwear","Sweaters","Drift Mohair Sweater",95,None,12,"relaxed","winter","Night City","Lightweight mohair-blend in relaxed silhouette."),
    ("Women","Knitwear","Sweaters","Arc Open-Knit Sweater",88,70,14,"relaxed","winter","Street Archive","Airy open-knit sweater for layering."),
    ("Women","Knitwear","Cardigans","Void Long Cardigan",92,None,10,"relaxed","fall","Heritage Denim","Floor-length duster cardigan in chunky knit."),
    ("Women","Knitwear","Cardigans","Carbon Crop Cardigan",75,60,14,"slim","fall","Night City","Cropped button cardigan in ribbed cotton."),
    ("Women","Knitwear","Turtlenecks","Edge Cowl Neck",72,None,15,"regular","winter","Street Archive","Cowl-neck pullover in soft merino blend."),
    ("Women","Knitwear","Turtlenecks","Lux Slim Turtleneck",65,52,18,"slim","winter","Night City","Fine-gauge slim turtleneck in cashmere-blend."),
    # ── Women Outerwear ───────────────────────────────────────────────────────
    ("Women","Outerwear","Bomber","Prism Floral Bomber",145,None,10,"regular","spring-fall","Night City","Embroidered floral bomber in satin."),
    ("Women","Outerwear","Bomber","Arc Oversized Bomber",155,124,8,"oversized","spring-fall","Street Archive","Oversized bomber in nylon ripstop."),
    ("Women","Outerwear","Puffer","Carbon Short Puffer",165,None,10,"regular","winter","Night City","Cropped recycled fill puffer jacket."),
    ("Women","Outerwear","Puffer","Void Vest Puffer",120,96,12,"regular","winter","Street Archive","Puffer vest with side-rib panels."),
    ("Women","Outerwear","Leather Jacket","Ghost Moto Jacket",225,None,8,"slim","fall","Night City","Lamb leather slim moto jacket."),
    ("Women","Outerwear","Leather Jacket","Lux Cropped Leather",245,196,6,"slim","fall","Street Archive","Cropped vegan leather jacket."),
    ("Women","Outerwear","Windbreaker","Flux Shell Wind",115,None,12,"regular","spring-fall","Street Archive","Lightweight shell with packable hood."),
    ("Women","Outerwear","Windbreaker","Arc Colour-Block Wind",128,102,10,"oversized","spring-fall","Night City","Colour-blocked windbreaker."),
    ("Women","Outerwear","Trench","Void Classic Trench",195,None,8,"regular","spring-fall","Heritage Denim","Double-breasted cotton gabardine trench."),
    ("Women","Outerwear","Trench","Edge Oversized Trench",215,172,6,"relaxed","spring-fall","Night City","Oversized belted trench."),
    ("Women","Outerwear","Wool Coat","Carbon Cocoon Coat",265,None,6,"relaxed","winter","Heritage Denim","Cocoon-shape wool-blend overcoat."),
    ("Women","Outerwear","Wool Coat","Arc Longline Coat",285,228,5,"regular","winter","Night City","Longline double-face wool coat."),
    ("Women","Outerwear","Blazer","Prism Oversized Blazer",155,None,10,"oversized","all-season","Street Archive","Relaxed oversized blazer in crepe."),
    ("Women","Outerwear","Blazer","Ghost Tailored Blazer",175,140,8,"regular","all-season","Night City","Single-breasted tailored blazer in stretch fabric."),
    # ── Women Bottoms ─────────────────────────────────────────────────────────
    ("Women","Bottoms","Jeans","Arc Wide-Leg Jeans",92,None,18,"relaxed","all-season","Heritage Denim","90s-inspired wide-leg in mid-wash denim."),
    ("Women","Bottoms","Jeans","Void Barrel Jeans",98,78,15,"relaxed","all-season","Street Archive","Barrel-fit jeans in a medium-blue wash."),
    ("Women","Bottoms","Cargo Pants","Carbon Parachute Pant",105,None,12,"regular","all-season","Street Archive","Y2K-inspired parachute cargo pants."),
    ("Women","Bottoms","Cargo Pants","Flux Wide Cargo",98,78,14,"relaxed","all-season","Night City","Wide-leg cargo in ripstop cotton."),
    ("Women","Bottoms","Joggers","Lux Velour Jogger",72,None,20,"regular","winter","Night City","Velour track-pant with contrast trim."),
    ("Women","Bottoms","Joggers","Edge Ribbed Jogger",65,52,22,"slim","all-season","Street Archive","Slim ribbed jogger in cotton blend."),
    ("Women","Bottoms","Shorts","Drift Denim Shorts",55,None,25,"regular","summer","Heritage Denim","Distressed denim mini-shorts."),
    ("Women","Bottoms","Shorts","Arc Bike Shorts",45,36,30,"slim","summer","Night City","Compression bike shorts with side pocket."),
    ("Women","Bottoms","Skirts","Prism Mini Skirt",65,None,20,"regular","spring-fall","Street Archive","A-line mini in a pleated fabric."),
    ("Women","Bottoms","Skirts","Carbon Denim Skirt",72,58,18,"regular","all-season","Heritage Denim","Straight-cut denim midi skirt."),
    # ── Women Dresses ─────────────────────────────────────────────────────────
    ("Women","Dresses","Mini","Void Slip Mini",88,None,15,"slim","spring-fall","Night City","Bias-cut satin slip dress."),
    ("Women","Dresses","Mini","Arc Ruched Mini",75,60,18,"slim","summer","Street Archive","Jersey ruched mini dress."),
    ("Women","Dresses","Midi","Ghost Shirt Dress",98,None,12,"relaxed","spring-fall","Heritage Denim","Oversized cotton shirt dress."),
    ("Women","Dresses","Midi","Lux Knit Midi",105,84,10,"regular","fall","Night City","Ribbed knit midi dress."),
    ("Women","Dresses","Maxi","Prism Linen Maxi",115,None,10,"relaxed","summer","Heritage Denim","Relaxed linen maxi dress."),
    ("Women","Dresses","Maxi","Carbon Velvet Maxi",145,116,8,"regular","winter","Night City","Velvet maxi dress with open back."),
    # ── Women Activewear ──────────────────────────────────────────────────────
    ("Women","Activewear","Leggings","Flux High-Waist Legging",65,None,25,"slim","all-season","Night City","Buttery-soft 7/8 high-waist leggings."),
    ("Women","Activewear","Leggings","Arc Mesh-Panel Legging",72,58,20,"slim","all-season","Street Archive","Leggings with side mesh panels."),
    ("Women","Activewear","Sports Bras","Void Low-Impact Bra",42,None,30,"slim","all-season","Night City","Lightweight low-impact sports bra."),
    ("Women","Activewear","Sports Bras","Carbon Racerback Bra",48,38,25,"slim","all-season","Street Archive","Medium-support racerback bra."),
    ("Women","Activewear","Track Pants","Surge Track Pant",72,None,20,"regular","all-season","Night City","Classic track pant with side stripe."),
    ("Women","Activewear","Track Pants","Lux Velour Track",78,62,18,"regular","winter","Street Archive","Velour track pants with contrast piping."),
    ("Women","Activewear","Training Tees","Arc Dry-Fit Tank",38,None,30,"regular","all-season","Night City","Moisture-wicking training tank."),
    ("Women","Activewear","Training Tees","Void Mesh Training Tee",42,34,25,"regular","all-season","Street Archive","Mesh-inset training tee."),
    # ── Women Loungewear ──────────────────────────────────────────────────────
    ("Women","Loungewear","Loungewear Sets","Drift Waffle Set",95,None,12,"regular","all-season","Night City","Matching waffle-knit lounge set."),
    ("Women","Loungewear","Loungewear Sets","Carbon Satin Set",115,92,10,"regular","all-season","Street Archive","Satin finish lounge set with piping."),
    # ── Women Footwear ────────────────────────────────────────────────────────
    ("Women","Footwear","Sneakers","Void Chunky Trainer",125,None,14,"","all-season","Street Archive","Platform chunky trainer."),
    ("Women","Footwear","Sneakers","Arc Court Sneaker",110,88,16,"","all-season","Night City","Classic low-top court sneaker."),
    ("Women","Footwear","Boots","Ghost Ankle Boot",165,None,10,"","fall","Night City","Heeled ankle boot in suede."),
    ("Women","Footwear","Boots","Lux Knee-High Boot",195,156,8,"","winter","Street Archive","Pull-on knee-high boot in faux leather."),
    ("Women","Footwear","Sandals","Prism Strappy Sandal",85,None,18,"","summer","Night City","Heeled strappy leather sandal."),
    ("Women","Footwear","Sandals","Carbon Flatform Sandal",95,76,15,"","summer","Street Archive","Flatform sandal with adjustable straps."),
    ("Women","Footwear","Slides","Arc Leather Slide",75,None,20,"","summer","Night City","Leather flat slide with padded footbed."),
    ("Women","Footwear","Slides","Lux Wedge Slide",88,70,15,"","summer","Street Archive","Wedge-heel padded slide."),
    ("Women","Footwear","Loafers","Void Platform Loafer",145,None,10,"","spring-fall","Night City","Platform loafer in patent leather."),
    ("Women","Footwear","Loafers","Edge Horsebit Loafer",155,124,8,"","spring-fall","Heritage Denim","Horsebit detail loafer in calfskin."),
    # ── Women Accessories ─────────────────────────────────────────────────────
    ("Women","Accessories","Caps","Arc 5-Panel Cap",42,None,25,"","all-season","Street Archive","Unstructured 5-panel in cotton twill."),
    ("Women","Accessories","Caps","Void Dad Cap",38,30,30,"","all-season","Night City","Washed cotton dad cap with embroidery."),
    ("Women","Accessories","Beanies","Ghost Pom Beanie",35,None,30,"","winter","Night City","Oversized pom beanie in soft acrylic."),
    ("Women","Accessories","Beanies","Lux Ribbed Beanie",42,34,25,"","winter","Street Archive","Fine-rib merino beanie."),
    ("Women","Accessories","Bags & Backpacks","Drift Mini Bag",75,None,18,"","all-season","Night City","Mini structured top-handle bag."),
    ("Women","Accessories","Bags & Backpacks","Carbon Tote",105,84,14,"","all-season","Street Archive","Oversized canvas tote."),
    ("Women","Accessories","Belts","Prism Chain Belt",55,None,20,"","all-season","Night City","Gold-tone chain belt."),
    ("Women","Accessories","Belts","Arc Slim Leather Belt",65,52,18,"","all-season","Street Archive","Slim leather belt with gold hardware."),
    ("Women","Accessories","Sunglasses","Ghost Cat-Eye Shades",88,None,18,"","summer","Night City","Oversized cat-eye in acetate."),
    ("Women","Accessories","Sunglasses","Void Round Frame",95,76,15,"","all-season","Street Archive","Round tortoiseshell acetate frames."),
    ("Women","Accessories","Socks","Drift Ankle Socks 3pk",22,None,40,"","all-season","Night City","Three-pack ankle socks in cotton blend."),
    ("Women","Accessories","Socks","Arc Knee-High Socks",28,22,35,"","all-season","Street Archive","Striped knee-high socks."),
    ("Women","Accessories","Scarves","Prism Wool Scarf",65,None,15,"","winter","Night City","Oversized checked wool scarf."),
    ("Women","Accessories","Scarves","Carbon Silk Scarf",85,68,12,"","all-season","Street Archive","Printed silk square scarf."),
    ("Women","Accessories","Watches","Edge Minimalist Watch",185,None,8,"","all-season","Night City","Minimalist 36mm with leather strap."),
    ("Women","Accessories","Watches","Lux Mesh Watch",215,172,6,"","all-season","Street Archive","38mm with stainless mesh bracelet."),
    # ── Kids Tops ─────────────────────────────────────────────────────────────
    ("Kids","Tops","T-Shirts","Arc Dino Tee",22,None,30,"regular","all-season","Night City","Cotton tee with dinosaur print."),
    ("Kids","Tops","T-Shirts","Void Stripe Tee",18,14,35,"regular","all-season","Street Archive","Classic stripe jersey tee."),
    ("Kids","Tops","Long Sleeves","Carbon Print LS",25,None,25,"regular","winter","Night City","Printed long sleeve in soft cotton."),
    ("Kids","Tops","Long Sleeves","Arc Ribbed LS",22,18,28,"slim","winter","Street Archive","Ribbed long sleeve."),
    # ── Kids Hoodies ──────────────────────────────────────────────────────────
    ("Kids","Hoodies & Sweatshirts","Pullover","Ghost Fleece Hoodie",45,None,20,"regular","winter","Night City","Zip-through fleece hoodie."),
    ("Kids","Hoodies & Sweatshirts","Pullover","Arc Graphic Hoodie",38,30,25,"regular","winter","Street Archive","Graphic print pullover hoodie."),
    ("Kids","Hoodies & Sweatshirts","Zip Hoodie","Carbon Mini Zip",42,None,20,"regular","winter","Night City","Full-zip hooded sweatshirt."),
    ("Kids","Hoodies & Sweatshirts","Zip Hoodie","Void Fleece Zip",38,30,22,"regular","winter","Street Archive","Lightweight fleece zip hoodie."),
    # ── Kids Outerwear ────────────────────────────────────────────────────────
    ("Kids","Outerwear","Puffer","Flux Kids Puffer",75,None,15,"regular","winter","Night City","Lightweight puffer jacket."),
    ("Kids","Outerwear","Puffer","Arc Neon Puffer",68,54,18,"regular","winter","Street Archive","Colour-block puffer jacket."),
    ("Kids","Outerwear","Windbreaker","Edge Wind Jacket",58,None,20,"regular","spring-fall","Night City","Packable kids windbreaker."),
    ("Kids","Outerwear","Windbreaker","Void Shell Jacket",52,42,22,"regular","spring-fall","Street Archive","Lightweight shell windbreaker."),
    # ── Kids Bottoms ──────────────────────────────────────────────────────────
    ("Kids","Bottoms","Jeans","Carbon Slim Jeans",38,None,25,"slim","all-season","Heritage Denim","Slim-fit kids jeans."),
    ("Kids","Bottoms","Jeans","Arc Stretch Jeans",35,28,28,"regular","all-season","Night City","Stretch denim for active kids."),
    ("Kids","Bottoms","Joggers","Ghost Jogger Pant",32,None,30,"regular","all-season","Night City","Comfortable kids jogger."),
    ("Kids","Bottoms","Joggers","Void Tech Jogger",35,28,25,"slim","all-season","Street Archive","Technical jogger for active wear."),
    ("Kids","Bottoms","Shorts","Arc Printed Shorts",28,None,30,"regular","summer","Street Archive","Fun printed kids shorts."),
    ("Kids","Bottoms","Shorts","Carbon Cargo Shorts",32,25,25,"regular","summer","Night City","Mini cargo shorts with pockets."),
    # ── Kids Footwear ─────────────────────────────────────────────────────────
    ("Kids","Footwear","Sneakers","Lux Junior Trainer",65,None,20,"","all-season","Street Archive","Comfortable kids trainer."),
    ("Kids","Footwear","Sneakers","Arc Velcro Sneaker",55,44,25,"","all-season","Night City","Easy velcro closure sneaker."),
    ("Kids","Footwear","Boots","Prism Kids Boot",72,None,15,"","winter","Night City","Warm-lined kids boot."),
    ("Kids","Footwear","Boots","Void Ankle Boot",65,52,18,"","winter","Street Archive","Classic kids ankle boot."),
    # ── Kids Accessories ──────────────────────────────────────────────────────
    ("Kids","Accessories","Caps","Carbon Kids Cap",28,None,30,"","all-season","Night City","Adjustable kids baseball cap."),
    ("Kids","Accessories","Caps","Arc Kids Snapback",32,25,25,"","all-season","Street Archive","Kids flat-brim snapback."),
    ("Kids","Accessories","Beanies","Void Kids Beanie",22,None,35,"","winter","Night City","Soft knit kids beanie."),
    ("Kids","Accessories","Beanies","Ghost Pom Kids Beanie",25,20,30,"","winter","Street Archive","Kids pom pom beanie."),
    ("Kids","Accessories","Socks","Arc Kids Socks 3pk",15,None,50,"","all-season","Night City","Three-pack kids crew socks."),
    ("Kids","Accessories","Socks","Carbon Striped Socks",18,14,45,"","all-season","Street Archive","Fun striped kids socks 3-pack."),
]

CARE = "Machine wash cold, tumble dry low, do not bleach."


def run():
    with Session(engine) as s:
        existing_names = {p.name.lower() for p in s.exec(select(Product)).all()}
        existing_slugs = {p.slug for p in s.exec(select(Product)).all()}
        added = 0

        for row in EXTRAS:
            dept, cat, sub, name, price, sale, stock, fit, season, collection, desc = row
            if name.lower() in existing_names:
                continue

            # unique slug
            base = to_slug(name)
            slug, n = base, 1
            while slug in existing_slugs:
                slug = f"{base}-{n}"
                n += 1

            fabric = FABRICS.get(sub, "Polyester blend")
            colors = colors_for(name)
            imgs   = images_for(slug)

            p = Product(
                slug=slug, name=name, brand="NOVA WEAR",
                department=dept, category=cat, subcategory=sub,
                price=float(price),
                sale_price=float(sale) if sale is not None else None,
                stock=stock, fit=fit, season=season,
                collection=collection, fabric=fabric,
                care_instructions=CARE,
                description=desc,
                sizes=sizes_for(dept, cat, sub),
                colors=colors,
                images=imgs,
                image=imgs[0],
                color=colors[0]["hex"],
                is_new=(sale is None),
            )
            s.add(p)
            existing_names.add(name.lower())
            existing_slugs.add(slug)
            added += 1

        s.commit()
        print(f"Added {added} products.")


if __name__ == "__main__":
    run()
