import random
from sqlmodel import SQLModel, Session
from models import engine, Product

CATS = {
    "Hoodies": ["Oversized Hoodie", "Zip Hoodie", "Cropped Hoodie"],
    "T-Shirts": ["Boxy Tee", "Graphic Tee", "Longline Tee"],
    "Jackets": ["Bomber Jacket", "Denim Jacket", "Puffer Jacket"],
    "Pants": ["Cargo Pants", "Wide Jeans", "Joggers"],
    "Sneakers": ["Chunky Sneaker", "Low Runner", "High Top"],
}
ADJ = ["Midnight", "Urban", "Classic", "Vintage", "Neon", "Essential", "Premium", "Stealth"]
COLORS = ["#111111", "#f2f2f2", "#556b2f", "#1f2a44", "#d8c3a5", "#b3261e"]

SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)
random.seed(7)

with Session(engine) as s:
    n = 0
    for cat, items in CATS.items():
        for i in range(8):
            n += 1
            item = random.choice(items)
            adj = random.choice(ADJ)
            s.add(Product(
                name=f"{adj} {item}",
                category=cat,
                price=round(random.uniform(19, 149), 2),
                stock=random.randint(5, 80),
                description=f"A modern {item.lower()} with a relaxed fit and premium fabric.",
                image=f"https://picsum.photos/seed/shop{n}/600/760",
                color=random.choice(COLORS),
            ))
    s.commit()
print("Seeded", n, "products")