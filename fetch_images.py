import os
import itertools
from dotenv import load_dotenv
import httpx
from sqlmodel import Session, select
from models import engine, Product

load_dotenv()

API_KEY = os.getenv("PIXABAY_API_KEY")
if not API_KEY:
    raise RuntimeError("PIXABAY_API_KEY not set in .env")

QUERIES = {
    "Hoodies":  "hoodie streetwear",
    "T-Shirts": "t-shirt fashion",
    "Jackets":  "jacket fashion",
    "Pants":    "pants jeans fashion",
    "Sneakers": "sneakers shoes",
}

def fetch_portraits(query: str) -> list[str]:
    resp = httpx.get(
        "https://pixabay.com/api/",
        params={
            "key": API_KEY,
            "q": query,
            "image_type": "photo",
            "orientation": "vertical",
            "per_page": 15,
            "safesearch": "true",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return [h["largeImageURL"] for h in resp.json()["hits"]]

with Session(engine) as session:
    for category, query in QUERIES.items():
        urls = fetch_portraits(query)
        products = session.exec(select(Product).where(Product.category == category)).all()
        if not urls:
            print(f"{category}: no photos found, skipping")
            continue
        url_cycle = itertools.cycle(urls)
        for product in products:
            product.image = next(url_cycle)
            session.add(product)
        session.commit()
        print(f"{category}: {len(urls)} photos fetched, {len(products)} products updated")
